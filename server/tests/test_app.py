import http
from dataclasses import asdict
from packaging.version import Version
from unittest.mock import Mock, patch

import pytest
import requests
from traitlets.config import Config

from notebook.tests.launchnotebook import NotebookTestBase

import ballet_assemble.app
from ballet_assemble import load_jupyter_server_extension
from ballet_assemble.app import AssembleApp


@pytest.fixture
def config():
    return Config(**{
        'debug': True,
        'token': 'foobar',
    })


def test_app_config(config):
    app = AssembleApp.instance(config=config)
    assert app.debug in {True, False}


class BaseTestCase(NotebookTestBase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        load_jupyter_server_extension(cls.notebook)
        cls.app = AssembleApp.instance()


class AssembleHandlersTest(BaseTestCase):

    def test_status(self):
        response = self.request('GET', '/assemble/status')
        d = response.json()
        assert 'OK' == d['status']

    def test_version(self):
        response = self.request('GET', '/assemble/version')
        d = response.json()

        assemble_version = d['assemble']
        assert assemble_version is None or Version(assemble_version)

        ballet_version = d['ballet']
        assert ballet_version is None or Version(ballet_version)

        project_version = d['project']
        assert project_version is None or isinstance(project_version, str)

    def test_config(self):
        traits = AssembleApp.class_own_traits()

        response = self.request('GET', '/assemble/config')
        d = response.json()

        assert d.keys() == traits.keys()

    def test_config_item(self):
        debug = self.app.debug

        response = self.request('GET', '/assemble/config/debug')
        d = response.json()

        assert d == {'debug': debug}

    def test_auth_authorize(self):
        response = self.request('GET', '/assemble/auth/authorize', allow_redirects=False)

        assert response.status_code == http.HTTPStatus.FOUND

    @patch('ballet_assemble.handlers.requests')
    def test_auth_token(self, mock_requests):
        mock_response = Mock(spec=requests.Response)
        mock_requests.post.return_value = mock_response
        token = 'e72e16c7e42f292c6912e7710c838347ae178b4a'
        mock_response.json.return_value = {
            'access_token': token,
            'scope': 'repo,gist',
            'token_type': 'bearer',
            'message': None
        }
        mock_response.ok = True

        self.app.debug = True
        response = self.request('POST', '/assemble/auth/token')

        assert response.ok
        assert self.app.github_token == token

    def test_auth_authenticated(self):
        self.app._is_authenticated = True

        response = self.request('GET', '/assemble/auth/authenticated')
        d = response.json()

        assert 'result' in d and d['result']

    @patch('ballet_assemble.app.AssembleApp.create_pull_request_for_code_content')
    def test_submit(self, mock_create):
        url = 'url'
        result = True
        mock_result = ballet_assemble.app.Response(result=result, url=url)
        mock_create.return_value = asdict(mock_result)

        response = self.request('POST', '/assemble/submit', json={
            'codeContent': 'code',
        })
        d = response.json()

        assert d['result'] == result and d['url'] == url

    def test_submit_empty_cell(self):
        response = self.request('POST', '/assemble/submit', json={
            'codeContent': '',
        })
        d = response.json()

        assert d['result'] == False
        assert d['message'] is not None
