import { LogOut, SquarePen, FileText, PanelLeft } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import KnowledgeUpload from './KnowledgeUpload';
import ThemeToggle from './ThemeToggle';
import UserMenu from './UserMenu';
import { LOCAL_STORAGE_AUTH_DATA_KEY } from '@/lib/constants';

interface SidebarProps {
  isOpen: boolean;
  onToggle: () => void;
  onChatSelect?: (chatId: string) => void;
  onNewChat?: () => void;
  currentChatId?: string | null;
}

const Sidebar = ({ isOpen, onToggle, onChatSelect, onNewChat, currentChatId }: SidebarProps) => {
  const navigate = useNavigate();
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false);

  const timeframes = [
    {
      title: 'Hôm qua',
      items: [
        { id: 'chat1', title: 'Top 10 khách hàng có số dư cao nhất' },
        { id: 'chat2', title: 'Báo cáo tăng trưởng CASA' },
      ],
    },
    {
      title: '7 ngày qua',
      items: [
        { id: 'chat3', title: 'Phân tích dư nợ tín dụng theo chi nhánh' },
        { id: 'chat4', title: 'Thống kê khách hàng mới' },
        { id: 'chat5', title: 'So sánh hiệu suất kinh doanh' },
        { id: 'chat6', title: 'Báo cáo rủi ro tín dụng' },
      ],
    },
    {
      title: '30 ngày qua',
      items: [
        { id: 'chat7', title: 'Dashboard tổng quan ngân hàng' },
        { id: 'chat8', title: 'Phân tích xu hướng tiền gửi' },
        { id: 'chat9', title: 'Báo cáo chất lượng tài sản' },
        { id: 'chat10', title: 'Thống kê sản phẩm dịch vụ' },
        { id: 'chat11', title: 'Phân tích khách hàng VIP' },
      ],
    },
  ];

  const handleLogout = () => {
    localStorage.removeItem(LOCAL_STORAGE_AUTH_DATA_KEY);
    navigate('/login');
  };

  const handleChatClick = (chatId: string) => {
    console.log('Đã chọn cuộc trò chuyện:', chatId);
    if (onChatSelect) {
      onChatSelect(chatId);
    }
  };

  const handleNewChat = () => {
    if (onNewChat) {
      onNewChat();
    }
  };

  return (
    <div
      className={cn(
        'fixed left-0 top-0 z-40 h-screen border-r border-gray-200 bg-white transition-all duration-300 ease-in-out dark:border-gray-700 dark:bg-gray-900',
        isOpen ? 'w-64' : 'w-16',
      )}
    >
      <nav className={cn('flex h-full flex-col', isOpen ? 'px-3' : 'px-2')}>
        {/* Top section */}
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
                {timeframes.map((timeframe) => (
                  <div key={timeframe.title}>
                    <div className='px-3 py-2 text-xs text-gray-500 dark:text-gray-400'>
                      {timeframe.title}
                    </div>
                    {timeframe.items.map((item) => (
                      <div
                        key={item.id}
                        onClick={() => handleChatClick(item.id)}
                        className={cn(
                          'group flex h-10 cursor-pointer items-center gap-2.5 rounded-lg px-2 transition-colors hover:bg-gray-100 dark:hover:bg-gray-800',
                          currentChatId === item.id && 'bg-blue-50 dark:bg-blue-900/20',
                        )}
                      >
                        <span className='text-sm text-gray-700 dark:text-gray-300'>
                          {item.title}
                        </span>
                      </div>
                    ))}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Bottom section - single row layout */}
        <div className='border-t border-gray-200 py-2 dark:border-gray-700'>
          <div
            className={cn(
              'flex items-center',
              isOpen ? 'justify-between px-2' : 'flex-col gap-2 px-0',
            )}
          >
            {/* Left group: Settings and Theme */}
            <div className={cn('flex items-center', isOpen ? 'gap-2' : 'flex-col gap-2')}>
              <UserMenu />
              <ThemeToggle />
            </div>

            {/* Right: Logout */}
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

          {/* Logout for collapsed state */}
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
