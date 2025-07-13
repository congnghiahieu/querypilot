import { forgotPasswordAuthForgotPasswordPostMutation } from '@/api/@tanstack/react-query.gen';
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

const forgotPasswordSchema = z.object({
  email: z.email('Email không hợp lệ'),
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

const ForgotPassword = () => {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    formState: { errors, isSubmitting },
  } = useForm<ForgotPasswordFormData>({
    resolver: zodResolver(forgotPasswordSchema),
    defaultValues: {
      email: '',
    },
  });

  const forgotPasswordMutation = useMutation({
    ...forgotPasswordAuthForgotPasswordPostMutation(),
    onError: (error) => {
      console.error('Forgot password failed:', error);
      toast({
        title: 'Gửi email thất bại',
        description: 'Có lỗi xảy ra. Vui lòng thử lại.',
        variant: 'destructive',
      });
    },
    onSuccess: () => {
      toast({
        title: 'Email đã được gửi',
        description: 'Vui lòng kiểm tra email để đặt lại mật khẩu.',
      });
      navigate('/login');
    },
  });

  const onSubmit = (data: ForgotPasswordFormData) => {
    forgotPasswordMutation.mutate({
      body: { email: data.email },
    });
  };

  return (
    <div className='flex min-h-screen items-center justify-center bg-gradient-to-br from-slate-100 to-slate-200 px-4 dark:from-slate-900 dark:to-slate-800'>
      <Card className='w-full max-w-md border-slate-200 bg-white/90 shadow-xl backdrop-blur-sm dark:border-slate-700 dark:bg-slate-800/90'>
        <CardHeader className='space-y-1'>
          <CardTitle className='text-center text-2xl font-bold text-slate-900 dark:text-slate-100'>
            Quên mật khẩu
          </CardTitle>
          <CardDescription className='text-center text-slate-600 dark:text-slate-400'>
            Nhập email để nhận hướng dẫn đặt lại mật khẩu
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            onSubmit={handleSubmit(onSubmit)}
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
                {...register('email')}
                disabled={isSubmitting || forgotPasswordMutation.isPending}
                className='border-slate-300 bg-white/70 dark:border-slate-600 dark:bg-slate-700/70'
              />
              {errors.email && <p className='text-sm text-red-600'>{errors.email.message}</p>}
            </div>

            <Button
              type='submit'
              className='w-full bg-blue-600 font-medium text-white hover:bg-blue-700'
              disabled={isSubmitting || forgotPasswordMutation.isPending}
            >
              {isSubmitting || forgotPasswordMutation.isPending ? 'Đang gửi...' : 'Gửi email'}
            </Button>
          </form>

          <div className='mt-6 text-center text-sm'>
            <button
              onClick={() => navigate('/login')}
              className='text-blue-600 hover:text-blue-800 dark:text-blue-400 dark:hover:text-blue-300'
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
