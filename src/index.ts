import {
  Dialog,
  showDialog,
  showErrorMessage,
  ToolbarButton,
  ICommandPalette
} from '@jupyterlab/apputils';

import { LabIcon } from '@jupyterlab/ui-components';

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

const EXTENSION_NAME = 'ballet-assemble';
const PLUGIN_ID = `${EXTENSION_NAME}:plugin`;

const balletIconSvg = `<?xml version="1.0" encoding="utf-8"?><!-- Generator: Adobe Illustrator 24.3.0, SVG Export Plug-In . SVG Version: 6.00 Build 0)  --> <svg version="1.1" id="Layer_1" xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" x="0px" y="0px" viewBox="0 0 72 72" style="enable-background:new 0 0 72 72;" xml:space="preserve"> <style type="text/css"> .st0{fill:#FBDD37;} .st1{fill:#565656;} </style> <g> <g> <rect x="0" class="st0" width="72" height="72"/> </g> <g> <path class="st1" d="M23.8,16.3c0-1.2,0.6-1.8,1.8-1.8h1.7c1.2,0,1.8,0.6,1.8,1.8v11.4c0,0.4,0,0.7,0,1c0,0.3,0,0.5-0.1,0.7 c0,0.3-0.1,0.5-0.1,0.7h0.1c0.5-1,1.2-1.8,2-2.5c0.7-0.6,1.7-1.2,2.9-1.8s2.6-0.8,4.2-0.8c1.8,0,3.5,0.4,5,1.1 c1.5,0.7,2.8,1.7,3.9,3c1.1,1.3,1.9,2.8,2.5,4.6c0.6,1.8,0.9,3.8,0.9,5.9c0,2.3-0.3,4.3-0.9,6.1c-0.6,1.8-1.5,3.4-2.7,4.6 c-1.1,1.3-2.5,2.3-4,3s-3.2,1.1-5,1.1c-1.7,0-3.1-0.3-4.2-0.8c-1.1-0.6-2.1-1.2-2.8-1.8c-0.8-0.8-1.5-1.7-2-2.7h-0.1 c0,0.1,0,0.3,0.1,0.4c0.1,0.4,0.1,0.8,0.1,1.2V52c0,1.1-0.6,1.6-1.8,1.6h-1.4c-1.2,0-1.8-0.6-1.8-1.8V16.3z M29,39.6 c0,1.3,0.2,2.5,0.5,3.7c0.3,1.2,0.8,2.3,1.5,3.2c0.6,0.9,1.5,1.7,2.4,2.2c1,0.6,2.1,0.8,3.5,0.8c1.1,0,2.2-0.2,3.2-0.7 c1-0.4,1.9-1.1,2.6-1.9c0.7-0.8,1.3-1.9,1.7-3.1c0.4-1.2,0.6-2.6,0.6-4.2c0-1.5-0.2-2.9-0.6-4.1c-0.4-1.2-0.9-2.3-1.6-3.1 c-0.7-0.9-1.5-1.5-2.5-2c-1-0.5-2-0.7-3.2-0.7c-1.1,0-2.1,0.2-3,0.6c-1,0.4-1.8,1-2.6,1.8c-0.8,0.8-1.4,1.8-1.8,3.1 C29.3,36.4,29,37.9,29,39.6z"/> </g> </g> </svg>`;
const ONE_SECOND = 1000;
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
      icon: new LabIcon({
        name: 'ballet-icon',
        svgstr: balletIconSvg
      }),
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
    let authIntervalId = setInterval(authCallback, 5 * ONE_SECOND);

    async function authCallback() {
      let authenticated = await isAuthenticated();
      githubAuthButton.toggleClass(
        'assemble-githubAuthButtonIcon-authenticated',
        authenticated
      );
      if (authenticated) {
        // githubAuthButton.update = 'Already authenticated with GitHub';
        clearInterval(authIntervalId);
      }
    }

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
