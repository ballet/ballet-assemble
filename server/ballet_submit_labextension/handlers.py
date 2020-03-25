from functools import partial

import tornado
from notebook.notebookapp import NotebookWebApplication
from notebook.base.handlers import APIHandler
from notebook.utils import url_path_join

from .submit import create_pull_request_for_code_content


class StatusHandler(APIHandler):

    @tornado.web.authenticated
    def get(self):
        self.set_header('Content-Type', 'text/plain')
        self.finish('OK')


class SubmitHandler(APIHandler):

    @tornado.web.authenticated
    def post(self):
        input_data = self.get_json_body()
        result = create_pull_request_for_code_content(input_data)
        self.write(result)


def setup_handlers(app: NotebookWebApplication, url_path: str):
    host_pattern = '.*$'
    base_url = app.settings['base_url']
    route_pattern = partial(url_path_join, base_url, url_path)

    app.add_handlers(host_pattern, [
        (route_pattern('status'), StatusHandler),
        (route_pattern('submit'), SubmitHandler)
    ])
