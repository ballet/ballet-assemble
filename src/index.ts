import {
  Dialog,
  showDialog,
  showErrorMessage,
  ToolbarButton,
  ICommandPalette
} from '@jupyterlab/apputils';

import { IDisposable, DisposableDelegate } from '@lumino/disposable';

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

import { DocumentRegistry } from '@jupyterlab/docregistry';

import { NotebookPanel, INotebookModel } from '@jupyterlab/notebook';

import { ISettingRegistry } from '@jupyterlab/settingregistry';

import { ConfirmWidget, FeatureSubmittedOkayWidget } from './widgets';

import {
  ISubmissionResponse,
  checkStatus,
  getEndpointUrl,
  submit,
  request,
  isAuthenticated
} from './serverextension';

import $ from 'jquery';

const EXTENSION_NAME = 'ballet-assemble';
const PLUGIN_ID = `${EXTENSION_NAME}:plugin`;

/**
 * A notebook widget extension that adds a submit button to the toolbar.
 */
export class AssembleSubmitButtonExtension
  implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  settingRegistry: ISettingRegistry;

  constructor(settingRegistry: ISettingRegistry) {
    this.settingRegistry = settingRegistry;
  }

  async loadSetting(settingName: string): Promise<string> {
    return (await this.settingRegistry.get(PLUGIN_ID, settingName))
      .composite as string;
  }

  /**
   * Create a new extension object.
   */
  createNew(
    panel: NotebookPanel,
    context: DocumentRegistry.IContext<INotebookModel>
  ): IDisposable {
    let button = new ToolbarButton({
      label: 'Submit',
      iconClass: 'fa fa-share assemble-submitButtonIcon',
      onClick: async () => {
        // check if authenticated
        if (!(await isAuthenticated())) {
          void showErrorMessage(
            'Not authenticated',
            "You're not authenticated with GitHub - click the GitHub icon in the toolbar to connect!"
          );
          return;
        }

        // load current cell
        let notebook = panel.content;
        let activeCell = notebook.activeCell;
        let contents = activeCell.model.value.text;

        // confirm to proceed
        const confirmDialog = await showDialog({
          title: 'Submit feature?',
          body: new ConfirmWidget(contents)
        });
        if (!confirmDialog.button.accept) {
          return;
        }

        // post contents to server
        console.log(contents);
        const result: ISubmissionResponse = await submit(contents);

        // try to add a message to cell outputs
        if (result.result) {
          void showDialog({
            title: 'Feature submitted successfully',
            body: new FeatureSubmittedOkayWidget(result.url),
            buttons: [Dialog.okButton()]
          });
        } else {
          const message =
            result.message !== undefined && result.message !== null
              ? `: ${result.message}.`
              : '.';
          void showErrorMessage(
            'Error submitting feature',
            `Oops - there was a problem submitting your feature${message}`
          );
          console.error(result);
        }
      },
      tooltip: 'Submit current cell to Ballet project'
    });
    panel.toolbar.addItem('assembleSubmitButton', button);

    let githubAuthButton = new ToolbarButton({
      iconClass: 'fa fa-github assemble-githubAuthButtonIcon',
      onClick: async () => {
        if (!(await isAuthenticated())) {
          window.open(
            getEndpointUrl('auth/authorize'),
            '_blank',
            'width=350,height=600'
          );
          // async
          void request<void>('auth/token', {
            method: 'POST'
          });
        } else {
          void showDialog({
            title: 'Already authenticated',
            body: 'You have successfully authenticated with GitHub.',
            buttons: [Dialog.okButton()]
          });
        }
      },
      tooltip: 'Authenticate with GitHub'
    });
    panel.toolbar.addItem('githubAuthButton', githubAuthButton);

    // ugh
    // TODO - remove callback when authenticated, assuming that we will never become un-authenticated
    setInterval(async () => {
      $('.assemble-githubAuthButtonIcon').toggleClass(
        'assemble-githubAuthButtonIcon-authenticated',
        await isAuthenticated()
      );
    }, 5 * 1000);

    return new DisposableDelegate(() => {
      button.dispose();
      githubAuthButton.dispose();
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
  app.docRegistry.addWidgetExtension(
    'Notebook',
    new AssembleSubmitButtonExtension(settingRegistry)
  );

  // create submit command
  const submitCommand: string = 'assemble:submit';
  app.commands.addCommand(submitCommand, {
    label: 'Submit Feature',
    execute: () => {
      console.log('Submit feature executed (TODO)');
    }
  });
  palette.addItem({ command: submitCommand, category: 'Assemble' });

  // check status of /assemble endpoints
  try {
    await checkStatus();
    console.log('Connected to /assemble endpoints');
  } catch {
    console.error("Can't connect to /assemble endpoints");
  }
}

/**
 * Initialization data for the ballet-assemble extension.
 */
const extension: JupyterFrontEndPlugin<void> = {
  id: PLUGIN_ID,
  autoStart: true,
  requires: [ICommandPalette, ISettingRegistry],
  activate: activate
};

export default extension;
