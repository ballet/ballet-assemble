import base64
import datetime
import json
import hashlib
import logging
import os
import pathlib
import socket
import tempfile
import uuid
from dataclasses import asdict, dataclass
from os import getenv
from textwrap import dedent
from typing import List, Optional, Tuple
from urllib.parse import urljoin

import ballet.templating
import funcy as fy
import git
import requests
from ballet.exc import ConfigurationError
from ballet.project import Project
from ballet.util import truthy
from ballet.util.code import blacken_code, is_valid_python
from ballet.util.git import set_config_variables
from cookiecutter.utils import work_in
from github import Github
from notebook.notebookapp import NotebookApp
from requests import RequestException
from stacklog import stacklog as _stacklog
from traitlets import Bool, Integer, Unicode, default, validate
from traitlets.config import SingletonConfigurable

TESTING_URL = 'http://some/testing/url'


@dataclass
class Response:
    result: bool
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


def make_random_state():
    return base64.urlsafe_b64encode(os.urandom(16)).decode()


@fy.decorator
def handlefailures(call):
    try:
        return call()
    except Exception as e:
        message = str(e)
        return Response(result=False, message=message)


def iftelenabled(method):
    def wrapped(self, *args, **kwargs):
        if not self.tel:
            return
        else:
            return method(self, *args, **kwargs)
    return wrapped


def sha1(s):
    return hashlib.sha1(s.encode('utf-8')).hexdigest()


