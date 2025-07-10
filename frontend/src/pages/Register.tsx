import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

const Register = () => {
  const [formData, setFormData] = useState({
    fullname: '',
    email: '',
    username: '',
    password: '',
    confirmPassword: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const navigate = useNavigate();

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!formData.fullname || !formData.email || !formData.username || !formData.password) {
      return;
    }

    if (formData.password !== formData.confirmPassword) {
      return;
    }

    setIsLoading(true);

    try {
      await new Promise((resolve) => setTimeout(resolve, 1000));
      console.log('Registration successful');
      navigate('/login');
    } catch (error) {
      console.error('Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (field: string, value: string) => {
    setFormData((prev) => ({ ...prev, [field]: value }));
  };

  return (
    <div className='flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 dark:from-slate-900 dark:to-slate-800'>
      <Card className='w-full max-w-md border-slate-200 bg-white/90 shadow-xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/90'>
        <CardHeader className='space-y-1'>
          <CardTitle className='text-center text-2xl font-bold text-slate-900 dark:text-slate-100'>
            Đăng ký tài khoản
          </CardTitle>
          <CardDescription className='text-center text-slate-600 dark:text-slate-400'>
            Tạo tài khoản mới cho VPBank Text2SQL
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleRegister}
            className='space-y-4'
          >
            <div className='space-y-2'>
              <Label
                htmlFor='fullname'
                className='text-slate-700 dark:text-slate-300'
              >
                Họ và tên
              </Label>
              <Input
                id='fullname'
                type='text'
                placeholder='Nhập họ tên đầy đủ'
                value={formData.fullname}
                onChange={(e) => handleInputChange('fullname', e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
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
                placeholder='Nhập email'
                value={formData.email}
                onChange={(e) => handleInputChange('email', e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
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
                value={formData.username}
                onChange={(e) => handleInputChange('username', e.target.value)}
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
                value={formData.password}
                onChange={(e) => handleInputChange('password', e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
            <div className='space-y-2'>
              <Label
                htmlFor='confirmPassword'
                className='text-slate-700 dark:text-slate-300'
              >
                Xác nhận mật khẩu
              </Label>
              <Input
                id='confirmPassword'
                type='password'
                placeholder='Nhập lại mật khẩu'
                value={formData.confirmPassword}
                onChange={(e) => handleInputChange('confirmPassword', e.target.value)}
                disabled={isLoading}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
            </div>
            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isLoading}
            >
              {isLoading ? 'Đang đăng ký...' : 'Đăng ký'}
            </Button>
          </form>

          <div className='mt-6 text-center'>
            <button
              onClick={() => navigate('/login')}
              className='text-sm text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300'
            >
              Đã có tài khoản? Đăng nhập
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};

export default Register;
