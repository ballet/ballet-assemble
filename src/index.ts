import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';


/**
 * Initialization data for the ballet-submit extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'ballet-submit',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension ballet-submit is activated!');
  }
};

export default extension;
