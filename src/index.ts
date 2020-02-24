import {
  IDisposable, DisposableDelegate
} from '@phosphor/disposable';

import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  ToolbarButton
} from '@jupyterlab/apputils';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookActions, NotebookPanel, Notebook, INotebookModel
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

function recordSubmitted(notebook: Notebook, index: number, url: string): void {
  notebook.activeCellIndex = index;
  NotebookActions.insertBelow(notebook);
  NotebookActions.changeCellType(notebook, 'raw');
  let cell = notebook.activeCell;

  let text: string;
  if (url === undefined) {
    text = `Oops - there was a problem submitting your feature.`;
  } else {
    text = `Your feature was submitted! The associated pull request is visible at ${url}. Please do not submit this same feature more than once.`;
  }
  cell.model.value.text = text;
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
      let activeCellIndex = notebook.activeCellIndex;
      let contents = activeCell.model.value.text;

      // post contents to ballet-submit-server
      console.log(contents);
      const url = await postModule(contents);

      // try to add a message to cell outputs
      recordSubmitted(notebook, activeCellIndex, url);
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
    console.log('JupyterLab extension ballet-submit is activated!');
    app.docRegistry.addWidgetExtension('Notebook', new BalletSubmitButtonExtension());
  }
};

export default extension;
