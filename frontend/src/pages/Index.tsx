import {
  continueChatChatContinueChatIdPostMutation,
  getChatByIdChatHistoryChatIdGetOptions,
} from '@/api/@tanstack/react-query.gen';
import ChatHeader from '@/components/ChatHeader';
import ChatInput from '@/components/ChatInput';
import MessageList from '@/components/MessageList';
import Sidebar from '@/components/Sidebar';
import { useMutation, useQuery } from '@tanstack/react-query';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

type Message = {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  response_type?: string;
  execution_time?: number;
  rows_count?: number;
  created_at: string;
  has_data?: boolean;
  data?: {
    type: 'table' | 'chart';
    tableData?: {
      data: any[];
      columns: string[];
      title?: string;
      sqlQuery?: string;
    };
    chartData?: {
      data: any[];
      title: string;
      xAxisKey: string;
      yAxisKey: string;
      type?: 'bar' | 'line' | 'pie';
      sqlQuery?: string;
    };
  };
  isStreaming?: boolean;
  isLoading?: boolean;
};

const Index = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(chatId || null);
  const [chatTitle, setChatTitle] = useState<string>('');

  // Query to get chat history
  const { data: chatData, isLoading: isLoadingChat } = useQuery({
    ...getChatByIdChatHistoryChatIdGetOptions({
      path: { chat_id: chatId! },
    }),
    enabled: !!chatId,
  });

  // Mutation to continue chat
  const continueChatMutation = useMutation({
    ...continueChatChatContinueChatIdPostMutation(),
    onSuccess: (data) => {
      // Add the new assistant message to messages
      const response = data.response;
      const newMessage: Message = {
        id: data.message_id,
        role: 'assistant',
        content: response.content,
        sql_query: response.sql_query,
        response_type: response.type,
        execution_time: response.execution_time,
        rows_count: response.rows_count,
        created_at: new Date().toISOString(),
        has_data: response.type === 'table' || response.type === 'chart',
        // Parse data if available
        data:
          response.type === 'table' ?
            {
              type: 'table',
              tableData: {
                data: JSON.parse(response.content),
                columns: Object.keys(JSON.parse(response.content)[0] || {}),
                title: 'Query Results',
                sqlQuery: response.sql_query,
              },
            }
          : response.type === 'chart' ?
            {
              type: 'chart',
              chartData: {
                data: JSON.parse(response.content),
                title: 'Chart Data',
                xAxisKey: 'x',
                yAxisKey: 'y',
                type: 'bar',
                sqlQuery: response.sql_query,
              },
            }
          : undefined,
      };

      setMessages((prev) => [...prev, newMessage]);
    },
    onError: (error) => {
      console.error('Error continuing chat:', error);
    },
  });

  // Load chat data when component mounts or chatId changes
  useEffect(() => {
    if (chatData) {
      setChatTitle(chatData.title);
      setCurrentChatId(chatData.id);

      // Convert backend messages to frontend format
      const formattedMessages: Message[] = chatData.messages.map((msg: any) => ({
        id: msg.id,
        role: msg.role,
        content: msg.content,
        sql_query: msg.sql_query,
        response_type: msg.response_type,
        execution_time: msg.execution_time,
        rows_count: msg.rows_count,
        created_at: msg.created_at,
        has_data: msg.has_data,
        // For assistant messages with data, we might need to fetch data separately
        data:
          msg.response_type === 'table' && msg.has_data ?
            {
              type: 'table',
              tableData: {
                data: [], // Will be loaded separately if needed
                columns: [],
                title: 'Query Results',
                sqlQuery: msg.sql_query,
              },
            }
          : undefined,
      }));

      setMessages(formattedMessages);
    }
  }, [chatData]);

  const handleSendMessage = async (
    message: string,
    options?: { search?: string; data?: string },
  ) => {
    if (!message.trim() || !chatId) return;

    // Add user message immediately
    const userMessage: Message = {
      id: `temp-${Date.now()}`,
      role: 'user',
      content: message,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Call backend to continue chat
    continueChatMutation.mutate({
      path: { chat_id: chatId },
      body: { message },
    });
  };

  const loadChatSession = (selectedChatId: string) => {
    navigate(`/${selectedChatId}`);
  };

  const startNewChat = () => {
    navigate('/');
  };

  // If no chatId, redirect to welcome
  if (!chatId) {
    navigate('/');
    return null;
  }

  return (
    <div className='flex h-screen bg-background text-foreground transition-colors duration-300'>
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onChatSelect={loadChatSession}
        onNewChat={startNewChat}
        currentChatId={currentChatId}
      />

      {/* Main content area */}
      <div
        className={`flex flex-1 flex-col transition-all duration-300 ${
          isSidebarOpen ? 'ml-64' : 'ml-16'
        }`}
      >
        {/* Fixed header */}
        <div
          className='fixed right-0 top-0 z-30 transition-all duration-300'
          style={{ left: isSidebarOpen ? '256px' : '64px' }}
        >
          <ChatHeader
            isSidebarOpen={isSidebarOpen}
            chatTitle={chatTitle}
          />
        </div>

        {/* Main chat area */}
        <div className='flex-1 pt-[60px]'>
          {/* Scrollable messages area */}
          <div className='h-full overflow-y-auto pb-[120px]'>
            <MessageList messages={messages} />
          </div>

          {/* Fixed input at bottom */}
          <div
            className='fixed bottom-0 right-0 z-20 border-t border-gray-200 bg-white/95 p-4 backdrop-blur transition-all duration-300 dark:border-gray-700 dark:bg-gray-900/95'
            style={{ left: isSidebarOpen ? '256px' : '64px' }}
          >
            <ChatInput
              onSend={handleSendMessage}
              isLoading={continueChatMutation.isPending}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
