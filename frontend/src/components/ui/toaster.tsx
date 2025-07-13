import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastViewport as ToastPrimitivesViewport,
  ToastProvider,
  ToastTitle,
} from '@/components/ui/toast';
import { useToast } from '@/hooks/use-toast';
import { cn } from '@/lib/utils';
import React from 'react';

const ToastViewport = React.forwardRef<
  React.ElementRef<typeof ToastPrimitivesViewport>,
  React.ComponentPropsWithoutRef<typeof ToastPrimitivesViewport>
>(({ className, ...props }, ref) => (
  <ToastPrimitivesViewport
    ref={ref}
    className={cn(
      'fixed right-4 top-4 z-[100] flex max-h-screen w-full max-w-md flex-col gap-2 p-4',
      className,
    )}
    {...props}
  />
));

export function Toaster() {
  const { toasts } = useToast();

  return (
    <ToastProvider>
      {toasts.map(function ({ id, title, description, action, ...props }) {
        return (
          <Toast
            key={id}
            {...props}
          >
            <div className='grid gap-1'>
              {title && <ToastTitle>{title}</ToastTitle>}
              {description && <ToastDescription>{description}</ToastDescription>}
            </div>
            {action}
            <ToastClose />
          </Toast>
        );
      })}
      <ToastViewport />
    </ToastProvider>
  );
}
