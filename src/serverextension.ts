import { URLExt } from '@jupyterlab/coreutils';

import { ServerConnection } from '@jupyterlab/services';

export interface ISubmissionRequest {
  codeContent: string;
}

export interface ISubmissionResponse {
  result: boolean;
  url?: string;
  message?: string;
}

export async function submit(cellContents: string): Promise<ISubmissionResponse> {
  const endPoint = 'submit'
  const init = {
    method: 'POST',
    body: JSON.stringify({
      codeContent: cellContents
    })
  }

  try {
    return await request<ISubmissionResponse>(endPoint, init)
  } catch (error) {
    console.error(error);
    return { result: false }
  }
}

export async function checkStatus(): Promise<void> {
  return request<void>('status');
}

/**
 * Call the API extension
 *
 * @param endPoint API REST end point for the extension
 * @param init Initial values for the request
 * @returns The response body interpreted as JSON
 */
export async function request<T>(
  endPoint: string = '',
  init: RequestInit = {}
): Promise<T> {
  // Make request to Jupyter API
  const settings = ServerConnection.makeSettings();
  const requestUrl = URLExt.join(
    settings.baseUrl,
    'ballet',
    endPoint
  );

  let response: Response;
  try {
    response = await ServerConnection.makeRequest(requestUrl, init, settings);
  } catch (error) {
    throw new ServerConnection.NetworkError(error);
  }

  const data = await response.json();

  if (!response.ok) {
    throw new ServerConnection.ResponseError(response, data.message);
  }

  return data;
}
