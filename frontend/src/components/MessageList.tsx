import { forwardRef, useEffect, useImperativeHandle, useRef } from 'react';

import Message from './Message';

type MessageType = {
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

interface MessageListProps {
  messages: MessageType[];
}

export interface MessageListRef {
  scrollToBottom: () => void;
}

const MessageList = forwardRef<MessageListRef, MessageListProps>(({ messages }, ref) => {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const containerRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'instant' });
  };

  useImperativeHandle(ref, () => ({
    scrollToBottom,
  }));

  // Scroll to bottom when messages change (new message added)
  useEffect(() => {
    scrollToBottom();
  }, [messages.length]);

  // Scroll to bottom when component first loads with existing messages
  useEffect(() => {
    if (messages.length > 0) {
      // Use timeout to ensure DOM is rendered
      setTimeout(() => {
        scrollToBottom();
      }, 100);
    }
  }, [messages.length > 0]);

  return (
    <div
      ref={containerRef}
      className='flex flex-col gap-4 p-4'
    >
      {messages.map((message) => (
        <Message
          key={message.id}
          id={message.id}
          role={message.role}
          content={message.content}
          sql_query={message.sql_query}
          response_type={message.response_type}
          execution_time={message.execution_time}
          rows_count={message.rows_count}
          created_at={message.created_at}
          has_data={message.has_data}
          data={message.data}
          isStreaming={message.isStreaming}
          isLoading={message.isLoading}
        />
      ))}
      {/* Invisible div to scroll to */}
      <div ref={messagesEndRef} />
    </div>
  );
});

MessageList.displayName = 'MessageList';

export default MessageList;
