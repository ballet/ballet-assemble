import http
from dataclasses import asdict
from unittest.mock import Mock, patch

import pytest
import requests
from traitlets.config import Config

from notebook.tests.launchnotebook import NotebookTestBase

import ballet_submit_labextension.app
from ballet_submit_labextension import load_jupyter_server_extension
from ballet_submit_labextension.app import BalletApp


@pytest.fixture
def config():
    return Config(**{
        'debug': True,
        'token': 'foobar',
    })


def test_app_config(config):
    app = BalletApp.instance(config=config)
    assert app.debug in {True, False}


class BaseTestCase(NotebookTestBase):

    @classmethod
    def setup_class(cls):
        super().setup_class()
        load_jupyter_server_extension(cls.notebook)
        cls.app = BalletApp.instance()


class BalletHandlersTest(BaseTestCase):

    def test_status(self):
        response = self.request('GET', '/ballet/status')
        d = response.json()
        assert 'OK' == d['status']

    def test_config(self):
        traits = BalletApp.class_own_traits()

        response = self.request('GET', '/ballet/config')
        d = response.json()

        assert d.keys() == traits.keys()

    def test_config_item(self):
        debug = self.app.debug

        response = self.request('GET', '/ballet/config/debug')
        d = response.json()

        assert d == {'debug': debug}

    def test_auth_authorize(self):
        response = self.request('GET', '/ballet/auth/authorize', allow_redirects=False)

        assert response.status_code == http.HTTPStatus.FOUND

    @patch('ballet_submit_labextension.handlers.requests')
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
        response = self.request('POST', '/ballet/auth/token')

        assert response.ok
        assert self.app.github_token == token

    def test_auth_authenticated(self):
        self.app._is_authenticated = True

        response = self.request('GET', '/ballet/auth/authenticated')
        d = response.json()

        assert 'result' in d and d['result']

    @patch('ballet_submit_labextension.app.BalletApp.create_pull_request_for_code_content')
    def test_submit(self, mock_create):
        url = 'url'
        result = True
        mock_result = ballet_submit_labextension.app.Response(result=result, url=url)
        mock_create.return_value = asdict(mock_result)

        response = self.request('POST', '/ballet/submit', json={
            'codeContent': 'code',
        })
        d = response.json()

        assert d['result'] == result and d['url'] == url
