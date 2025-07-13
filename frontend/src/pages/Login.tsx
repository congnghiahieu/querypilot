import { loginAuthLoginPostMutation } from '@/api/@tanstack/react-query.gen';
import { zUserLogin } from '@/api/zod.gen';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';
import { LOCAL_STORAGE_AUTH_DATA_KEY } from '@/lib/constants';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

type LoginFormData = z.infer<typeof zUserLogin>;

const Login = () => {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<LoginFormData>({
    resolver: zodResolver(zUserLogin),
    defaultValues: {
      username: '',
      password: '',
    },
  });

  const loginMutation = useMutation({
    ...loginAuthLoginPostMutation(),
    onError: (error) => {
      console.error('Login failed:', error);
      toast({
        title: 'Đăng nhập thất bại',
        description: 'Tên đăng nhập hoặc mật khẩu không đúng',
        variant: 'destructive',
      });
    },
    onSuccess: (data) => {
      // Store the complete response data
      localStorage.setItem(LOCAL_STORAGE_AUTH_DATA_KEY, JSON.stringify(data));

      toast({
        title: 'Đăng nhập thành công',
        description: 'Chào mừng bạn đến với VPBank Text2SQL',
        variant: 'success',
      });
      navigate('/');
    },
  });

  const onSubmit = (data: LoginFormData) => {
    loginMutation.mutate({
      body: data,
    });
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
            onSubmit={handleSubmit(onSubmit)}
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
                {...register('username')}
                disabled={isSubmitting || loginMutation.isPending}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
              {errors.username && <p className='text-sm text-red-600'>{errors.username.message}</p>}
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
                {...register('password')}
                disabled={isSubmitting || loginMutation.isPending}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
              {errors.password && <p className='text-sm text-red-600'>{errors.password.message}</p>}
            </div>

            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isSubmitting || loginMutation.isPending}
            >
              {isSubmitting || loginMutation.isPending ? 'Đang đăng nhập...' : 'Đăng nhập'}
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
