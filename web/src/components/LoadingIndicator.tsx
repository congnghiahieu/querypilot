import { useEffect, useState } from 'react';

interface LoadingIndicatorProps {
  text?: string;
}

const LoadingIndicator = ({ text = 'Đang suy nghĩ' }: LoadingIndicatorProps) => {
  const [dots, setDots] = useState('');

  useEffect(() => {
    const interval = setInterval(() => {
      setDots((prev) => {
        if (prev === '...') return '';
        return prev + '.';
      });
    }, 500);

    return () => clearInterval(interval);
  }, []);

  return (
    <div className='flex items-center gap-2 py-2'>
      <div className='flex space-x-1'>
        <div className='h-2 w-2 animate-bounce rounded-full bg-blue-500'></div>
        <div
          className='h-2 w-2 animate-bounce rounded-full bg-blue-500'
          style={{ animationDelay: '0.1s' }}
        ></div>
        <div
          className='h-2 w-2 animate-bounce rounded-full bg-blue-500'
          style={{ animationDelay: '0.2s' }}
        ></div>
      </div>
      <span className='text-gray-600 dark:text-gray-400'>
        {text}
        {dots}
      </span>
    </div>
  );
};

export default LoadingIndicator;
