import http

import pytest
from traitlets.config import Config

from notebook.tests.launchnotebook import NotebookTestBase

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

    def test_auth_authorize(self):
        response = self.request('GET', '/ballet/auth/authorize', allow_redirects=False)

        assert response.status_code == http.HTTPStatus.FOUND

    def test_auth_authenticated(self):
        app = BalletApp.instance()
        app._is_authenticated = True

        response = self.request('GET', '/ballet/auth/authenticated')
        d = response.json()

        assert 'result' in d and d['result']
