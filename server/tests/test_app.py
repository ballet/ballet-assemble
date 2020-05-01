import pytest
from notebook.notebookapp import NotebookApp

from ballet_submit_labextension.submit import BalletApp

@pytest.fixture
def notebookapp():
    instance = NotebookApp.instance()
    return instance


def test_app(notebookapp):
    app = BalletApp(config=notebookapp.config)
    assert app.debug in {True, False}
