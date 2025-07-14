import {
  deleteChatByIdChatHistoryChatIdDeleteMutation,
  getChatHistoryChatHistoryGetOptions,
} from '@/api/@tanstack/react-query.gen';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { LOCAL_STORAGE_AUTH_DATA_KEY } from '@/lib/constants';
import { cn } from '@/lib/utils';
import { useChatStore } from '@/stores/chatStore';
import { useMutation, useQuery } from '@tanstack/react-query';
import { FileText, LogOut, PanelLeft, SquarePen, Trash2 } from 'lucide-react';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

import KnowledgeUpload from './KnowledgeUpload';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onChatSelect?: (chatId: string) => void;
  onNewChat?: () => void;
  currentChatId?: string | null;
}

interface ChatSession {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

const Sidebar = ({ isOpen, onToggle, onChatSelect, onNewChat, currentChatId }: SidebarProps) => {
  const navigate = useNavigate();
  const { chatId } = useParams();
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false);

  // Use Zustand store for chat history
  const { chatHistory, setChatHistory, removeChat } = useChatStore();

  // Query to get chat history from server
  const { data: fetchedChatHistory = [], isLoading: isLoadingHistory } = useQuery({
    ...getChatHistoryChatHistoryGetOptions(),
  });

  // Sync server data with Zustand store - Only depend on chatHistoryData
  useEffect(() => {
    if (fetchedChatHistory && fetchedChatHistory.length > 0) {
      setChatHistory(fetchedChatHistory);
    }
  }, [fetchedChatHistory, setChatHistory]); // Only depend on chatHistoryData

  // Mutation to delete chat
  const deleteChatMutation = useMutation({
    ...deleteChatByIdChatHistoryChatIdDeleteMutation(),
    onSuccess: (_, variables) => {
      // Remove from Zustand store immediately
      removeChat(variables.path.chat_id);

      // If we're currently viewing the deleted chat, navigate to welcome
      // Use chatId from useParams() instead of relying on currentChatId prop
      if (chatId === variables.path.chat_id) {
        navigate('/');
      }
    },
    onError: (error) => {
      console.error('Error deleting chat:', error);
    },
  });

  // Categorize chats by time
  const categorizeChatsByTime = (chats: ChatSession[]) => {
    const now = new Date();
    const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
    const yesterday = new Date(today);
    yesterday.setDate(yesterday.getDate() - 1);
    const sevenDaysAgo = new Date(today);
    sevenDaysAgo.setDate(sevenDaysAgo.getDate() - 7);
    const thirtyDaysAgo = new Date(today);
    thirtyDaysAgo.setDate(thirtyDaysAgo.getDate() - 30);

    const todayChats = chats.filter((chat) => new Date(chat.updated_at) >= today);
    const yesterdayChats = chats.filter(
      (chat) => new Date(chat.updated_at) >= yesterday && new Date(chat.updated_at) < today,
    );
    const last7DaysChats = chats.filter(
      (chat) => new Date(chat.updated_at) >= sevenDaysAgo && new Date(chat.updated_at) < yesterday,
    );
    const last30DaysChats = chats.filter(
      (chat) =>
        new Date(chat.updated_at) >= thirtyDaysAgo && new Date(chat.updated_at) < sevenDaysAgo,
    );

    return { todayChats, yesterdayChats, last7DaysChats, last30DaysChats };
  };

  const { todayChats, yesterdayChats, last7DaysChats, last30DaysChats } =
    categorizeChatsByTime(chatHistory);

  // Build dynamic timeframes
  const timeframes = [];

  if (todayChats.length > 0) {
    timeframes.push({
      title: 'Hôm nay',
      items: todayChats.map((chat) => ({ id: chat.id, title: chat.title })),
    });
  }
  if (yesterdayChats.length > 0) {
    timeframes.push({
      title: 'Hôm qua',
      items: yesterdayChats.map((chat) => ({ id: chat.id, title: chat.title })),
    });
  }
  if (last7DaysChats.length > 0) {
    timeframes.push({
      title: '7 ngày qua',
      items: last7DaysChats.map((chat) => ({ id: chat.id, title: chat.title })),
    });
  }
  if (last30DaysChats.length > 0) {
    timeframes.push({
      title: '30 ngày qua',
      items: last30DaysChats.map((chat) => ({ id: chat.id, title: chat.title })),
    });
  }

  const handleLogout = () => {
    localStorage.removeItem(LOCAL_STORAGE_AUTH_DATA_KEY);
    navigate('/login');
  };

  const handleChatClick = (chatId: string) => {
    if (onChatSelect) {
      onChatSelect(chatId);
    }
  };

  const handleNewChat = () => {
    if (onNewChat) {
      onNewChat();
    }
  };

  const handleDeleteChat = (chatId: string, e: React.MouseEvent) => {
    e.stopPropagation(); // Prevent chat selection
    deleteChatMutation.mutate({
      path: { chat_id: chatId },
    });
  };

