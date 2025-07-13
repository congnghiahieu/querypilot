import { client } from '@/api/client.gen';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ThemeProvider } from '@/hooks/useTheme';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { getAuthToken } from './lib/auth';
import { LOCAL_STORAGE_AUTH_DATA_KEY, LOCAL_STORAGE_THEME_KEY } from './lib/constants';
import ForgotPassword from './pages/ForgotPassword';
import Index from './pages/Index';
import Login from './pages/Login';
import Register from './pages/Register';
import Welcome from './pages/Welcome';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: (failureCount, error: any) => {
        // Don't retry on 401 errors
        if (error?.response?.status === 401) return false;
        return failureCount < 3;
      },
    },
  },
});

// Configure internal service client
client.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URL,
  withCredentials: true,
});

// Add request interceptor for authentication
client.instance.interceptors.request.use((config) => {
  const token = getAuthToken();
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Add response interceptor for handling 401 errors
client.instance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Clear auth data and redirect to login
      localStorage.removeItem(LOCAL_STORAGE_AUTH_DATA_KEY);
      window.location.href = '/login';
    }
    return Promise.reject(error);
  },
);

const ProtectedRoute = ({ children }: { children: React.ReactNode }) => {
  const authData = localStorage.getItem(LOCAL_STORAGE_AUTH_DATA_KEY);
  const isAuthenticated = authData ? JSON.parse(authData).access_token : false;

  return isAuthenticated ? children : (
      <Navigate
        to='/login'
        replace
      />
    );
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider
      defaultTheme='light'
      storageKey={LOCAL_STORAGE_THEME_KEY}
    >
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter
          future={{
            v7_startTransition: true,
            v7_relativeSplatPath: true,
          }}
        >
          <Routes>
            <Route
              path='/login'
              element={<Login />}
            />
            <Route
              path='/register'
              element={<Register />}
            />
            <Route
              path='/forgot-password'
              element={<ForgotPassword />}
            />
            <Route
              path='/'
              element={
                <ProtectedRoute>
                  <Welcome />
                </ProtectedRoute>
              }
            />
            <Route
              path='/:chatId'
              element={
                <ProtectedRoute>
                  <Index />
                </ProtectedRoute>
              }
            />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </ThemeProvider>
    {import.meta.env.DEV && <ReactQueryDevtools initialIsOpen={false} />}
  </QueryClientProvider>
);

export default App;
