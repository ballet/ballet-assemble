import {
  Dialog, showDialog, showErrorMessage, ToolbarButton, ICommandPalette
} from '@jupyterlab/apputils';

import {
  IDisposable, DisposableDelegate
} from '@lumino/disposable';

import {
  JupyterFrontEnd, JupyterFrontEndPlugin
} from '@jupyterlab/application';

import {
  DocumentRegistry
} from '@jupyterlab/docregistry';

import {
  NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';

import {
  ISettingRegistry
} from '@jupyterlab/settingregistry';

import {
  ConfirmWidget, FeatureSubmittedOkayWidget
} from './widgets';

import {
  ISubmissionResponse, checkStatus, submit
} from './serverextension';


const EXTENSION_NAME = 'ballet-submit-labextension';
const PLUGIN_ID = `${EXTENSION_NAME}:plugin`;

/**
 * A notebook widget extension that adds a submit button to the toolbar.
 */
export
class BalletSubmitButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  settingRegistry: ISettingRegistry;

  constructor(settingRegistry: ISettingRegistry) {
    this.settingRegistry = settingRegistry;
  }

  async loadSetting(settingName: string): Promise<string> {
    return (await this.settingRegistry.get(PLUGIN_ID, settingName)).composite as string;
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
      const result: ISubmissionResponse = await submit(contents);

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
      iconClass: 'fa fa-share ballet-submitButtonIcon',
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
  console.log(`JupyterLab extension ${EXTENSION_NAME} is activated!`);

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

  // check status of /ballet endpoints
  checkStatus()
    .then(() => console.log('Connected to /ballet endpoints'))
    .catch(() => console.error('Can\'t connect to /ballet endpoints'));
}

/**
 * Initialization data for the ballet-submit-labextension extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICommandPalette, ISettingRegistry],
  activate: activate
};

export default extension;
