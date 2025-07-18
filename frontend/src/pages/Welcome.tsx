import { newChatChatNewPostMutation } from '@/api/@tanstack/react-query.gen';
import ChatInput from '@/components/ChatInput';
import EmptyChatState from '@/components/EmptyChatState';
import Sidebar from '@/components/Sidebar';
import { useChatStore } from '@/stores/chatStore';
import { useMutation } from '@tanstack/react-query';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';

const Welcome = () => {
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const { addChat } = useChatStore();

  const newChatMutation = useMutation({
    ...newChatChatNewPostMutation(),
    onSuccess: (data) => {
      // Add to Zustand store immediately
      addChat({
        id: data.chat_id,
        title: data.title,
        created_at: data.created_at,
        updated_at: data.updated_at,
        message_count: 1, // First message
      });

      // Navigate to the new chat with the returned chat_id
      navigate(`/${data.chat_id}`);
    },
    onError: (error) => {
      console.error('Error creating new chat:', error);
      // Handle error (show toast, etc.)
    },
  });

  const handleSendMessage = async (
    message: string,
    options?: { search?: string; data?: string },
  ) => {
    if (!message.trim()) return;

    // Call backend to create new chat
    newChatMutation.mutate({
      body: { message },
    });
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
              isLoading={newChatMutation.isPending}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Welcome;
