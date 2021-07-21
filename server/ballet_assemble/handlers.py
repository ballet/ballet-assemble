from functools import partial
from urllib.parse import urlencode, urljoin

import requests
import tornado
from notebook.base.handlers import APIHandler, IPythonHandler
from notebook.notebookapp import NotebookWebApplication
from notebook.utils import url_path_join
from tenacity import (
    RetryError, retry, retry_if_exception_message, retry_if_exception_type, stop_after_delay,
    wait_fixed)
from tornado.httpclient import AsyncHTTPClient

from .app import AssembleApp

try:
    from importlib import metadata
except ImportError:
    import importlib_metadata as metadata


GITHUB_OAUTH_URL = 'https://github.com/login/oauth/authorize'


class StatusHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        self.write({'status': 'OK'})


class VersionHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        app = AssembleApp.instance()

        try:
            assemble_version = metadata.version('ballet_assemble')
        except Exception:
            assemble_version = None
        try:
            ballet_version = metadata.version('ballet')
        except Exception:
            ballet_version = None
        try:
            project_version = app.project.version
        except Exception:
            project_version = None

        self.write({
            'assemble': assemble_version,
            'ballet': ballet_version,
            'project': project_version,
        })


class ConfigHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        app = AssembleApp.instance()
        result = {}
        for attr in app.class_own_traits():
            result[attr] = getattr(app, attr)
        self.write(result)


class ConfigItemHandler(APIHandler):

    @tornado.web.authenticated
    def get(self, attr):
        app = AssembleApp.instance()
        try:
            param = getattr(app, attr)
            self.write({attr: param})
        except AttributeError:
            self.send_error(404)


class SubmitHandler(APIHandler):

    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        app = AssembleApp.instance()
        result = app.create_pull_request_for_code_content(input_data)
        self.write(result)


class AuthorizeHandler(IPythonHandler):

    @tornado.web.authenticated
    def get(self):
        app = AssembleApp.instance()

        # wake server async
        http_client = AsyncHTTPClient()
        url = urljoin(app.oauth_gateway_url, '/status')
        http_client.fetch(url)

        # do oauth flow
        base = GITHUB_OAUTH_URL
        params = {
            'client_id': app.client_id,
            'state': app.state,
            'scope': ','.join(app.scopes),
        }

        url = base + '?' + urlencode(params)
        self.redirect(url, permanent=False)


class TokenHandler(IPythonHandler):

    @retry(
        wait=wait_fixed(3),
        retry=(
            retry_if_exception_type(RuntimeError) &
            retry_if_exception_message(match=r'[Nn]o authorization code found.*')
        ),
        stop=stop_after_delay(AssembleApp.instance().access_token_timeout)
    )
    async def get_token(self, url, data):
        response = requests.post(url, json=data)
        d = response.json()
        if response.ok:
            # TODO also store other token info
            return d['access_token']
        else:
            reason = d.get('message', '').lower()
            raise RuntimeError(reason)

    @tornado.web.authenticated
    async def post(self):
        """request token if we have just authenticated"""
        app = AssembleApp.instance()
        base = app.oauth_gateway_url
        state = app.state
        url = urljoin(base, '/api/v1/access_token')
        data = {'state': state}

        try:
            token = await self.get_token(url, data)
            app.set_github_token(token)
            self.finish()
        except RetryError:
            self.send_error(status_code=400, reason='timeout')
        except RuntimeError as e:
            self.send_error(status_code=400, reason=str(e))

        app.reset_state()


class AuthenticatedHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        app = AssembleApp.instance()
        self.write({
            'result': app.is_authenticated(),
            'message': None,
        })


def setup_handlers(app: NotebookWebApplication, url_path: str):
    host_pattern = '.*$'
    base_url = app.settings['base_url']
    route_pattern = partial(url_path_join, base_url, url_path)

    app.add_handlers(host_pattern, [
        (route_pattern('status'), StatusHandler),
        (route_pattern('version'), VersionHandler),
        (route_pattern('config'), ConfigHandler),
        (route_pattern(r'config/(.*)'), ConfigItemHandler),
        (route_pattern('submit'), SubmitHandler),
        (route_pattern('auth', 'authorize'), AuthorizeHandler),
        (route_pattern('auth', 'token'), TokenHandler),
        (route_pattern('auth', 'authenticated'), AuthenticatedHandler),
    ])
