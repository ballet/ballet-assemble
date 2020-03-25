// import {
//   JupyterFrontEnd, JupyterFrontEndPlugin
// } from '@jupyterlab/application';
//
// import { requestAPI } from './ballet-submit-labextension';
//
// /**
//  * Initialization data for the ballet-submit-labextension extension.
//  */
// const extension: JupyterFrontEndPlugin<void> = {
//   id: 'ballet-submit-labextension',
//   autoStart: true,
//   activate: (app: JupyterFrontEnd) => {
//     console.log('JupyterLab extension ballet-submit-labextension is activated!');
//
//     requestAPI<any>('get_example')
//       .then(data => {
//         console.log(data);
//       })
//       .catch(reason => {
//         console.error(
//           `The ballet-submit-labextension server extension appears to be missing.\n${reason}`
//         );
//       });
//   }
// };
//
// export default extension;
