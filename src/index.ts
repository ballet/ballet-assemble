import {
  Dialog, showDialog, showErrorMessage, ToolbarButton, ICommandPalette
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
import { ISettingRegistry } from '@jupyterlab/coreutils';


interface ISubmissionResponse {
  result: boolean;
  url?: string;
  message?: string;
}

async function postModule(cellContents: string, submitUrl: string): Promise<ISubmissionResponse> {
  try {
    const response = await axios.post(submitUrl, {
      codeContent: cellContents,
    })
    return response.data
  } catch (error) {
    console.log(error);
    return { result: false }
  }
}

async function loadSubmitUrl(settingRegistry: ISettingRegistry): Promise<string> {
  return (
     await settingRegistry.get(
       'ballet-submit-labextension:plugin',
       'submitUrl'
     )
   ).composite as string;
}

/**
 * A notebook widget extension that adds a submit button to the toolbar.
 */
export
class BalletSubmitButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  settingRegistry: ISettingRegistry;

  constructor(settingRegistry: ISettingRegistry) {
    this.settingRegistry = settingRegistry;
  }

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
      const submitUrl = await loadSubmitUrl(this.settingRegistry);
      const result = await postModule(contents, submitUrl);

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

async function activate(
  app: JupyterFrontEnd,
  palette: ICommandPalette,
  settingRegistry: ISettingRegistry
): Promise<void> {
  console.log('JupyterLab extension ballet-submit-labextension is activated!');

  // log submit url
  const submitUrl: string = await loadSubmitUrl(settingRegistry);
  console.log(`Will be submitting to ${submitUrl}`);

  // add button to toolbar
  app.docRegistry.addWidgetExtension('Notebook', new BalletSubmitButtonExtension(settingRegistry));

  // create command
  const command: string = 'ballet:submit';
  app.commands.addCommand(command, {
    label: 'Submit Feature',
    execute: () => {
      console.log('Submit feature executed (TODO)');
    }
  });

  // add command to palette
  palette.addItem({command, category: 'Ballet'});
}

/**
 * Initialization data for the ballet-submit-labextension extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: 'ballet-submit-labextension:plugin',
  autoStart: true,
  requires: [ICommandPalette, ISettingRegistry],
  activate: activate
};

export default extension;
