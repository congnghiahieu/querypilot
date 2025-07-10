import { Bot } from 'lucide-react';

const EmptyChatState = () => {
  return (
    <div className='mb-12 text-center'>
      <div className='mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30'>
        <Bot className='h-8 w-8 text-blue-600 dark:text-blue-400' />
      </div>
      <h1 className='mb-2 text-2xl font-semibold text-gray-900 dark:text-gray-100'>
        VPBank Text2SQL
      </h1>
      <p className='text-gray-600 dark:text-gray-400'>
        Hỏi tôi bất cứ điều gì về dữ liệu ngân hàng của bạn
      </p>
    </div>
  );
};

export default EmptyChatState;
