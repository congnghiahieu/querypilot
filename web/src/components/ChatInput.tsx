import { useState, useRef } from 'react';
import { Send } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import SessionUpload from './SessionUpload';

interface ChatInputProps {
  onSend: (message: string, options?: { search?: string; data?: string }) => void;
  isLoading?: boolean;
}

const ChatInput = ({ onSend, isLoading = false }: ChatInputProps) => {
  const [message, setMessage] = useState('');
  const [selectedSearchOption, setSelectedSearchOption] = useState<string>('');
  const [selectedDataOption, setSelectedDataOption] = useState<string>('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      const options = {
        search: selectedSearchOption || undefined,
        data: selectedDataOption || undefined,
      };
      onSend(message.trim(), options);
      setMessage('');
      setSelectedSearchOption('');
      setSelectedDataOption('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const handleTextareaChange = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setMessage(e.target.value);
    // Auto-resize textarea
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
    }
  };

  const handleFileUpload = (files: File[]) => {
    console.log('Các tệp đã tải lên cho phiên này:', files);
  };

  return (
    <form
      onSubmit={handleSubmit}
      className='w-full'
    >
      <div className='mx-auto max-w-4xl'>
        <div className='flex items-center gap-3 rounded-2xl border border-gray-200 bg-white p-3 shadow-sm dark:border-gray-700 dark:bg-gray-900'>
          <SessionUpload onFileUpload={handleFileUpload} />

          <div className='flex-1'>
            <Textarea
              ref={textareaRef}
              value={message}
              onChange={handleTextareaChange}
              onKeyDown={handleKeyDown}
              placeholder='Hỏi bất kỳ điều gì mà bạn muốn biết với sự hỗ trợ của VPBank Text2SQL'
              disabled={isLoading}
              className='max-h-32 min-h-[24px] resize-none border-0 bg-transparent p-0 text-sm text-gray-900 placeholder:text-gray-500 focus:outline-none focus:ring-0 focus-visible:ring-0 focus-visible:ring-offset-0 dark:text-gray-100 dark:placeholder:text-gray-400'
              rows={1}
            />
          </div>

          <Button
            type='submit'
            size='sm'
            disabled={!message.trim() || isLoading}
            className='h-8 w-8 rounded-lg bg-blue-500 p-0 text-white hover:bg-blue-600 disabled:bg-gray-300 dark:disabled:bg-gray-600'
          >
            <Send className='h-4 w-4' />
          </Button>
        </div>
      </div>
    </form>
  );
};

export default ChatInput;
