import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableBody,
  TableCaption,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  ArrowUpDown,
  Check,
  ChevronLeft,
  ChevronRight,
  Code,
  Copy,
  Download,
  File,
  FileSpreadsheet,
  FileText,
  Search,
} from 'lucide-react';
import { useState } from 'react';

interface DataTableProps {
  data: any[];
  columns: string[];
  title?: string;
  sqlQuery?: string;
}

const DataTable = ({ data, columns, title, sqlQuery }: DataTableProps) => {
  const [showSql, setShowSql] = useState(false);
  const [copied, setCopied] = useState(false);
  const [sortColumn, setSortColumn] = useState<string | null>(null);
  const [sortDirection, setSortDirection] = useState<'asc' | 'desc'>('asc');
  const [filterText, setFilterText] = useState('');
  const [currentPage, setCurrentPage] = useState(1);
  const itemsPerPage = 10;

  // Sort data
  const sortedData = [...data];
  if (sortColumn) {
    sortedData.sort((a, b) => {
      const aVal = a[sortColumn];
      const bVal = b[sortColumn];
      if (aVal < bVal) return sortDirection === 'asc' ? -1 : 1;
      if (aVal > bVal) return sortDirection === 'asc' ? 1 : -1;
      return 0;
    });
  }

  // Filter data
  const filteredData = sortedData.filter((row) =>
    columns.some((column) => String(row[column]).toLowerCase().includes(filterText.toLowerCase())),
  );

  // Paginate data
  const totalPages = Math.ceil(filteredData.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const paginatedData = filteredData.slice(startIndex, startIndex + itemsPerPage);

  const downloadData = (format: 'csv' | 'excel' | 'pdf') => {
    console.log(`Đang tải dữ liệu định dạng ${format}`);
    const blob = new Blob([JSON.stringify(filteredData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `data.${format === 'excel' ? 'xlsx' : format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    console.log('SQL đã được sao chép');
  };

  const handleSort = (column: string) => {
    if (sortColumn === column) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(column);
      setSortDirection('asc');
    }
  };

  // Calculate page numbers to show
  const getPageNumbers = () => {
    const pages = [];
    const maxVisiblePages = 5;

    if (totalPages <= maxVisiblePages) {
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i);
      }
    } else {
      const start = Math.max(1, currentPage - Math.floor(maxVisiblePages / 2));
      const end = Math.min(totalPages, start + maxVisiblePages - 1);

      for (let i = start; i <= end; i++) {
        pages.push(i);
      }
    }

    return pages;
  };

  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <h3 className='text-lg font-semibold text-gray-900 dark:text-gray-100'>
          {title || 'Kết quả truy vấn'}
        </h3>
        <div className='flex gap-2'>
          {sqlQuery && (
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant='ghost'
                    size='sm'
                    onClick={() => setShowSql(!showSql)}
                    className='h-8 w-8 p-0'
                  >
                    <Code className='h-4 w-4' />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{showSql ? 'Ẩn SQL' : 'Hiển thị SQL'}</p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          )}

          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button
                      variant='ghost'
                      size='sm'
                      className='h-8 w-8 p-0'
                    >
                      <Download className='h-4 w-4' />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent>
                    <DropdownMenuItem onClick={() => downloadData('csv')}>
                      <File className='mr-2 h-4 w-4' />
                      CSV
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => downloadData('excel')}>
                      <FileSpreadsheet className='mr-2 h-4 w-4' />
                      Excel
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => downloadData('pdf')}>
                      <FileText className='mr-2 h-4 w-4' />
                      PDF
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TooltipTrigger>
              <TooltipContent>
                <p>Tải xuống dữ liệu</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>
        </div>
      </div>

      {/* Search and Filter */}
      <div className='flex items-center gap-4'>
        <div className='relative max-w-sm flex-1'>
          <Search className='absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-gray-500' />
          <Input
            placeholder='Tìm kiếm trong bảng...'
            value={filterText}
            onChange={(e) => {
              setFilterText(e.target.value);
              setCurrentPage(1);
            }}
            className='pl-10'
          />
        </div>
        <div className='text-sm text-gray-500'>
          Hiển thị {startIndex + 1}-{Math.min(startIndex + itemsPerPage, filteredData.length)} /{' '}
          {filteredData.length} bản ghi
        </div>
      </div>

      {showSql && sqlQuery && (
        <div className='relative rounded-lg border border-gray-200 bg-gray-50 p-4 dark:border-gray-700 dark:bg-gray-900'>
          <div className='mb-2 flex items-center justify-between'>
            <span className='text-sm font-medium text-gray-700 dark:text-gray-300'>
              Truy vấn SQL:
            </span>
            <Button
              variant='ghost'
              size='sm'
              onClick={() => copyToClipboard(sqlQuery)}
              className='h-6 w-6 p-0'
            >
              {copied ?
                <Check className='h-3 w-3 text-green-500' />
              : <Copy className='h-3 w-3' />}
            </Button>
          </div>
          <pre className='whitespace-pre-wrap rounded border bg-white p-3 font-mono text-sm text-gray-800 dark:bg-gray-800 dark:text-gray-200'>
            {sqlQuery}
          </pre>
        </div>
      )}

      <div className='rounded-lg border border-gray-200 dark:border-gray-700'>
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((column) => (
                <TableHead
                  key={column}
                  className='cursor-pointer text-gray-900 hover:bg-gray-50 dark:text-gray-100 dark:hover:bg-gray-800'
                  onClick={() => handleSort(column)}
                >
                  <div className='flex items-center gap-2'>
                    {column}
                    <ArrowUpDown className='h-3 w-3' />
                  </div>
                </TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {paginatedData.map((row, index) => (
              <TableRow key={index}>
                {columns.map((column) => (
                  <TableCell
                    key={column}
                    className='text-gray-700 dark:text-gray-300'
                  >
                    {row[column]?.toString() || ''}
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
          <TableCaption className='text-gray-500 dark:text-gray-400'>
            Tổng cộng {filteredData.length} bản ghi
          </TableCaption>
        </Table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className='flex items-center justify-between'>
          <Button
            variant='outline'
            size='sm'
            onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
            disabled={currentPage === 1}
          >
            <ChevronLeft className='mr-1 h-4 w-4' />
            Trước
          </Button>

          <div className='flex items-center gap-2'>
            {getPageNumbers().map((page) => (
              <Button
                key={page}
                variant={currentPage === page ? 'default' : 'outline'}
                size='sm'
                onClick={() => setCurrentPage(page)}
                className='h-8 w-8 p-0'
              >
                {page}
              </Button>
            ))}
          </div>

          <Button
            variant='outline'
            size='sm'
            onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
            disabled={currentPage === totalPages}
          >
            Sau
            <ChevronRight className='ml-1 h-4 w-4' />
          </Button>
        </div>
      )}
    </div>
  );
};

export default DataTable;
