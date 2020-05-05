import pytest
from traitlets.config import Config

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
