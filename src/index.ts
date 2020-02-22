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
  NotebookActions, NotebookPanel, INotebookModel
} from '@jupyterlab/notebook';


/**
 * A notebook widget extension that adds a submit button to the toolbar.
 */
export
class BalletSubmitButtonExtension implements DocumentRegistry.IWidgetExtension<NotebookPanel, INotebookModel> {
  /**
   * Create a new extension object.
   */
  createNew(panel: NotebookPanel, context: DocumentRegistry.IContext<INotebookModel>): IDisposable {
    let callback = () => {
      NotebookActions.run(panel.content, context.session);
    };
    let button = new ToolbarButton({
      className: 'balletSubmitButton',
      iconClassName: 'fa fa-share',
      onClick: callback,
      tooltip: 'Submit Ballet Module'
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
