import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Copy, RefreshCw, ThumbsDown, ThumbsUp } from 'lucide-react';
import { useState } from 'react';

interface MessageActionsProps {
  content: string;
  onRegenerate?: () => void;
}

const MessageActions = ({ content, onRegenerate }: MessageActionsProps) => {
  const [copied, setCopied] = useState(false);
  const [liked, setLiked] = useState(false);
  const [disliked, setDisliked] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
      console.log('Đã sao chép nội dung tin nhắn');
    } catch (err) {
      console.error('Không thể sao chép:', err);
    }
  };

  const handleLike = () => {
    setLiked(!liked);
    setDisliked(false);
    console.log(liked ? 'Bỏ thích tin nhắn' : 'Thích tin nhắn');
  };

  const handleDislike = () => {
    setDisliked(!disliked);
    setLiked(false);
    console.log(disliked ? 'Bỏ không thích tin nhắn' : 'Không thích tin nhắn');
  };

  const handleRegenerate = () => {
    if (onRegenerate) {
      onRegenerate();
    }
    console.log('Tạo lại phản hồi');
  };

  return (
    <div className='flex items-center gap-1 pt-2'>
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant='ghost'
              size='sm'
              onClick={handleCopy}
              className='h-7 w-7 p-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            >
              <Copy className={`h-3 w-3 ${copied ? 'text-green-500' : ''}`} />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{copied ? 'Đã sao chép!' : 'Sao chép'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant='ghost'
              size='sm'
              onClick={handleLike}
              className={`h-7 w-7 p-0 ${
                liked ?
                  'text-blue-500 hover:text-blue-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <ThumbsUp className='h-3 w-3' />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{liked ? 'Bỏ thích' : 'Thích'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant='ghost'
              size='sm'
              onClick={handleDislike}
              className={`h-7 w-7 p-0 ${
                disliked ?
                  'text-red-500 hover:text-red-600'
                : 'text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
              }`}
            >
              <ThumbsDown className='h-3 w-3' />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>{disliked ? 'Bỏ không thích' : 'Không thích'}</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>

      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant='ghost'
              size='sm'
              onClick={handleRegenerate}
              className='h-7 w-7 p-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            >
              <RefreshCw className='h-3 w-3' />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Tạo lại</p>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    </div>
  );
};

export default MessageActions;
