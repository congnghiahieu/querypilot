import Message, { type MessageProps } from './Message';

interface MessageListProps {
  messages: Array<MessageProps>;
}

const MessageList = ({ messages }: MessageListProps) => {
  return (
    <div className='mx-auto max-w-4xl px-4'>
      {messages.map((message, index) => (
        <Message
          key={message.id || index}
          id={message.id}
          role={message.role}
          content={message.content}
          sql_query={message.sql_query}
          response_type={message.response_type}
          execution_time={message.execution_time}
          rows_count={message.rows_count}
          has_data={message.has_data}
          data={message.data}
          isStreaming={message.isStreaming}
          isLoading={message.isLoading}
        />
      ))}
    </div>
  );
};

export default MessageList;
