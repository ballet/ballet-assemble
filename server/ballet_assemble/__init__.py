# -*- coding: utf-8 -*-

"""Server extension for ballet-assemble"""

__author__ = 'Micah Smith'
__email__ = 'micahs@mit.edu'
__version__ = '0.8.4'

from jupyterlab.labapp import LabApp

from .handlers import setup_handlers

EXTENSION_URL_PATH = 'assemble'


def _jupyter_server_extension_paths():
    return [{
        'module': 'ballet_assemble'
    }]


def load_jupyter_server_extension(app: LabApp):
    """Register the API handler

    Args:
        app (notebook.notebookapp.NotebookApp)
            Notebook application instance
    """

    # initialize app instance
    from .app import AssembleApp
    AssembleApp.clear_instance()
    AssembleApp.instance(config=app.config)

    setup_handlers(app.web_app, EXTENSION_URL_PATH)
    app.log.info('Registered ballet-assemble extension at URL path /%s',
                 EXTENSION_URL_PATH)
