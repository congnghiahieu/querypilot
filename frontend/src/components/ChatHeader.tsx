interface ChatHeaderProps {
  isSidebarOpen?: boolean;
  chatTitle?: string;
}

const ChatHeader = ({ isSidebarOpen = true, chatTitle }: ChatHeaderProps) => {
  return (
    <div className='fixed top-0 z-30 w-full border-b border-gray-200 bg-white/95 backdrop-blur dark:border-gray-700 dark:bg-gray-900/95'>
      <div className='flex h-[60px] items-center justify-between px-4'>
        <div className='flex items-center gap-2'>
          <span
            className={`font-semibold text-gray-900 dark:text-gray-100 ${!isSidebarOpen ? 'ml-12' : ''}`}
          >
            {chatTitle || 'VPBank Text2SQL'}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ChatHeader;
