import pytest
from traitlets.config import Config

from notebook.tests.launchnotebook import NotebookTestBase

from ballet_submit_labextension import load_jupyter_server_extension
from ballet_submit_labextension.submit import BalletApp


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
        pass
        # response = self.request('GET', '/ballet/status')
        # d = response.json()
        # assert 'OK' == d['status']
