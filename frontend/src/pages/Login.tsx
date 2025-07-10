import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const Login = () => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!username || !password) {
      return;
    }

    setIsLoading(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      localStorage.setItem('user', JSON.stringify({ username }));
      navigate('/');
    } catch (error) {
      console.error('Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className='flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 dark:from-slate-900 dark:to-slate-800'>
      <Card className='w-full max-w-md border-slate-200 bg-white/90 shadow-xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/90'>
        <CardHeader className='space-y-1'>
          <CardTitle className='text-center text-2xl font-bold text-slate-900 dark:text-slate-100'>
            VPBank Text2SQL
          </CardTitle>
          <CardDescription className='text-center text-slate-600 dark:text-slate-400'>
            Đăng nhập để sử dụng hệ thống chatbot hỏi đáp dữ liệu
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleLogin}
            className='space-y-4'
          >
            <div className='space-y-2'>
              <Label
                htmlFor='username'
                className='text-slate-700 dark:text-slate-300'
              >
                Tên đăng nhập
              </Label>
              <Input
                id='username'
                type='text'
                placeholder='Nhập tên đăng nhập'
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
            <div className='space-y-2'>
              <Label
                htmlFor='password'
                className='text-slate-700 dark:text-slate-300'
              >
                Mật khẩu
              </Label>
              <Input
                id='password'
                type='password'
                placeholder='Nhập mật khẩu'
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isLoading}
            >
              {isLoading ? 'Đang đăng nhập...' : 'Đăng nhập'}
            </Button>
          </form>

          <div className='mt-6 flex justify-between text-sm'>
            <button
              onClick={() => navigate('/register')}
              className='text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300'
            >
              Đăng ký
            </button>
            <button
              onClick={() => navigate('/forgot-password')}
              className='text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300'
            >
              Quên mật khẩu?
            </button>
          </div>

          <div className='mt-6 text-center text-sm text-slate-500 dark:text-slate-400'>
            <p>Hệ thống chatbot Text2SQL cho VPBank</p>
            <p className='mt-1'>Hỗ trợ truy vấn dữ liệu thông minh với phân quyền</p>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Login;
