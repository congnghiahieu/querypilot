import { LOCAL_STORAGE_AUTH_DATA_KEY } from './constants';

export interface AuthData {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: {
    id: string;
    username: string;
    email: string;
    full_name: string;
    created_at: string;
    role?: string;
  };
}

export const getAuthData = (): AuthData | null => {
  const data = localStorage.getItem(LOCAL_STORAGE_AUTH_DATA_KEY);
  if (!data) return null;

  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
};

export const setAuthData = (data: AuthData): void => {
  localStorage.setItem(LOCAL_STORAGE_AUTH_DATA_KEY, JSON.stringify(data));
};

export const clearAuthData = (): void => {
  localStorage.removeItem(LOCAL_STORAGE_AUTH_DATA_KEY);
};

export const getAuthToken = (): string | null => {
  const authData = getAuthData();
  return authData ? authData.access_token : null;
};

export const isAuthenticated = (): boolean => {
  return getAuthToken() !== null;
};
