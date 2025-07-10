import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const ForgotPassword = () => {
  const [email, setEmail] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [isSuccess, setIsSuccess] = useState(false);
  const navigate = useNavigate();

  const handleForgotPassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!email) {
      return;
    }

    setIsLoading(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      setIsSuccess(true);
      console.log('Reset password email sent');
    } catch (error) {
      console.error('Failed to send reset email');
    } finally {
      setIsLoading(false);
    }
  };

  if (isSuccess) {
    return (
      <div className='flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 dark:from-slate-900 dark:to-slate-800'>
        <Card className='w-full max-w-md border-slate-200 bg-white/90 shadow-xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/90'>
          <CardHeader className='space-y-1'>
            <CardTitle className='text-center text-2xl font-bold text-slate-900 dark:text-slate-100'>
              Email đã được gửi
            </CardTitle>
            <CardDescription className='text-center text-slate-600 dark:text-slate-400'>
              Vui lòng kiểm tra email của bạn để nhận hướng dẫn khôi phục mật khẩu
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button
              onClick={() => navigate('/login')}
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
            >
              Quay lại đăng nhập
            </Button>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className='flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 dark:from-slate-900 dark:to-slate-800'>
      <Card className='w-full max-w-md border-slate-200 bg-white/90 shadow-xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/90'>
        <CardHeader className='space-y-1'>
          <CardTitle className='text-center text-2xl font-bold text-slate-900 dark:text-slate-100'>
            Quên mật khẩu
          </CardTitle>
          <CardDescription className='text-center text-slate-600 dark:text-slate-400'>
            Nhập email để nhận hướng dẫn khôi phục mật khẩu
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleForgotPassword}
            className='space-y-4'
          >
            <div className='space-y-2'>
              <Label
                htmlFor='email'
                className='text-slate-700 dark:text-slate-300'
              >
                Email
              </Label>
              <Input
                id='email'
                type='email'
                placeholder='Nhập email của bạn'
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isLoading}
            >
              {isLoading ? 'Đang gửi...' : 'Gửi hướng dẫn khôi phục'}
            </Button>
          </form>

          <div className='mt-6 text-center'>
            <button
              onClick={() => navigate('/login')}
              className='text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300'
            >
              Quay lại đăng nhập
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default ForgotPassword;
