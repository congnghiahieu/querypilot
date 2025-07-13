import { getMessageDataChatDataMessageIdGetOptions } from '@/api/@tanstack/react-query.gen';
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';

import DataChart from './DataChart';
import DataTable from './DataTable';
import LoadingIndicator from './LoadingIndicator';
import MessageActions from './MessageActions';
import MessageAvatar from './MessageAvatar';
import TypewriterText from './TypewriterText';

export type MessageProps = {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  sql_query?: string;
  response_type?: string;
  execution_time?: number;
  rows_count?: number;
  created_at?: string;
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
  onRegenerate?: () => void;
};

const Message = ({
  id,
  role,
  content,
  has_data = false,
  sql_query,
  response_type,
  data,
  isStreaming = false,
  isLoading = false,
  onRegenerate,
}: MessageProps) => {
  const [streamingComplete, setStreamingComplete] = useState(false);

  // Fetch message data if this is an assistant message with data
  const { data: messageData } = useQuery({
    ...getMessageDataChatDataMessageIdGetOptions({
      path: { message_id: id! },
    }),
    enabled: !!(id && role === 'assistant' && has_data && response_type === 'table'),
  });

  // Determine what data to display
  const displayData =
    data ||
    (messageData ?
      {
        type: 'table' as const,
        tableData: {
          data: messageData.data,
          columns: messageData.columns,
          title: 'Query Results',
          sqlQuery: messageData.sql_query,
        },
      }
    : undefined);

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
          {role === 'assistant' && displayData && (!isStreaming || streamingComplete) && (
            <div className='mt-4'>
              {displayData.type === 'table' && displayData.tableData && (
                <DataTable {...displayData.tableData} />
              )}
              {displayData.type === 'chart' && displayData.chartData && (
                <DataChart {...displayData.chartData} />
              )}
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
