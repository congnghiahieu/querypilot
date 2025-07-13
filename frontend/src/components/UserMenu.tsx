import { useState } from 'react';
import { User, Settings, Database } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import UserPermissions from './UserPermissions';
import KnowledgeManager from './KnowledgeManager';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { UserResponse } from '@/api';
import { LOCAL_STORAGE_AUTH_DATA_KEY } from '@/lib/constants';

const UserMenu = () => {
  const [isOpen, setIsOpen] = useState(false);
  const [isPermissionsOpen, setIsPermissionsOpen] = useState(false);
  const [isKnowledgeOpen, setIsKnowledgeOpen] = useState(false);

  const authData = localStorage.getItem(LOCAL_STORAGE_AUTH_DATA_KEY);
  const user: UserResponse = authData ? JSON.parse(authData).user : {};

  const handlePermissionsClick = () => {
    setIsOpen(false);
    setIsPermissionsOpen(true);
  };

  const handleKnowledgeClick = () => {
    setIsOpen(false);
    setIsKnowledgeOpen(true);
  };

  return (
    <>
      <Popover
        open={isOpen}
        onOpenChange={setIsOpen}
      >
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <PopoverTrigger asChild>
                <Button
                  variant='ghost'
                  size='sm'
                  className='h-8 w-8 rounded-full p-0 hover:bg-gray-100 dark:hover:bg-gray-800'
                >
                  <Settings className='h-4 w-4' />
                </Button>
              </PopoverTrigger>
            </TooltipTrigger>
            <TooltipContent>
              <p>Cài đặt</p>
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
        <PopoverContent
          className='w-64 border-gray-200 bg-white p-0 dark:border-gray-700 dark:bg-gray-900'
          align='end'
        >
          <div className='p-4'>
            <div className='mb-4 flex items-center gap-3'>
              <div className='flex h-10 w-10 items-center justify-center rounded-full bg-blue-500'>
                <User className='h-5 w-5 text-white' />
              </div>
              <div>
                <p className='font-medium text-gray-900 dark:text-gray-100'>
                  {user.username || 'User'}
                </p>
                <p className='text-sm text-gray-500 dark:text-gray-400'>VPBank Text2SQL</p>
              </div>
            </div>

            <div className='space-y-2'>
              <button
                onClick={handlePermissionsClick}
                className='flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'
              >
                <User className='h-4 w-4 text-gray-500' />
                <span className='text-gray-700 dark:text-gray-300'>Quyền truy cập dữ liệu</span>
              </button>

              <button
                onClick={handleKnowledgeClick}
                className='flex w-full items-center gap-3 rounded-lg px-3 py-2 text-left text-sm transition-colors hover:bg-gray-100 dark:hover:bg-gray-800'
              >
                <Database className='h-4 w-4 text-gray-500' />
                <span className='text-gray-700 dark:text-gray-300'>Quản lý kiến thức</span>
              </button>
            </div>
          </div>
        </PopoverContent>
      </Popover>

      <Dialog
        open={isPermissionsOpen}
        onOpenChange={setIsPermissionsOpen}
      >
        <DialogContent className='max-w-md border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900'>
          <DialogHeader>
            <DialogTitle className='text-gray-900 dark:text-gray-100'>
              Quyền truy cập dữ liệu
            </DialogTitle>
          </DialogHeader>
          <UserPermissions username={user.username || 'user'} />
        </DialogContent>
      </Dialog>

      <Dialog
        open={isKnowledgeOpen}
        onOpenChange={setIsKnowledgeOpen}
      >
        <DialogContent className='max-h-[80vh] max-w-4xl overflow-y-auto border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900'>
          <DialogHeader>
            <DialogTitle className='text-gray-900 dark:text-gray-100'>
              Quản lý kiến thức
            </DialogTitle>
          </DialogHeader>
          <KnowledgeManager />
        </DialogContent>
      </Dialog>
    </>
  );
};

export default UserMenu;
