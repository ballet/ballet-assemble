# -*- coding: utf-8 -*-

"""Server for ballet-submit"""

__author__ = 'Micah Smith'
__email__ = 'micahs@mit.edu'
__version__ = '0.2.0'


from .handlers import setup_handlers


EXTENSION_URL_PATH = 'ballet-submit'


def load_jupyter_server_extension(app):
    """Register the API handler

    Args:
        app (notebook.notebookapp.NotebookApp)
            Notebook application instance
    """
    setup_handlers(app, EXTENSION_URL_PATH)
    app.log.info('Registered ballet_submit_serverextension extension at URL path /%s',
                 EXTENSION_URL_PATH)
