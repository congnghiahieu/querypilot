import { useState, useRef } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Textarea } from '@/components/ui/textarea';
import { Upload, FileSpreadsheet, Plus, Minus } from 'lucide-react';

interface KnowledgeRule {
  id: string;
  concept: string;
  definition: string;
  formula: string;
}

const KnowledgeUpload = () => {
  const [rules, setRules] = useState<KnowledgeRule[]>([]);
  const [newRule, setNewRule] = useState({ concept: '', definition: '', formula: '' });
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    if (
      !file.name.endsWith('.xlsx') &&
      !file.name.endsWith('.xls') &&
      !file.name.endsWith('.csv') &&
      !file.name.endsWith('.pdf')
    ) {
      console.log('Chỉ hỗ trợ file Excel (.xlsx, .xls), CSV và PDF');
      return;
    }

    // Simulate file processing
    console.log(`Đã tải lên file ${file.name} thành công. Đang xử lý...`);

    // In real implementation, this would parse files and extract knowledge rules
    setTimeout(() => {
      const mockRules: KnowledgeRule[] = [
        {
          id: '1',
          concept: 'Dư nợ tín dụng thông thường',
          definition: 'Tổng dư nợ tín dụng không bao gồm thẻ tín dụng',
          formula: 'dư nợ tín dụng món vay + dư nợ tín dụng thấu chi',
        },
      ];
      setRules((prev) => [...prev, ...mockRules]);
      console.log('Đã import thành công các định nghĩa từ file');
    }, 2000);
  };

  const addRule = () => {
    if (!newRule.concept || !newRule.definition) {
      console.log('Vui lòng nhập đầy đủ thông tin');
      return;
    }

    const rule: KnowledgeRule = {
      id: Date.now().toString(),
      concept: newRule.concept,
      definition: newRule.definition,
      formula: newRule.formula,
    };

    setRules((prev) => [...prev, rule]);
    setNewRule({ concept: '', definition: '', formula: '' });
    console.log('Đã thêm định nghĩa mới');
  };

  const removeRule = (id: string) => {
    setRules((prev) => prev.filter((rule) => rule.id !== id));
  };

  return (
    <div className='space-y-6'>
      <Card className='border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'>
        <CardHeader>
          <CardTitle className='flex items-center gap-2 text-gray-900 dark:text-gray-100'>
            <Upload className='h-5 w-5' />
            Thêm kiến thức
          </CardTitle>
        </CardHeader>
        <CardContent className='space-y-4'>
          <div>
            <Label className='text-gray-700 dark:text-gray-300'>Đăng tải file định nghĩa</Label>
            <div className='mt-2 flex gap-2'>
              <Input
                ref={fileInputRef}
                type='file'
                accept='.xlsx,.xls,.csv,.pdf'
                onChange={handleFileUpload}
                className='hidden'
              />
              <Button
                onClick={() => fileInputRef.current?.click()}
                variant='outline'
                className='flex-1 border-gray-300 bg-white text-gray-900 hover:bg-gray-50 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100 dark:hover:bg-gray-600'
              >
                <FileSpreadsheet className='mr-2 h-4 w-4' />
                Chọn file (Excel, CSV, PDF)
              </Button>
            </div>
            <p className='mt-1 text-sm text-gray-500 dark:text-gray-400'>
              File cần có các cột: Khái niệm, Định nghĩa, Công thức
            </p>
          </div>

          <div className='border-t border-gray-200 pt-4 dark:border-gray-600'>
            <Label className='text-gray-700 dark:text-gray-300'>
              Hoặc thêm định nghĩa thủ công
            </Label>
            <div className='mt-2 grid gap-3'>
              <Input
                placeholder='Tên khái niệm (VD: Dư nợ tín dụng thông thường)'
                value={newRule.concept}
                onChange={(e) => setNewRule((prev) => ({ ...prev, concept: e.target.value }))}
                className='border-gray-300 bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100'
              />
              <Textarea
                placeholder='Định nghĩa chi tiết'
                value={newRule.definition}
                onChange={(e) => setNewRule((prev) => ({ ...prev, definition: e.target.value }))}
                className='border-gray-300 bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100'
              />
              <Input
                placeholder='Công thức tính (tuỳ chọn)'
                value={newRule.formula}
                onChange={(e) => setNewRule((prev) => ({ ...prev, formula: e.target.value }))}
                className='border-gray-300 bg-white text-gray-900 dark:border-gray-600 dark:bg-gray-700 dark:text-gray-100'
              />
              <Button
                onClick={addRule}
                className='flex items-center gap-2 bg-blue-500 text-white hover:bg-blue-600'
              >
                <Plus className='h-4 w-4' />
                Thêm định nghĩa
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {rules.length > 0 && (
        <Card className='border-gray-200 bg-gray-50 dark:border-gray-700 dark:bg-gray-800'>
          <CardHeader>
            <CardTitle className='text-gray-900 dark:text-gray-100'>
              Danh sách định nghĩa đã có ({rules.length})
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className='space-y-3'>
              {rules.map((rule) => (
                <div
                  key={rule.id}
                  className='rounded-lg border border-gray-200 bg-white p-3 dark:border-gray-600 dark:bg-gray-700'
                >
                  <div className='flex items-start justify-between'>
                    <div className='flex-1'>
                      <h4 className='font-medium text-blue-600 dark:text-blue-400'>
                        {rule.concept}
                      </h4>
                      <p className='mt-1 text-sm text-gray-600 dark:text-gray-300'>
                        {rule.definition}
                      </p>
                      {rule.formula && (
                        <p className='mt-1 text-sm text-green-600 dark:text-green-400'>
                          <strong>Công thức:</strong> {rule.formula}
                        </p>
                      )}
                    </div>
                    <Button
                      variant='ghost'
                      size='sm'
                      onClick={() => removeRule(rule.id)}
                      className='text-red-500 hover:bg-red-50 hover:text-red-700 dark:hover:bg-red-900/20'
                    >
                      <Minus className='h-4 w-4' />
                    </Button>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
};

export default KnowledgeUpload;
