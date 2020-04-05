import getpass
import logging
import pathlib
import tempfile
import uuid
from dataclasses import asdict, dataclass
from os import getenv
from textwrap import dedent
from typing import List, Tuple

import ballet.templating
import funcy as fy
import git
from ballet.project import Project
from ballet.util import truthy
from ballet.util.code import blacken_code, is_valid_python
from ballet.util.git import set_config_variables
from cookiecutter.utils import work_in
from github import Github
from stacklog import stacklog as _stacklog
from traitlets import Bool, Unicode, default
from traitlets.config import LoggingConfigurable

TESTING_URL = 'http://some/testing/url'


@dataclass
class Response:
    result: str
    url: str = None
    message: str = None


@dataclass
class Request:
    codeContent: str


def stacklog(level, message):
    """Stacklog decorator that uses instance method's `.logger` at given level"""
    level = logging.getLevelName(level)

    def decorator(func):
        @fy.wraps(func)
        def wrapped(self, *args, **kwargs):
            with _stacklog(fy.partial(self.log.log, level), message):
                return func(self, *args, **kwargs)
        return wrapped
    return decorator


def make_feature_and_branch_name():
    my_id = str(uuid.uuid4())
    branch_name = f'submit-feature-{my_id}'
    underscore_id = my_id.replace('-', '_')
    feature_name = underscore_id
    return feature_name, branch_name


def get_new_feature_path(changes: List[Tuple[str, str]]):
    cwd = pathlib.Path.cwd()
    for (name, kind) in changes:
        if kind == 'file' and '__init__' not in str(name):
            relname = pathlib.Path(name).relative_to(cwd)
            return relname
    return None


@fy.decorator
def handlefailures(call):
    try:
        return call()
    except Exception as e:
        message = str(e)
        return Response(result=False, message=message)


