import threading
from functools import partial
from urllib.parse import urlencode, urljoin

import requests
import tornado
from notebook.base.handlers import APIHandler, IPythonHandler
from notebook.notebookapp import NotebookWebApplication
from notebook.utils import url_path_join

from .app import BalletApp


GITHUB_OAUTH_URL = 'https://github.com/login/oauth/authorize'


class StatusHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        self.write({'status': 'OK'})


class ConfigHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        app = BalletApp.instance()
        result = {}
        for attr in app.class_own_traits():
            result[attr] = getattr(app, attr)
        self.write(result)


class SubmitHandler(APIHandler):

    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        app = BalletApp.instance()
        result = app.create_pull_request_for_code_content(input_data)
        self.write(result)


# class TokenHandler(APIHandler):
#
#     @tornado.web.authenticated
#     def get(self):
#         app = BalletApp.instance()
#         result = {'access_token': app.token}
#         self.write(result)
#
#     @tornado.web.authenticated
#     def post(self):
#         input_data = self.get_json_body()
#         if 'access_token' not in input_data:
#             self.send_error(status_code=400)
#
#         token = input_data['access_token']
#
#         app = BalletApp.instance()
#         app.set_token(token)


class AuthorizeHandler(IPythonHandler):

    @tornado.web.authenticated
    def get(self):
        app = BalletApp.instance()

        # try to wake server - don't care about response
        threading.Thread(
            target=requests.get,
            args=(urljoin(app.oauth_gateway_url, '/status'),),
        ).start()

        # do oauth flow
        # TODO get port, prefix from settings?
        redirect_url = 'http://localhost:8888/ballet/auth/authorize/success'
        base = GITHUB_OAUTH_URL
        params = {
            'client_id': app.client_id,
            'state': app.state,
            'scope': ','.join(app.scopes),
            'redirect_url': redirect_url,
        }

        url = base + '?' + urlencode(params)
        self.redirect(url, permanent=False)

        # clean up
        app.reset_state()


class AuthorizeSuccessHandler(IPythonHandler):

    @tornado.web.authenticated
    def get(self):
        """callback indicating that we have authenticated"""
        app = BalletApp.instance()
        base = app.oauth_gateway_url
        url = urljoin(base, '/api/v1/access_token')
        data = {
            'state': app.state,
        }
        response = requests.post(url, data=data)
        d = response.json()

        if not response.ok:
            reason = d.get('message')
            self.send_error(status_code=400)

        # TODO also store other token info
        token = d['access_token']
        app.set_token(token)

        # just in case
        app.reset_state()


def setup_handlers(app: NotebookWebApplication, url_path: str):
    host_pattern = '.*$'
    base_url = app.settings['base_url']
    route_pattern = partial(url_path_join, base_url, url_path)

    app.add_handlers(host_pattern, [
        (route_pattern('status'), StatusHandler),
        (route_pattern('config'), ConfigHandler),
        (route_pattern('submit'), SubmitHandler),
        # (route_pattern('auth', 'token'), TokenHandler),
        (route_pattern('auth', 'authorize'), AuthorizeHandler),
        (route_pattern('auth', 'authorize', 'success'), AuthorizeSuccessHandler),
    ])
