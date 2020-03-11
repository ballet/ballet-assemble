import { ReactWidget } from '@jupyterlab/apputils';
import React from 'react';

export class ConfirmWidget extends ReactWidget {
  code: string;

  constructor(code: string) {
    super();
    this.code = code;
    this.addClass('jp-ReactWidget');
  }

  render() {
    return (
      <div className="ballet-featureSubmittedConfirm">
        <p> The following feature would be submitted to the upstream Ballet project: </p>
        <div>
          <pre><code>
          {this.code}
          </code></pre>
        </div>
      </div>
    );
  }
}

export class FeatureSubmittedOkayWidget extends ReactWidget {
  url: string;

  constructor(url: string) {
    super();
    this.url = url;
    this.addClass('jp-ReactWidget');
  }

  render() {
    return (
      <div className="ballet-featureSubmittedOkay">
        <p> Your feature was submitted! </p>
        <br/>
        <p> The associated pull request is visible at <a  href={this.url} target="_blank">{this.url}</a>. </p>
        <br/>
        <p> Please do not submit this same feature more than once. </p>
      </div>
    );
  }
}
