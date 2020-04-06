# -*- coding: utf-8 -*-

"""Server for ballet-submit"""

__author__ = 'Micah Smith'
__email__ = 'micahs@mit.edu'
__version__ = '0.5.0'

from jupyterlab.labapp import LabApp

from .handlers import setup_handlers

EXTENSION_URL_PATH = 'ballet'


def _jupyter_server_extension_paths():
    return [{
        'module': 'ballet_submit_labextension'
    }]


def load_jupyter_server_extension(app: LabApp):
    """Register the API handler

    Args:
        app (notebook.notebookapp.NotebookApp)
            Notebook application instance
    """
    setup_handlers(app.web_app, EXTENSION_URL_PATH)
    app.log.info('Registered ballet-submit-labextension extension at URL path /%s',
                 EXTENSION_URL_PATH)
