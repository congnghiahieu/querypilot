import { useState } from 'react';
import MessageAvatar from './MessageAvatar';
import MessageActions from './MessageActions';
import DataTable from './DataTable';
import DataChart from './DataChart';
import TypewriterText from './TypewriterText';
import LoadingIndicator from './LoadingIndicator';

type MessageProps = {
  role: 'user' | 'assistant';
  content: string;
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
  onRegenerate?: () => void;
};

const Message = ({
  role,
  content,
  data,
  isStreaming = false,
  isLoading = false,
  onRegenerate,
}: MessageProps) => {
  const [streamingComplete, setStreamingComplete] = useState(false);

  return (
    <div className='py-6'>
      <div className={`flex gap-4 ${role === 'user' ? 'flex-row-reverse' : ''}`}>
        <MessageAvatar isAssistant={role === 'assistant'} />
        <div className={`flex-1 space-y-4 ${role === 'user' ? 'flex justify-end' : ''}`}>
          <div
            className={`${role === 'user' ? 'inline-block rounded-[20px] bg-blue-100 px-4 py-2 text-blue-900 dark:bg-blue-900 dark:text-blue-100' : ''}`}
          >
            {isLoading && role === 'assistant' ?
              <LoadingIndicator />
            : isStreaming && role === 'assistant' ?
              <TypewriterText
                text={content}
                onComplete={() => setStreamingComplete(true)}
                speed={10}
              />
            : content}
          </div>

          {/* Data visualization section */}
          {role === 'assistant' && data && (!isStreaming || streamingComplete) && (
            <div className='mt-4'>
              {data.type === 'table' && data.tableData && <DataTable {...data.tableData} />}
              {data.type === 'chart' && data.chartData && <DataChart {...data.chartData} />}
            </div>
          )}

          {role === 'assistant' && (
            <MessageActions
              content={content}
              onRegenerate={onRegenerate}
            />
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;
