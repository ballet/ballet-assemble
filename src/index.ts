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
import {
  ConfirmWidget, FeatureSubmittedOkayWidget
} from './widgets';


const SUBMIT_URL = 'https://ballet-submit-server.herokuapp.com/submit'

interface ISubmissionResponse {
  result: boolean;
  url?: string;
  message?: string;
}

async function postModule(cellContents: string): Promise<ISubmissionResponse> {
  try {
    const response = await axios.post(SUBMIT_URL, {
      codeContent: cellContents,
    })
    return response.data
  } catch (error) {
    console.log(error);
    return { result: false }
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
      const confirmDialog = await showDialog({
        title: 'Submit feature?',
        body: new ConfirmWidget(contents)
      });
      if (! confirmDialog.button.accept) {
        return;
      }

      // post contents to ballet-submit-server
      console.log(contents);
      const result = await postModule(contents);

      // try to add a message to cell outputs
      if (result.result) {
        showDialog({
          title: 'Feature submitted successfully',
          body: new FeatureSubmittedOkayWidget(result.url),
          buttons: [
            Dialog.okButton()
          ]
        });
      } else {
        const message = result.message !== undefined && result.message !== null
          ? `: ${result.message}.`
          : '.';
        showErrorMessage(
          'Error submitting feature',
          `Oops - there was a problem submitting your feature${message}`
        );
      }
    };

    let button = new ToolbarButton({
      label: 'Submit',
      iconClassName: 'fa fa-share ballet-submitButtonIcon',
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
 * Initialization data for the ballet-submit-labextension extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'ballet-submit-labextension',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension ballet-submit-labextension is activated!');
    app.docRegistry.addWidgetExtension('Notebook', new BalletSubmitButtonExtension());
  }
};

export default extension;
