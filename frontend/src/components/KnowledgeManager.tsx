import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import { Database, Download, FileImage, FileSpreadsheet, FileText, Trash2 } from 'lucide-react';
import { useState } from 'react';

import KnowledgeUpload from './KnowledgeUpload';

interface KnowledgeItem {
  id: string;
  name: string;
  type: 'excel' | 'pdf' | 'csv' | 'image' | 'text';
  size: string;
  uploadDate: string;
  insight: string;
  description?: string;
  formula?: string;
}

const KnowledgeManager = () => {
  const [knowledge, setKnowledge] = useState<KnowledgeItem[]>([
    {
      id: '1',
      name: 'Định nghĩa chỉ tiêu tín dụng.xlsx',
      type: 'excel',
      size: '2.1 MB',
      uploadDate: '2024-12-20',
      insight:
        'Tài liệu chứa định nghĩa về 47 chỉ tiêu tín dụng quan trọng, bao gồm dư nợ tín dụng, tỷ lệ nợ xấu, CAR ratio, và các công thức tính toán liên quan. Đặc biệt có phân loại theo Basel III và quy định của NHNN.',
    },
    {
      id: '2',
      name: 'Quy trình phê duyệt tín dụng.pdf',
      type: 'pdf',
      size: '1.8 MB',
      uploadDate: '2024-12-19',
      insight:
        'Tài liệu mô tả chi tiết quy trình phê duyệt tín dụng 7 bước, từ tiếp nhận hồ sơ đến giải ngân. Bao gồm thẩm quyền phê duyệt theo từng cấp và các điều kiện đặc biệt cho khách hàng ưu tiên.',
    },
    {
      id: '3',
      name: 'Danh sách mã sản phẩm.csv',
      type: 'csv',
      size: '156 KB',
      uploadDate: '2024-12-18',
      insight:
        'Danh sách 234 mã sản phẩm ngân hàng được phân loại theo 12 nhóm chính: Tiền gửi, Tín dụng, Thẻ, Bảo hiểm, Đầu tư, FX, v.v. Mỗi mã có mô tả chi tiết và điều kiện áp dụng.',
    },
    {
      id: '4',
      name: 'Dự phòng rủi ro tín dụng',
      type: 'text',
      size: '2 KB',
      uploadDate: '2024-12-17',
      insight:
        'Định nghĩa về dự phòng rủi ro tín dụng và công thức tính toán dựa trên phân loại nợ theo Thông tư 02/2019/TT-NHNN.',
      description:
        'Dự phòng rủi ro tín dụng là khoản tiền mà ngân hàng phải trích lập để bù đắp cho các khoản tổn thất có thể phát sinh từ hoạt động tín dụng.',
      formula:
        'Dự phòng = Dư nợ × Tỷ lệ trích lập theo nhóm nợ (Nhóm 1: 0%, Nhóm 2: 5%, Nhóm 3: 20%, Nhóm 4: 50%, Nhóm 5: 100%)',
    },
  ]);

  const [isUploadOpen, setIsUploadOpen] = useState(false);

  const getTypeIcon = (type: string) => {
    switch (type) {
      case 'excel':
        return <FileSpreadsheet className='h-4 w-4' />;
      case 'pdf':
        return <FileText className='h-4 w-4' />;
      case 'csv':
        return <Database className='h-4 w-4' />;
      case 'image':
        return <FileImage className='h-4 w-4' />;
      case 'text':
        return <FileText className='h-4 w-4' />;
      default:
        return <FileText className='h-4 w-4' />;
    }
  };

  const getTypeBadge = (type: string) => {
    const colors = {
      excel: 'bg-green-100 text-green-800 hover:bg-green-200 dark:bg-green-900 dark:text-green-200',
      pdf: 'bg-red-100 text-red-800 hover:bg-red-200 dark:bg-red-900 dark:text-red-200',
      csv: 'bg-blue-100 text-blue-800 hover:bg-blue-200 dark:bg-blue-900 dark:text-blue-200',
      image:
        'bg-purple-100 text-purple-800 hover:bg-purple-200 dark:bg-purple-900 dark:text-purple-200',
      text: 'bg-gray-100 text-gray-800 hover:bg-gray-200 dark:bg-gray-900 dark:text-gray-200',
    };

    return colors[type as keyof typeof colors] || colors.text;
  };

  const handleDownload = (item: KnowledgeItem) => {
    console.log(`Đang tải xuống: ${item.name}`);

    // Create sample content based on item type
    let content = '';
    let mimeType = '';
    let fileName = item.name;

    switch (item.type) {
      case 'excel':
        content = 'Sample Excel content for ' + item.name;
        mimeType = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet';
        break;
      case 'pdf':
        content = 'Sample PDF content for ' + item.name;
        mimeType = 'application/pdf';
        break;
      case 'csv':
        content = 'Column1,Column2,Column3\nData1,Data2,Data3\nData4,Data5,Data6';
        mimeType = 'text/csv';
        break;
      default:
        content = item.description || item.insight;
        mimeType = 'text/plain';
        fileName = item.name + '.txt';
    }

    const blob = new Blob([content], { type: mimeType });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleDelete = (item: KnowledgeItem) => {
    console.log(`Đang xóa: ${item.name}`);
    setKnowledge((prev) => prev.filter((k) => k.id !== item.id));
  };

  return (
    <div className='space-y-6'>
      <div className='flex items-center justify-between'>
        <div>
          <h3 className='text-lg font-semibold text-gray-900 dark:text-gray-100'>
            Cơ sở kiến thức đã tải lên
          </h3>
          <p className='text-sm text-gray-600 dark:text-gray-400'>
            Quản lý tất cả tài liệu và định nghĩa đã được tải lên hệ thống
          </p>
        </div>
        <Dialog
          open={isUploadOpen}
          onOpenChange={setIsUploadOpen}
        >
          <DialogTrigger asChild>
            <Button className='bg-blue-600 text-white hover:bg-blue-700 dark:text-white'>
              Tải lên kiến thức mới
            </Button>
          </DialogTrigger>
          <DialogContent className='max-h-[80vh] max-w-4xl overflow-y-auto border-gray-200 bg-white dark:border-gray-700 dark:bg-gray-900'>
            <DialogHeader>
              <DialogTitle className='text-gray-900 dark:text-gray-100'>
                Tải lên kiến thức mới
              </DialogTitle>
            </DialogHeader>
            <KnowledgeUpload />
          </DialogContent>
        </Dialog>
      </div>

      <div className='grid gap-4'>
        {knowledge.map((item) => (
          <div
            key={item.id}
            className='rounded-lg border border-gray-200 bg-white p-4 shadow-sm transition-shadow hover:shadow-md dark:border-gray-700 dark:bg-gray-800'
          >
            <div className='flex items-start justify-between'>
              <div className='flex flex-1 items-start gap-3'>
                <div className='flex h-10 w-10 items-center justify-center rounded-lg bg-gray-100 dark:bg-gray-700'>
                  {getTypeIcon(item.type)}
                </div>

                <div className='min-w-0 flex-1'>
                  <div className='mb-2 flex items-center gap-2'>
                    <h4 className='truncate font-medium text-gray-900 dark:text-gray-100'>
                      {item.name}
                    </h4>
                    <Badge className={getTypeBadge(item.type)}>{item.type.toUpperCase()}</Badge>
                  </div>

                  <div className='mb-2 text-sm text-gray-500 dark:text-gray-400'>
                    {item.size} • {item.uploadDate}
                  </div>

                  {item.description && (
                    <div className='mb-2 rounded-lg border-l-4 border-blue-400 bg-blue-50 p-3 dark:bg-blue-900/20'>
                      <div className='text-sm text-gray-700 dark:text-gray-300'>
                        <strong>Định nghĩa:</strong> {item.description}
                      </div>
                      {item.formula && (
                        <div className='mt-2 text-sm text-gray-700 dark:text-gray-300'>
                          <strong>Công thức:</strong> {item.formula}
                        </div>
                      )}
                    </div>
                  )}

                  <div className='rounded-lg border-l-4 border-blue-400 bg-blue-50 p-3 dark:bg-blue-900/20'>
                    <div className='flex items-start gap-2'>
                      <div className='mt-0.5 h-4 w-4 flex-shrink-0 rounded-full bg-blue-600'></div>
                      <div>
                        <div className='mb-1 text-sm font-medium text-blue-900 dark:text-blue-100'>
                          AI phân tích được:
                        </div>
                        <div className='text-sm leading-relaxed text-blue-800 dark:text-blue-200'>
                          {item.insight}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>

              <div className='ml-4 flex gap-2'>
                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() => handleDownload(item)}
                        className='h-8 w-8 p-0'
                      >
                        <Download className='h-4 w-4' />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Tải xuống tài liệu</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>

                <TooltipProvider>
                  <Tooltip>
                    <TooltipTrigger asChild>
                      <Button
                        variant='ghost'
                        size='sm'
                        onClick={() => handleDelete(item)}
                        className='h-8 w-8 p-0 text-red-600 hover:bg-red-50 hover:text-red-700 dark:text-red-400 dark:hover:bg-red-900/20'
                      >
                        <Trash2 className='h-4 w-4' />
                      </Button>
                    </TooltipTrigger>
                    <TooltipContent>
                      <p>Xóa tài liệu</p>
                    </TooltipContent>
                  </Tooltip>
                </TooltipProvider>
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default KnowledgeManager;
