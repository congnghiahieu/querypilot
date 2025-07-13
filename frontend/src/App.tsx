import { client } from '@/api/client.gen';
import { Toaster as Sonner } from '@/components/ui/sonner';
import { Toaster } from '@/components/ui/toaster';
import { TooltipProvider } from '@/components/ui/tooltip';
import { ThemeProvider } from '@/hooks/useTheme';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactQueryDevtools } from '@tanstack/react-query-devtools';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';

import { LOCAL_STORAGE_AUTH_DATA_KEY, LOCAL_STORAGE_THEME_KEY } from './lib/constants';
import ForgotPassword from './pages/ForgotPassword';
import Index from './pages/Index';
import Login from './pages/Login';
import Register from './pages/Register';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
    },
  },
});

// configure internal service client
client.setConfig({
  baseURL: import.meta.env.VITE_API_BASE_URl,
  withCredentials: true,
});

client.instance.interceptors.request.use((config) => {
  const authData = localStorage.getItem(LOCAL_STORAGE_AUTH_DATA_KEY);
  if (authData) {
    const { access_token } = JSON.parse(authData);
    config.headers.Authorization = `Bearer ${access_token}`;
  }
  return config;
});

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
      defaultTheme='system'
      storageKey={LOCAL_STORAGE_THEME_KEY}
    >
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
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
                  <Index />
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
