import KnowledgeUpload from '@/components/KnowledgeUpload';
import { Button } from '@/components/ui/button';
import { ArrowLeft } from 'lucide-react';

interface KnowledgeProps {
  onBack: () => void;
}

const Knowledge = ({ onBack }: KnowledgeProps) => {
  return (
    <div className='flex h-full flex-col'>
      <div className='flex items-center gap-4 border-b p-4'>
        <Button
          variant='ghost'
          size='sm'
          onClick={onBack}
        >
          <ArrowLeft className='mr-2 h-4 w-4' />
          Quay lại chat
        </Button>
        <h1 className='text-xl font-semibold'>Quản lý kiến thức</h1>
      </div>

      <div className='flex-1 overflow-y-auto p-6'>
        <div className='mx-auto max-w-4xl'>
          <div className='mb-6'>
            <h2 className='mb-2 text-lg font-medium'>Định nghĩa khái niệm nghiệp vụ</h2>
            <p className='text-gray-600'>
              Thêm các định nghĩa khái niệm từ bên ngoài để bot có thể hiểu và trả lời các câu hỏi
              phức tạp hơn. Ví dụ: "Dư nợ tín dụng thông thường" = "Dư nợ tín dụng món vay" + "Dư nợ
              tín dụng thấu chi"
            </p>
          </div>

          <KnowledgeUpload />
        </div>
      </div>
    </div>
  );
};

export default Knowledge;
