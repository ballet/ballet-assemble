import threading
from functools import partial
from urllib.parse import urlencode, urljoin

import requests
import tornado
from notebook.base.handlers import APIHandler, IPythonHandler
from notebook.notebookapp import NotebookWebApplication
from notebook.utils import url_path_join
from tenacity import RetryError, retry, retry_if_result, stop_after_delay, wait_fixed

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


class ConfigItemHandler(APIHandler):

    @tornado.web.authenticated
    def get(self, attr):
        app = BalletApp.instance()
        try:
            param = getattr(app, attr)
            self.write({attr: param})
        except AttributeError:
            self.send_error(404)


class SubmitHandler(APIHandler):

    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        app = BalletApp.instance()
        result = app.create_pull_request_for_code_content(input_data)
        self.write(result)


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
        base = GITHUB_OAUTH_URL
        params = {
            'client_id': app.client_id,
            'state': app.state,
            'scope': ','.join(app.scopes),
        }

        url = base + '?' + urlencode(params)
        self.redirect(url, permanent=False)


class TokenHandler(IPythonHandler):

    @tornado.web.authenticated
    def post(self):
        """request token if we have just authenticated"""
        app = BalletApp.instance()
        base = app.oauth_gateway_url
        timeout = app.access_token_timeout
        state = app.state
        url = urljoin(base, '/api/v1/access_token')
        data = {
            'state': state,
        }

        retry_obj = object()

        @retry(
            wait=wait_fixed(3),
            retry=retry_if_result(lambda x: x is retry_obj),
            stop=stop_after_delay(timeout),
        )
        def get_token():
            response = requests.post(url, json=data)
            d = response.json()
            if response.ok:
                # TODO also store other token info
                return d['access_token']
            else:
                reason = d.get('message', '').lower()
                if 'no authorization code found' in reason:
                    return
                else:
                    raise RuntimeError(reason)

        try:
            token = get_token()
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
        app = BalletApp.instance()
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
        (route_pattern('config'), ConfigHandler),
        (route_pattern(r'config/(.*)'), ConfigItemHandler),
        (route_pattern('submit'), SubmitHandler),
        (route_pattern('auth', 'authorize'), AuthorizeHandler),
        (route_pattern('auth', 'token'), TokenHandler),
        (route_pattern('auth', 'authenticated'), AuthenticatedHandler),
    ])
