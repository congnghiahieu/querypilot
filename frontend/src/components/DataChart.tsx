import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import {
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
  Tooltip as UITooltip,
} from '@/components/ui/tooltip';
import { Check, Code, Copy, Download, File, FileSpreadsheet, FileText } from 'lucide-react';
import { useState } from 'react';
import {
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Legend,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from 'recharts';

interface DataChartProps {
  data: any[];
  title: string;
  xAxisKey: string;
  yAxisKey: string;
  type?: 'bar' | 'line' | 'pie';
  sqlQuery?: string;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const DataChart = ({ data, title, xAxisKey, yAxisKey, type = 'bar', sqlQuery }: DataChartProps) => {
  const [showSQL, setShowSQL] = useState(false);
  const [copied, setCopied] = useState(false);

  const downloadChart = (format: 'csv' | 'excel' | 'pdf') => {
    console.log(`Đang tải dữ liệu định dạng ${format}`);
    const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `chart-data.${format === 'excel' ? 'xlsx' : format}`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const copyToClipboard = (text: string) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
    console.log('SQL đã được sao chép');
  };

  const renderChart = () => {
    const commonProps = {
      height: 400,
      data,
    };

    switch (type) {
      case 'line':
        return (
          <LineChart {...commonProps}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e0e0e0' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e0e0e0' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#333' }}
              formatter={(value, name) => {
                const translations: { [key: string]: string } = {
                  amount: 'Số tiền',
                  count: 'Số lượng',
                  total: 'Tổng cộng',
                  value: 'Giá trị',
                  percentage: 'Phần trăm',
                  revenue: 'Doanh thu',
                  profit: 'Lợi nhuận',
                  growth: 'Tăng trưởng',
                  deposits: 'Tiền gửi',
                  casa: 'CASA',
                };
                const translatedName = translations[name?.toString().toLowerCase() || ''] || name;
                return [value, translatedName];
              }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
              }}
              formatter={(value) => {
                const translations: { [key: string]: string } = {
                  amount: 'Số tiền',
                  count: 'Số lượng',
                  total: 'Tổng cộng',
                  value: 'Giá trị',
                  percentage: 'Phần trăm',
                  revenue: 'Doanh thu',
                  profit: 'Lợi nhuận',
                  growth: 'Tăng trưởng',
                  deposits: 'Tiền gửi',
                  casa: 'CASA',
                };
                return translations[value.toLowerCase()] || value;
              }}
            />
            <Line
              type='monotone'
              dataKey={yAxisKey}
              stroke='#2563eb'
              strokeWidth={2}
              dot={{ fill: '#2563eb', r: 4 }}
            />
          </LineChart>
        );

      case 'pie':
        return (
          <PieChart {...commonProps}>
            <Pie
              data={data}
              cx='50%'
              cy='50%'
              outerRadius={150}
              fill='#8884d8'
              dataKey={yAxisKey}
              label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
            >
              {data.map((entry, index) => (
                <Cell
                  key={`cell-${index}`}
                  fill={COLORS[index % COLORS.length]}
                />
              ))}
            </Pie>
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
              }}
              formatter={(value, name) => {
                const translations: { [key: string]: string } = {
                  amount: 'Số tiền',
                  count: 'Số lượng',
                  total: 'Tổng cộng',
                  value: 'Giá trị',
                  percentage: 'Phần trăm',
                  revenue: 'Doanh thu',
                  profit: 'Lợi nhuận',
                };
                const translatedName = translations[name?.toString().toLowerCase() || ''] || name;
                return [value, translatedName];
              }}
            />
          </PieChart>
        );

      default:
        return (
          <BarChart {...commonProps}>
            <CartesianGrid strokeDasharray='3 3' />
            <XAxis
              dataKey={xAxisKey}
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e0e0e0' }}
            />
            <YAxis
              tick={{ fontSize: 12 }}
              axisLine={{ stroke: '#e0e0e0' }}
            />
            <Tooltip
              contentStyle={{
                backgroundColor: '#fff',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
              }}
              labelStyle={{ color: '#333' }}
              formatter={(value, name) => {
                const translations: { [key: string]: string } = {
                  amount: 'Số tiền',
                  count: 'Số lượng',
                  total: 'Tổng cộng',
                  value: 'Giá trị',
                  percentage: 'Phần trăm',
                  revenue: 'Doanh thu',
                  profit: 'Lợi nhuận',
                };
                const translatedName = translations[name?.toString().toLowerCase() || ''] || name;
                return [value, translatedName];
              }}
            />
            <Legend
              wrapperStyle={{
                paddingTop: '20px',
              }}
              formatter={(value) => {
                const translations: { [key: string]: string } = {
                  amount: 'Số tiền',
                  count: 'Số lượng',
                  total: 'Tổng cộng',
                  value: 'Giá trị',
                  percentage: 'Phần trăm',
                  revenue: 'Doanh thu',
                  profit: 'Lợi nhuận',
                };
                return translations[value.toLowerCase()] || value;
              }}
            />
            <Bar
              dataKey={yAxisKey}
              fill='#2563eb'
              radius={[4, 4, 0, 0]}
            />
          </BarChart>
        );
    }
  };

  return (
    <div className='space-y-4'>
      <div className='flex items-center justify-between'>
        <h3 className='text-lg font-semibold text-gray-900 dark:text-gray-100'>{title}</h3>
        <div className='flex items-center gap-2'>
          {sqlQuery && (
            <TooltipProvider>
              <UITooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant='ghost'
                    size='sm'
                    onClick={() => setShowSQL(!showSQL)}
                    className='h-8 w-8 p-0'
                  >
                    <Code className='h-4 w-4' />
                  </Button>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{showSQL ? 'Ẩn SQL' : 'Hiển thị SQL'}</p>
                </TooltipContent>
              </UITooltip>
            </TooltipProvider>
          )}
          <TooltipProvider>
            <UITooltip>
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
                    <DropdownMenuItem onClick={() => downloadChart('csv')}>
                      <File className='mr-2 h-4 w-4' />
                      CSV
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => downloadChart('excel')}>
                      <FileSpreadsheet className='mr-2 h-4 w-4' />
                      Excel
                    </DropdownMenuItem>
                    <DropdownMenuItem onClick={() => downloadChart('pdf')}>
                      <FileText className='mr-2 h-4 w-4' />
                      PDF
                    </DropdownMenuItem>
                  </DropdownMenuContent>
                </DropdownMenu>
              </TooltipTrigger>
              <TooltipContent>
                <p>Tải xuống dữ liệu</p>
              </TooltipContent>
            </UITooltip>
          </TooltipProvider>
        </div>
      </div>

      {showSQL && sqlQuery && (
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
        <Card>
          <CardContent className='p-6'>
            <ResponsiveContainer
              width='100%'
              height={400}
            >
              {renderChart()}
            </ResponsiveContainer>
          </CardContent>
        </Card>
      </div>
    </div>
  );
};

export default DataChart;
