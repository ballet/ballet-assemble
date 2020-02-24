import {
  Dialog, showDialog, showErrorMessage, ToolbarButton
} from '@jupyterlab/apputils';

import {
  IDisposable, DisposableDelegate
} from '@phosphor/disposable';

import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import axios from 'axios';


const SUBMIT_URL = 'https://ballet-submit-server.herokuapp.com/submit'

async function postModule(cellContents: string): Promise<string> {
  try {
    const response = await axios.post(SUBMIT_URL, {
      codeContent: cellContents,
    })
    return response.data
  } catch (error) {
    console.log(error);
    return undefined
  }
}

/**
 * A notebook widget extension that adds a submit button to the toolbar.
 */
export
class BalletSubmitButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {

    let callback = async () => {
      // load current cell
      let notebook = panel.content;
      let activeCell = notebook.activeCell;
      let contents = activeCell.model.value.text;

      // confirm to proceed
      const result = await showDialog({
        title: 'Submit feature?',
        body: `
          The following feature would be submitted to the upstream Ballet project:
          \n
          \n
          ${contents}
        `
      });
      if (! result.button.accept) {
        return;
      }

      // post contents to ballet-submit-server
      console.log(contents);
      const url = await postModule(contents);

      // try to add a message to cell outputs
      if (url !== undefined) {
        showDialog({
          title: 'Feature submitted successfully',
          body: `Your feature was submitted! The associated pull request is visible at ${url}. Please do not submit this same feature more than once.`,
          buttons: [
            Dialog.okButton()
          ]
        });
      } else {
        showErrorMessage('Feature submitted successfully', `Oops - there was a problem submitting your feature.`
        );
      }
    };

    let button = new ToolbarButton({
      label: 'Submit',
      iconClassName: 'fa fa-share balletSubmitButtonIcon',
      onClick: callback,
      tooltip: 'Submit current cell to Ballet project'
    });

    panel.toolbar.addItem('balletSubmitButton', button);

    return new DisposableDelegate(() => {
      button.dispose();
    });
  }
}


/**
 * Initialization data for the ballet-submit extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'ballet-submit',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension ballet-submit-labextension is activated!');
    app.docRegistry.addWidgetExtension('Notebook', new BalletSubmitButtonExtension());
  }
};

export default extension;
