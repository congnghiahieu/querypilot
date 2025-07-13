import { registerAuthRegisterPostMutation } from '@/api/@tanstack/react-query.gen';
import { zUserCreate } from '@/api/zod.gen';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from '@/hooks/use-toast';
import { zodResolver } from '@hookform/resolvers/zod';
import { useMutation } from '@tanstack/react-query';
import { useForm } from 'react-hook-form';
import { useNavigate } from 'react-router-dom';
import { z } from 'zod';

// Extended schema for form validation including confirmPassword
const registerFormSchema = zUserCreate
  .extend({
    confirmPassword: z.string().min(1, 'Vui lòng xác nhận mật khẩu'),
  })
  .refine((data) => data.password === data.confirmPassword, {
    message: 'Mật khẩu xác nhận không khớp',
    path: ['confirmPassword'],
  });

type RegisterFormData = z.infer<typeof registerFormSchema>;

const Register = () => {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<RegisterFormData>({
    resolver: zodResolver(registerFormSchema),
    defaultValues: {
      username: '',
      password: '',
      confirmPassword: '',
    },
  });

  const registerMutation = useMutation({
    ...registerAuthRegisterPostMutation(),
    onError: (error) => {
      console.error('Registration failed:', error);
      toast({
        title: 'Đăng ký thất bại',
        description: 'Có lỗi xảy ra trong quá trình đăng ký. Vui lòng thử lại.',
        variant: 'destructive',
      });
    },
    onSuccess: () => {
      toast({
        title: 'Đăng ký thành công',
        description: 'Tài khoản đã được tạo thành công. Vui lòng đăng nhập.',
        variant: 'success',
      });
      navigate('/login');
    },
  });

  const onSubmit = (data: RegisterFormData) => {
    const { confirmPassword, ...registerData } = data;
    registerMutation.mutate({
      body: registerData,
    });
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
                disabled={isSubmitting || registerMutation.isPending}
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
                disabled={isSubmitting || registerMutation.isPending}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
              {errors.password && <p className='text-sm text-red-600'>{errors.password.message}</p>}
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
                {...register('confirmPassword')}
                disabled={isSubmitting || registerMutation.isPending}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
              {errors.confirmPassword && (
                <p className='text-sm text-red-600'>{errors.confirmPassword.message}</p>
              )}
            </div>

            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isSubmitting || registerMutation.isPending}
            >
              {isSubmitting || registerMutation.isPending ? 'Đang đăng ký...' : 'Đăng ký'}
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