class BalletApp(SingletonConfigurable):

    # -- begin traits --

    debug = Bool(
        config=True,
        help='enable debug mode (no changes made on GitHub), will read from $BALLET_DEBUG if '
             'present',
    )

    @default('debug')
    def _default_debug(self):
        _default = 'False'
        # fixme: truthy only works on strings as of ballet==0.6.11
        return truthy(getenv('BALLET_DEBUG', default=_default))

    github_token = Unicode(
        config=True,
        help='github access token, will read from $GITHUB_TOKEN if present'
    )

    @default('github_token')
    def _default_github_token(self):
        return getenv('GITHUB_TOKEN', '')

    ballet_yml_path = Unicode(
        '',
        config=True,
        help='path to ballet.yml file of Ballet project (if Lab is not run from project directory)'
    )

    @validate('ballet_yml_path')
    def _validate_ballet_yml_path(self, proposal):
        if proposal:
            return str(pathlib.Path(proposal['value']).expanduser().resolve())
        else:
            return proposal

    oauth_gateway_url = Unicode(
        'https://github-oauth-gateway.herokuapp.com/',
        config=True,
        help='url to github-oauth-gateway server',
    )

    access_token_timeout = Integer(
        60,
        config=True,
        help='timeout to receive access token from server via polling'
    )

    # -- end traits --

    @fy.cached_property
    def client_id(self):
        base = self.oauth_gateway_url
        url = urljoin(base, '/api/v1/app_id')
        response = requests.get(url)
        response.raise_for_status()
        d = response.json()
        return d['client_id']

    scopes = ['read:user', 'public_repo']
    _state = None

    @property
    def state(self):
        if self._state is None:
            self._state = make_random_state()

        return self._state

    def reset_state(self):
        self._state = None

    def set_github_token(self, token):
        self.github_token = token

    _is_authenticated = False

    def is_authenticated(self):
        if not self._is_authenticated:
            with fy.suppress(Exception):
                _ = self.username
                self._is_authenticated = True

        return self._is_authenticated

    @property
    def github(self):
        return Github(self.github_token)

    @property
    def username(self):
        return self.github.get_user().login

    @property
    def useremail(self):
        # in lieu of requesting `user:email` scope
        return f'{self.username}@users.noreply.github.com'

    @property
    def reponame(self):
        """name of project repo"""
        return self.project.config.get('project.project_slug', '')

    @property
    def upstream_repo_spec(self):
        """refspec of upstream repo of the form 'username/reponame'"""
        github_owner = self.project.config.get('github.github_owner', '')
        return f'{github_owner}/{self.reponame}'

    @property
    def upstream_repo(self):
        return self.github.get_repo(self.upstream_repo_spec)

    @property
    def repo_url(self):
        """url of forked repo, including token-based authentication"""
        return f'https://{self.github_token}@github.com/{self.username}/{self.reponame}'

    @property
    def project(self):
        # 1. configuration option passed explicitly
        # 2. from notebooks dir
        # 3. from cwd
        if self.ballet_yml_path:
            return Project.from_path(self.ballet_yml_path)

        path = NotebookApp.instance().notebook_dir
        with fy.suppress(Exception):
            return Project.from_path(path)

        with fy.suppress(Exception):
            return Project.from_cwd()

        raise ConfigurationError('Could not detect ballet project')

    @fy.post_processing(asdict)
    @handlefailures
    def create_pull_request_for_code_content(self, input_data: dict) -> Response:
        code_content = self.load_request(input_data)
        self.check_code_is_valid(code_content)

        # async
        self.fork_repo()

        with tempfile.TemporaryDirectory() as dirname:
            dirname = str(pathlib.Path(dirname).resolve())
            repo = self.clone_repo(dirname)
            with work_in(dirname):
                self.configure_repo(repo)
                feature_name, branch_name = self.create_new_branch(repo)
                changed_files, new_feature_path = self.start_new_feature(dirname, feature_name)
                self.write_code_content(new_feature_path, code_content)
                self.commit_changes(repo, changed_files)
                push_result = self.push_to_remote(repo, branch_name)  # noqa F841
                # TODO if push failed, likely because fork does not yet exist, then try again
                return self.create_pull_request(feature_name, branch_name)

    @stacklog('DEBUG', 'Loading request')
    def load_request(self, input_data: dict) -> str:
        try:
            req = Request(**input_data)
        except TypeError as e:
            raise TypeError(f'Bad request - {e}') from e
        return req.codeContent

    @stacklog('INFO', 'Checking for valid code')
    def check_code_is_valid(self, code_content: str) -> None:
        if not code_content.strip():
            raise ValueError('No code was submitted -- did you select the correct cell?')

        if not is_valid_python(code_content):
            raise ValueError('Submitted code is not valid Python code')

    @stacklog('INFO', 'Forking upstream repo')
    def fork_repo(self) -> None:
        if not self.debug:
            return self.upstream_repo.create_fork()
        else:
            self.log.debug('Didn\'t actually fork repo due to debug')
            return None

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
    def push_to_remote(
        self, repo, branch_name
    ) -> Optional[List[git.remote.PushInfo]]:
        refspec = f'refs/heads/{branch_name}:refs/heads/{branch_name}'
        if not self.debug:
            return repo.remote().push(refspec=refspec)
        else:
            self.log.debug('Didn\'t actually push to remote due to debug')
            return None

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

    # begin tel stuff

    tel = Bool(
        False,
        config=True,
        help='enable Ballet tel for experiments',
    )

    telserver = Unicode(
        'http://localhost',
        config=True,
        help='url to tel server'
    )

    _televents = []
    _tel_opted_in = 'unknown'
    _telgh_value = None
    _tel_already_added_launch = False

    @fy.cached_property
    def _telhost(self):
        return sha1(socket.gethostname())

    @property
    def _telgh(self):
        if self._telgh_value is None:
            with fy.suppress(Exception):
                self._telgh_value = sha1(self.username)

        return self._telgh_value

    @fy.ignore(RequestException)
    @iftelenabled
    def tel_post(self):
        if not self.tel_opted_in():
            return

        response = requests.post(
            self.telserver + '/events', json=self._televents)
        if response.ok:
            self._televents.clear()

    @fy.ignore(RequestException)
    @iftelenabled
    def tel_opted_in(self):
        if self._tel_opted_in == 'unknown' and self._telgh is not None:
            response = requests.get(
                self.telserver + '/optedin', params={'id': self._telgh})
            if response.ok:
                if 'yes' in response.text:
                    self._tel_opted_in = 'yes'
                elif 'no' in response.text:
                    self._tel_opted_in = 'no'
        return self._tel_opted_in == 'yes'

    @iftelenabled
    def tel_add(self, name, details):
        if name == 'binderlaunched':
            if self._tel_already_added_launch:
                return
            else:
                self._tel_already_added_launch = True

        event = {
            'id': str(uuid.uuid4()),
            'host': self._telhost,
            'gh': self._telgh,
            'name': name,
            'dt': datetime.datetime.utcnow().isoformat(),
            'details': json.dumps(details),
        }
        self._televents.append(event)
        self.log.info(f'added event {event["name"]} with id {event["id"]}')
        self.tel_post()


def print_help():
    BalletApp.class_print_help()


if __name__ == '__main__':
    print_help()
