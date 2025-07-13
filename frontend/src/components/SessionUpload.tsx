import { Button } from '@/components/ui/button';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { FileText, X } from 'lucide-react';
import { useRef, useState } from 'react';

interface SessionUploadProps {
  onFileUpload: (files: File[]) => void;
}

const SessionUpload = ({ onFileUpload }: SessionUploadProps) => {
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileSelect = (event: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(event.target.files || []);

    if (files.length === 0) return;

    // Validate file types
    const validFiles = files.filter(
      (file) =>
        file.name.endsWith('.xlsx') ||
        file.name.endsWith('.xls') ||
        file.name.endsWith('.csv') ||
        file.name.endsWith('.pdf') ||
        file.type.startsWith('image/'),
    );

    if (validFiles.length !== files.length) {
      console.log('Chỉ hỗ trợ tệp Excel, CSV, PDF và hình ảnh');
      return;
    }

    setSelectedFiles(validFiles);
    onFileUpload(validFiles);

    console.log(`Đã tải lên ${validFiles.length} tệp cho phiên này`);

    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  const removeFile = (index: number) => {
    const newFiles = selectedFiles.filter((_, i) => i !== index);
    setSelectedFiles(newFiles);
    onFileUpload(newFiles);
  };

  return (
    <TooltipProvider>
      <div className='relative'>
        <input
          ref={fileInputRef}
          type='file'
          multiple
          accept='.xlsx,.xls,.csv,.pdf,image/*'
          onChange={handleFileSelect}
          className='hidden'
        />
        <Tooltip>
          <TooltipTrigger asChild>
            <Button
              variant='ghost'
              size='sm'
              onClick={() => fileInputRef.current?.click()}
              className='h-8 w-8 p-0 text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200'
            >
              <FileText className='h-4 w-4' />
            </Button>
          </TooltipTrigger>
          <TooltipContent>
            <p>Tải lên cơ sở kiến thức</p>
          </TooltipContent>
        </Tooltip>

        {selectedFiles.length > 0 && (
          <div className='absolute bottom-full left-0 mb-2 min-w-48 rounded-lg border border-gray-200 bg-white p-2 shadow-md dark:border-gray-700 dark:bg-gray-800'>
            <div className='mb-1 text-xs font-medium text-gray-600 dark:text-gray-300'>
              Tệp trong phiên:
            </div>
            {selectedFiles.map((file, index) => (
              <div
                key={index}
                className='flex items-center justify-between py-1'
              >
                <span className='max-w-32 truncate text-xs text-gray-700 dark:text-gray-300'>
                  {file.name}
                </span>
                <Button
                  variant='ghost'
                  size='sm'
                  onClick={() => removeFile(index)}
                  className='h-4 w-4 p-0 text-gray-500 hover:text-red-500'
                >
                  <X className='h-3 w-3' />
                </Button>
              </div>
            ))}
          </div>
        )}
      </div>
    </TooltipProvider>
  );
};

export default SessionUpload;
