import { ReactWidget } from '@jupyterlab/apputils';
import React from 'react';

const ConfirmComponent = (options: {code: string}) => {
  return (
    <div>
      <p> The following feature would be submitted to the upstream Ballet project: </p>
      <div>
        <pre><code>
        {options.code}
        </code></pre>
      </div>
    </div>
  );
};

export class ConfirmWidget extends ReactWidget {
  code: string

  constructor(code: string) {
    super();
    this.code = code
    this.addClass('jp-ReactWidget');
  }

  render() {
    return <ConfirmComponent code={this.code} />;
  }
}
