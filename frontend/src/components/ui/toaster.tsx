import { useToast } from '@/hooks/use-toast';
import {
  Toast,
  ToastClose,
  ToastDescription,
  ToastProvider,
  ToastTitle,
  ToastViewport as ToastPrimitivesViewport,
} from '@/components/ui/toast';
import React from 'react';
import { cn } from '@/lib/utils';

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