class BalletApp(LoggingConfigurable):

    # -- begin traits --

    debug = Bool(
        config=True,
        help='enable debug mode (no changes made on GitHub)',
    )
    @default('debug')
    def _default_debug(self):
        _default = 'False'
        # fixme: truthy only works on strings as of ballet==0.6.11
        return truthy(getenv('BALLET_DEBUG', default=_default))

    username = Unicode(
        config=True,
        help='github username',
    )
    @default('username')
    def _default_username(self):
        # 1. load from environment variable
        # 2. detect github.user already configured with git (non-standard)
        # 3. use $USER
        username = getenv('BALLET_SUBMIT_USERNAME')
        if username is not None:
            return username

        username = self.project.repo.config_reader().get_value('github', 'user', default=None)
        if username is not None:
            return username

        return getpass.getuser()

    token = Unicode(
        config=True,
        help='github personal access token'
    )
    @default('token')
    def _default_token(self):
        return getenv('GITHUB_TOKEN', '')

    useremail = Unicode(
        config=True,
        help='email address to associate with git commit messages',
    )
    @default('useremail')
    def _default_useremail(self):
        # 1. load from environment variable
        # 2. detect user.email already configured with git
        # 3. construct <username>@users.noreply.github.com
        email = getenv('BALLET_SUBMIT_USEREMAIL')
        if email is not None:
            return email

        email = self.project.repo.config_reader().get_value('user', 'email', default=None)
        if email is not None:
            return email

        return f'{self.username}@users.noreply.github.com'

    reponame = Unicode(
        config=False,
        help='name of project repo',
    )
    @default('reponame')
    def _default_reponame(self):
        return self.project.config.get('project.project_slug', '')

    upstream_repo_spec = Unicode(
        config=False,
        help='spec of upstream repo of the form "username/reponame"'
    )
    @default('upstream_repo_spec')
    def _default_upstream_repo_spec(self):
        github_owner = self.project.config.get('github.github_owner', '')
        return f'{github_owner}/{self.reponame}'

    repo_spec = Unicode(
        config=False,
        help='spec of forked repo of the form "username/reponame"',
    )
    @default('repo_spec')
    def _default_repo_spec(self):
        return f'{self.username}/{self.reponame}'

    repo_url = Unicode(
        config=False,
        help='url of forked repo, including username and password authentication'
    )
    @default('repo_url')
    def _default_repo_url(self):
        return f'https://{self.username}:{self.token}@github.com/{self.repo_spec}'

    # -- end traits --

    @fy.cached_property
    def project(self):
        return Project.from_cwd()

    @fy.cached_property
    def github(self):
        return Github(self.token)

    @fy.post_processing(asdict)
    @handlefailures
    def create_pull_request_for_code_content(self, input_data: dict) -> Response:
        code_content = self.load_request(input_data)
        self.check_code_is_valid(code_content)

        with tempfile.TemporaryDirectory() as dirname:
            dirname = str(pathlib.Path(dirname).resolve())
            repo = self.clone_repo(dirname)
            with work_in(dirname):
                self.configure_repo(repo)
                feature_name, branch_name = self.create_new_branch(repo)
                changed_files, new_feature_path = self.start_new_feature(dirname, feature_name)
                self.write_code_content(new_feature_path, code_content)
                self.commit_changes(repo,  changed_files)
                self.push_to_remote(repo, branch_name)
                return self.create_pull_request(feature_name, branch_name)

    @stacklog('DEBUG', 'Loading request')
    def load_request(self, input_data: dict) -> str:
        try:
            req = Request(**input_data)
        except TypeError as e:
            raise TypeError(f'Bad request - {e!s}') from e
        return req.codeContent

    @stacklog('INFO', 'Checking for valid code')
    def check_code_is_valid(self, code_content: str) -> None:
        if not is_valid_python(code_content):
            raise ValueError('Submitted code is not valid Python code')

    @stacklog('INFO', 'Cloning repo')
    def clone_repo(self, dirname: str) -> git.Repo:
        return git.Repo.clone_from(self.repo_url, to_path=dirname)

    @stacklog('INFO', 'Configuring repo')
    def configure_repo(self, repo: git.Repo) -> None:
        set_config_variables(repo, {
            'user.name': self.username,  # github username
            'user.email': self.useremail,
        })
        repo.remote().set_url(self.repo_url)

    @stacklog('INFO', 'Creating new branch and checking it out')
    def create_new_branch(self, repo: git.Repo) -> Tuple[str, str]:
        feature_name, branch_name = make_feature_and_branch_name()
        repo.create_head(branch_name)
        repo.heads[branch_name].checkout()
        return feature_name, branch_name

    @stacklog('INFO', 'Starting new feature')
    def start_new_feature(self, dirname: str, feature_name: str) -> Tuple[List[str], str]:
        # start new feature
        extra_context = {
            'username': self.username.replace('-', '_'),
            'featurename': feature_name,
        }
        changes = ballet.templating.start_new_feature(
            no_input=True, extra_context=extra_context)
        changed_files = [
            str(pathlib.Path(name).relative_to(dirname))
            for (name, kind) in changes
            if kind == 'file'
        ]
        new_feature_path = get_new_feature_path(changes)
        return changed_files, new_feature_path

    @stacklog('INFO', 'Adding code content')
    def write_code_content(self, new_feature_path: str, code_content: str):
        with open(new_feature_path, 'w') as f:
            blackened_code_content = blacken_code(code_content)
            f.write(blackened_code_content)

    @stacklog('INFO', 'Committing new feature')
    def commit_changes(self, repo, changed_files):
        repo.index.add(changed_files)
        repo.index.commit('Add new feature')

    @stacklog('INFO', 'Pushing to remote')
    def push_to_remote(self, repo, branch_name):
        refspec = f'refs/heads/{branch_name}:refs/heads/{branch_name}'
        if not self.debug:
            repo.remote().push(refspec=refspec)
        else:
            self.log.debug('Didn\'t actually push to remote due to debug')

    @stacklog('INFO', 'Creating pull request')
    def create_pull_request(self, feature_name, branch_name):
        grepo = self.github.get_repo(self.upstream_repo_spec)
        title = 'Propose new feature'
        body = dedent(f'''\
                Propose new feature: {feature_name}
                Submitted by user: {self.username}

                --
                Pull request automatically created by ballet-submit-labextension
            ''')
        base = 'master'
        head = f'{self.username}:{branch_name}'
        maintainer_can_modify = True
        self.log.debug(
            'About to create pull: title=%s, body=%s, base=%s, head=%s',
            title, body, base, head)

        self.log.debug(
            'About to create pull: title=%s, body=%s, base=%s, head=%s',
            title, body, base, head,
        )
        if not self.debug:
            pr = grepo.create_pull(title=title, body=body, base=base, head=head,
                                   maintainer_can_modify=maintainer_can_modify)
            url = pr.html_url
        else:
            self.log.debug('Didn\'t create real pull request due to debug')
            url = TESTING_URL

        return Response(result=True, url=url)
