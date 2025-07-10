import Message from './Message';

type Message = {
  role: 'user' | 'assistant';
  content: string;
};

const MessageList = ({ messages }: { messages: Message[] }) => {
  return (
    <div className='flex-1 overflow-y-auto'>
      <div className='mx-auto w-full max-w-3xl px-4'>
        {messages.map((message, index) => (
          <Message
            key={index}
            {...message}
          />
        ))}
      </div>
    </div>
  );
};

export default MessageList;
