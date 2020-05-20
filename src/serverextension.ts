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

export interface IAuthenticatedResponse {
  result: boolean;
}

export async function submit(
  cellContents: string
): Promise<ISubmissionResponse> {
  const endPoint = 'submit';
  const init = {
    method: 'POST',
    body: JSON.stringify({
      codeContent: cellContents
    })
  };

  try {
    return request<ISubmissionResponse>(endPoint, init);
  } catch (error) {
    console.error(error);
    return { result: false };
  }
}

export async function checkStatus(): Promise<void> {
  return request<void>('status');
}

export async function isAuthenticated(): Promise<boolean> {
  const response = await request<IAuthenticatedResponse>('auth/authenticated');
  return response.result;
}

export function getEndpointUrl(endPoint: string): string {
  const settings = ServerConnection.makeSettings();
  return URLExt.join(settings.baseUrl, 'ballet', endPoint);
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
  const requestUrl = getEndpointUrl(endPoint);

  let response: Response;
  try {
    const settings = ServerConnection.makeSettings();
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
