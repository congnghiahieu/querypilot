import ChatInput from '@/components/ChatInput';
import EmptyChatState from '@/components/EmptyChatState';
import Sidebar from '@/components/Sidebar';
import { NEW_CHAT_EVENT_NAME } from '@/lib/constants';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Welcome = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [isLoading, setIsLoading] = useState(false);

  // Generate random chat ID and title
  const generateChatId = () => {
    return `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const generateChatTitle = (message: string) => {
    // Simple title generation - take first 50 characters
    const title = message.length > 50 ? message.substring(0, 50) + '...' : message;
    return title;
  };

  const handleSendMessage = async (
    message: string,
    options?: { search?: string; data?: string },
  ) => {
    if (!message.trim()) return;

    // Generate new chat ID and navigate to it
    const chatId = generateChatId();
    const title = generateChatTitle(message);

    // Store initial message and title in localStorage for the new chat
    localStorage.setItem(
      `chat-${chatId}`,
      JSON.stringify({
        id: chatId,
        title,
        initialMessage: message,
        initialOptions: options,
      }),
    );

    // Dispatch event to notify sidebar of new chat
    const event = new CustomEvent(NEW_CHAT_EVENT_NAME, {
      detail: { chatId, title },
    });
    window.dispatchEvent(event);

    // Navigate to the new chat
    navigate(`/${chatId}`);
  };

  const loadChatSession = (chatId: string) => {
    navigate(`/${chatId}`);
  };

  const startNewChat = () => {
    // Already on welcome page, just ensure we're at root
    navigate('/');
  };

  return (
    <div className='flex h-screen bg-background text-foreground transition-colors duration-300'>
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onChatSelect={loadChatSession}
        onNewChat={startNewChat}
        currentChatId={null}
      />

      {/* Main content area */}
      <div
        className={`flex flex-1 flex-col transition-all duration-300 ${
          isSidebarOpen ? 'ml-64' : 'ml-16'
        }`}
      >
        {/* Welcome state - chat input centered */}
        <div className='flex h-full flex-col items-center justify-center px-4'>
          <EmptyChatState />
          <div className='w-full max-w-3xl'>
            <ChatInput
              onSend={handleSendMessage}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
