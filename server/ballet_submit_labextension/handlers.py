from functools import partial

import tornado
from notebook.base.handlers import APIHandler
from notebook.notebookapp import NotebookWebApplication
from notebook.utils import url_path_join

from .submit import BalletApp


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


class TokenHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        app = BalletApp.instance()
        result = {'access_token': app.token}
        self.write(result)

    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        if 'access_token' not in input_data:
            self.send_error(status_code=400)

        token = input_data['access_token']

        app = BalletApp.instance()
        app.set_token(token)


def setup_handlers(app: NotebookWebApplication, url_path: str):
    host_pattern = '.*$'
    base_url = app.settings['base_url']
    route_pattern = partial(url_path_join, base_url, url_path)

    app.add_handlers(host_pattern, [
        (route_pattern('status'), StatusHandler),
        (route_pattern('config'), ConfigHandler),
        (route_pattern('submit'), SubmitHandler),
        (route_pattern('auth', 'token'), TokenHandler),
    ])