  return (
    <div
      className={cn(
        'fixed left-0 top-0 z-40 h-screen border-r border-gray-200 bg-white transition-all duration-300 ease-in-out dark:border-gray-700 dark:bg-gray-900',
        isOpen ? 'w-64' : 'w-16',
      )}
    >
      <nav className={cn('flex h-full flex-col', isOpen ? 'px-3' : 'px-2')}>
        <div
          className={cn(
            'flex h-[60px] items-center',
            isOpen ? 'justify-between' : 'flex-col justify-center gap-2',
          )}
        >
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <button
                  onClick={onToggle}
                  className='h-10 rounded-lg px-2 text-gray-600 transition-colors hover:bg-gray-100 dark:text-gray-400 dark:hover:bg-gray-800'
                >
                  <PanelLeft className='h-5 w-5' />
                </button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{isOpen ? 'Thu gọn thanh bên' : 'Mở rộng thanh bên'}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
          {isOpen && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <button
                    onClick={handleNewChat}
                    className='flex items-center gap-2 rounded-lg px-3 py-1 text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'
                  >
                    <SquarePen className='h-4 w-4 text-gray-600 dark:text-gray-400' />
                  </button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>Cuộc trò chuyện mới</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}
        </div>
        {/* Main content - only show when expanded */}
        {isOpen && (
          <div className='relative -mr-2 flex-1 flex-col overflow-y-auto pr-2 transition-opacity duration-500'>
            <div className='bg-white pt-0 dark:bg-gray-900'>
              <div className='flex flex-col gap-2 px-2 py-2'>
                <Dialog
                  open={isKnowledgeOpen}
                  onOpenChange={setIsKnowledgeOpen}
                >
                  <DialogTrigger asChild>
                    <div className='group flex h-10 cursor-pointer items-center gap-2.5 rounded-lg bg-blue-600 px-2 text-white shadow-md transition-colors hover:bg-blue-700'>
                      <FileText className='h-4 w-4' />
                      <span className='text-sm font-medium'>Cung cấp kiến thức</span>
                    </div>
                  </DialogTrigger>
                  <DialogContent className='max-h-[80vh] max-w-4xl overflow-y-auto border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900'>
                    <DialogHeader>
                      <DialogTitle className='text-gray-900 dark:text-gray-100'>
                        Cung cấp kiến thức
                      </DialogTitle>
                    </DialogHeader>
                    <KnowledgeUpload />
                  </DialogContent>
                </Dialog>
              </div>
              <div className='mt-4 flex flex-col gap-4'>
                {isLoadingHistory ?
                  <div className='px-3 py-2 text-sm text-gray-500'>Đang tải lịch sử...</div>
                : timeframes.map((timeframe) => (
                    <div key={timeframe.title}>
                      <div className='px-3 py-2 text-xs text-gray-500 dark:text-gray-400'>
                        {timeframe.title}
                      </div>
                      {timeframe.items.map((item) => (
                        <div
                          key={item.id}
                          className={cn(
                            'group flex h-10 cursor-pointer items-center gap-2.5 rounded-lg px-2 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800',
                            currentChatId === item.id && 'bg-blue-50 dark:bg-blue-900/20',
                          )}
                        >
                          <div
                            className='flex-1 truncate'
                            onClick={() => handleChatClick(item.id)}
                          >
                            <span className='text-sm text-gray-700 dark:text-gray-300'>
                              {item.title}
                            </span>
                          </div>
                          <button
                            onClick={(e) => handleDeleteChat(item.id, e)}
                            className='invisible h-6 w-6 rounded hover:bg-gray-200 group-hover:visible dark:hover:bg-gray-700'
                            disabled={deleteChatMutation.isPending}
                          >
                            <Trash2 className='h-3 w-3 text-gray-500 dark:text-gray-400' />
                          </button>
                        </div>
                      ))}
                    </div>
                  ))
                }
              </div>
            </div>
          </div>
        )}
        <div className='border-t border-gray-200 py-2 dark:border-gray-700'>
          <div
            className={cn(
              'flex items-center',
              isOpen ? 'justify-between px-2' : 'flex-col gap-2 px-0',
            )}
          >
            <div className={cn('flex items-center', isOpen ? 'gap-2' : 'flex-col gap-2')}>
              <UserMenu />
              <ThemeToggle />
            </div>
            {isOpen && (
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant='ghost'
                      size='sm'
                      onClick={handleLogout}
                      className='h-8 w-8 p-0 text-gray-600 hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-900/20 dark:hover:text-red-400'
                    >
                      <LogOut className='h-4 w-4' />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Đăng xuất</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            )}
          </div>
          {!isOpen && (
            <div className='flex justify-center pt-2'>
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <Button
                      variant='ghost'
                      size='sm'
                      onClick={handleLogout}
                      className='h-8 w-8 p-0 text-gray-600 hover:bg-red-50 hover:text-red-600 dark:text-gray-400 dark:hover:bg-red-900/20 dark:hover:text-red-400'
                    >
                      <LogOut className='h-4 w-4' />
                    </Button>
                  </TooltipTrigger>
                  <TooltipContent>
                    <p>Đăng xuất</p>
                  </TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>
          )}
        </div>
      </nav>
    </div>
  );
};

export default Sidebar;
