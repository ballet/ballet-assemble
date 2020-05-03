from ballet_submit_labextension.submit import BalletApp


def test_app_config():
    app = BalletApp.instance()
    assert app.runtime_dir is not None
    assert app.debug in {True, False}
