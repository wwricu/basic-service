import { createContext, useContext } from 'react';
import { message } from 'antd';

export const RefreshContext = createContext<{ key: boolean; triggerRefresh: () => void } | null>(null);

export const useRefresh = () => {
  // Get context in element wrapped by RefreshProvider who give context
  const context = useContext(RefreshContext);
  if (!context) {
    throw new Error('useRefresh must be used within RefreshProvider');
  }
  return context;
};

export class HttpError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

const handleResponse = async <T>(response: Response): Promise<T> => {
  const data = (await response.json().catch(() => null)) as { detail?: string } | null;

  if (response.ok) {
    return data as T;
  }

  const errorMsg = data?.detail || response.statusText;

  message.error(errorMsg);

  if (response.status === 401) {
    if (window.location.pathname.startsWith('/login')) {
      throw new HttpError(errorMsg, response.status);
    }
    window.location.href = '/login';
  }

  return new Promise<T>(() => {});
};

export const http = {
  async get<T>(url: string, headers?: Record<string, string>): Promise<T> {
    const response = await fetch(`/api${url}`, {
      method: 'GET',
      headers: {
        Accept: 'application/json',
        ...headers,
      },
    });
    return handleResponse<T>(response);
  },

  async post<T>(url: string, data?: unknown, headers?: Record<string, string>): Promise<T> {
    const isFormData = data instanceof FormData;
    const response = await fetch(`/api${url}`, {
      method: 'POST',
      headers: isFormData
        ? headers
        : {
            'Content-Type': 'application/json',
            Accept: 'application/json',
            ...headers,
          },
      body: isFormData ? data : JSON.stringify(data),
    });
    return handleResponse<T>(response);
  },
};
