import ChatHeader from '@/components/ChatHeader';
import ChatInput from '@/components/ChatInput';
import MessageList from '@/components/MessageList';
import Sidebar from '@/components/Sidebar';
import { NEW_CHAT_EVENT_NAME } from '@/lib/constants';
import { useEffect, useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';

type Message = {
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
};

// Enhanced mock chat sessions with comprehensive data
const mockChatSessions: Record<string, Message[]> = {
  chat1: [
    { role: 'user', content: 'Cho tôi xem top 10 khách hàng có số dư cao nhất' },
    {
      role: 'assistant',
      content:
        'Tôi sẽ truy vấn dữ liệu để tìm 10 khách hàng có số dư tiền gửi VND cao nhất trong hệ thống.',
      data: {
        type: 'table',
        tableData: {
          data: Array.from({ length: 150 }, (_, i) => ({
            STT: i + 1,
            CIF: `KH${String(i + 1).padStart(3, '0')}`,
            'Tên khách hàng': `Khách hàng ${i + 1}`,
            'Số dư (VND)': `${(15500000000 - i * 100000000).toLocaleString()}`,
            'Chi nhánh': ['Hà Nội', 'TP.HCM', 'Đà Nẵng', 'Cần Thơ', 'Hải Phòng'][i % 5],
          })),
          columns: ['STT', 'CIF', 'Tên khách hàng', 'Số dư (VND)', 'Chi nhánh'],
          title: 'Danh sách khách hàng có số dư cao nhất',
          sqlQuery:
            'SELECT TOP 150 cif, customer_name, balance_vnd, branch FROM customer_deposits ORDER BY balance_vnd DESC',
        },
      },
    },
  ],
  chat2: [
    { role: 'user', content: 'Báo cáo tăng trưởng CASA' },
    {
      role: 'assistant',
      content:
        'Dưới đây là báo cáo tăng trưởng CASA (Current Account Saving Account) trong 6 tháng qua:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { month: 'T7', growth: 12.5, amount: 1250 },
            { month: 'T8', growth: 15.2, amount: 1440 },
            { month: 'T9', growth: 18.7, amount: 1710 },
            { month: 'T10', growth: 16.3, amount: 1988 },
            { month: 'T11', growth: 19.8, amount: 2381 },
            { month: 'T12', growth: 22.1, amount: 2907 },
          ],
          title: 'Tăng trưởng CASA theo tháng (%)',
          xAxisKey: 'month',
          yAxisKey: 'growth',
          type: 'line' as const,
          sqlQuery:
            'SELECT DATE_FORMAT(date, "%m") as month, growth_rate as growth, total_amount as amount FROM casa_growth WHERE date >= DATE_SUB(NOW(), INTERVAL 6 MONTH) ORDER BY date',
        },
      },
    },
    { role: 'user', content: 'Phân tích chi tiết hơn về xu hướng này' },
    {
      role: 'assistant',
      content:
        '**Phân tích xu hướng tăng trưởng CASA:**\n\n• **Tăng trưởng ổn định**: Tỷ lệ tăng trưởng duy trì ở mức 12-22% qua các tháng\n• **Đỉnh cao tháng 12**: Đạt 22.1% do chiến dịch khuyến mãi cuối năm\n• **Dự báo**: Xu hướng tích cực sẽ tiếp tục trong Q1/2025\n• **Khuyến nghị**: Tập trung vào khách hàng SME để đẩy mạnh tăng trưởng',
    },
  ],
  chat3: [
    { role: 'user', content: 'Phân tích dư nợ tín dụng theo chi nhánh' },
    {
      role: 'assistant',
      content: 'Tôi sẽ phân tích dư nợ tín dụng của các chi nhánh để đưa ra báo cáo tổng quan.',
    },
    { role: 'user', content: 'Cho tôi xem dạng bảng trước' },
    {
      role: 'assistant',
      content: 'Đây là báo cáo dư nợ tín dụng chi tiết theo từng chi nhánh:',
      data: {
        type: 'table',
        tableData: {
          data: [
            {
              'Chi nhánh': 'Hà Nội',
              'Dư nợ (tỷ VND)': '850.5',
              'Số KH': '1,250',
              'Tỷ lệ nợ xấu (%)': '1.2',
            },
            {
              'Chi nhánh': 'TP.HCM',
              'Dư nợ (tỷ VND)': '1,120.8',
              'Số KH': '1,680',
              'Tỷ lệ nợ xấu (%)': '0.8',
            },
            {
              'Chi nhánh': 'Đà Nẵng',
              'Dư nợ (tỷ VND)': '420.3',
              'Số KH': '580',
              'Tỷ lệ nợ xấu (%)': '1.5',
            },
            {
              'Chi nhánh': 'Cần Thơ',
              'Dư nợ (tỷ VND)': '380.2',
              'Số KH': '520',
              'Tỷ lệ nợ xấu (%)': '2.1',
            },
          ],
          columns: ['Chi nhánh', 'Dư nợ (tỷ VND)', 'Số KH', 'Tỷ lệ nợ xấu (%)'],
          title: 'Báo cáo dư nợ tín dụng theo chi nhánh',
          sqlQuery:
            'SELECT branch, SUM(credit_balance) as total_credit, COUNT(customer_id) as customer_count, AVG(npl_ratio) as avg_npl FROM credit_portfolio GROUP BY branch ORDER BY total_credit DESC',
        },
      },
    },
    { role: 'user', content: 'Bây giờ cho tôi xem dạng biểu đồ' },
    {
      role: 'assistant',
      content: 'Đây là biểu đồ trực quan hóa dư nợ tín dụng theo chi nhánh:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { branch: 'TP.HCM', amount: 1120.8 },
            { branch: 'Hà Nội', amount: 850.5 },
            { branch: 'Đà Nẵng', amount: 420.3 },
            { branch: 'Cần Thơ', amount: 380.2 },
          ],
          title: 'Dư nợ tín dụng theo chi nhánh (tỷ VND)',
          xAxisKey: 'branch',
          yAxisKey: 'amount',
          type: 'bar' as const,
          sqlQuery:
            'SELECT branch, SUM(credit_balance/1000000000) as amount FROM credit_portfolio GROUP BY branch ORDER BY amount DESC',
        },
      },
    },
    { role: 'user', content: 'Chi nhánh nào có hiệu quả tốt nhất?' },
    {
      role: 'assistant',
      content:
        'Dựa trên phân tích dữ liệu:\n\n**Chi nhánh TP.HCM** có hiệu quả tốt nhất với:\n• Dư nợ cao nhất: 1,120.8 tỷ VND\n• Tỷ lệ nợ xấu thấp: chỉ 0.8%\n• Số lượng khách hàng đông: 1,680 KH\n\n**Chi nhánh Hà Nội** đứng thứ 2 với dư nợ 850.5 tỷ VND và tỷ lệ nợ xấu 1.2%.\n\n**Khuyến nghị**: Cần tăng cường hỗ trợ cho chi nhánh Cần Thơ do tỷ lệ nợ xấu cao (2.1%).',
    },
  ],
  chat4: [
    { role: 'user', content: 'Thống kê khách hàng mới' },
    {
      role: 'assistant',
      content: 'Đây là thống kê khách hàng mới trong 6 tháng qua:',
      data: {
        type: 'table',
        tableData: {
          data: [
            {
              Tháng: 'Tháng 7',
              'Khách hàng mới': '1,240',
              'Cá nhân': '980',
              'Doanh nghiệp': '260',
              'Tỷ lệ tăng trưởng': '8.5%',
            },
            {
              Tháng: 'Tháng 8',
              'Khách hàng mới': '1,356',
              'Cá nhân': '1,100',
              'Doanh nghiệp': '256',
              'Tỷ lệ tăng trưởng': '9.3%',
            },
            {
              Tháng: 'Tháng 9',
              'Khách hàng mới': '1,489',
              'Cá nhân': '1,205',
              'Doanh nghiệp': '284',
              'Tỷ lệ tăng trưởng': '9.8%',
            },
            {
              Tháng: 'Tháng 10',
              'Khách hàng mới': '1,567',
              'Cá nhân': '1,278',
              'Doanh nghiệp': '289',
              'Tỷ lệ tăng trưởng': '5.2%',
            },
            {
              Tháng: 'Tháng 11',
              'Khách hàng mới': '1,723',
              'Cá nhân': '1,389',
              'Doanh nghiệp': '334',
              'Tỷ lệ tăng trưởng': '10.0%',
            },
            {
              Tháng: 'Tháng 12',
              'Khách hàng mới': '1,892',
              'Cá nhân': '1,501',
              'Doanh nghiệp': '391',
              'Tỷ lệ tăng trưởng': '9.8%',
            },
          ],
          columns: ['Tháng', 'Khách hàng mới', 'Cá nhân', 'Doanh nghiệp', 'Tỷ lệ tăng trưởng'],
          title: 'Thống kê khách hàng mới theo tháng',
          sqlQuery:
            'SELECT MONTH(created_date) as month, COUNT(*) as new_customers, SUM(CASE WHEN customer_type = "Individual" THEN 1 ELSE 0 END) as individual, SUM(CASE WHEN customer_type = "Corporate" THEN 1 ELSE 0 END) as corporate FROM customers WHERE created_date >= DATEADD(month, -6, GETDATE()) GROUP BY MONTH(created_date)',
        },
      },
    },
    { role: 'user', content: 'Vẽ biểu đồ xu hướng tăng trưởng' },
    {
      role: 'assistant',
      content: 'Biểu đồ xu hướng tăng trưởng khách hàng mới:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { month: 'T7', total: 1240, individual: 980, corporate: 260 },
            { month: 'T8', total: 1356, individual: 1100, corporate: 256 },
            { month: 'T9', total: 1489, individual: 1205, corporate: 284 },
            { month: 'T10', total: 1567, individual: 1278, corporate: 289 },
            { month: 'T11', total: 1723, individual: 1389, corporate: 334 },
            { month: 'T12', total: 1892, individual: 1501, corporate: 391 },
          ],
          title: 'Xu hướng khách hàng mới',
          xAxisKey: 'month',
          yAxisKey: 'total',
          type: 'line' as const,
          sqlQuery:
            'SELECT DATE_FORMAT(created_date, "%m") as month, COUNT(*) as total, SUM(CASE WHEN type="individual" THEN 1 ELSE 0 END) as individual, SUM(CASE WHEN type="corporate" THEN 1 ELSE 0 END) as corporate FROM customers WHERE created_date >= DATE_SUB(NOW(), INTERVAL 6 MONTH) GROUP BY month ORDER BY month',
        },
      },
    },
  ],
  chat5: [
    { role: 'user', content: 'So sánh hiệu suất kinh doanh' },
    {
      role: 'assistant',
      content: 'Đây là báo cáo so sánh hiệu suất kinh doanh giữa các chi nhánh trong Q4/2024:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { branch: 'TP.HCM', revenue: 45.2, profit: 12.8, roi: 28.3 },
            { branch: 'Hà Nội', revenue: 38.7, profit: 10.5, roi: 27.1 },
            { branch: 'Đà Nẵng', revenue: 23.1, profit: 6.2, roi: 26.8 },
            { branch: 'Cần Thơ', revenue: 19.4, profit: 4.9, roi: 25.3 },
            { branch: 'Hải Phòng', revenue: 16.8, profit: 4.1, roi: 24.4 },
          ],
          title: 'So sánh doanh thu theo chi nhánh (tỷ VND)',
          xAxisKey: 'branch',
          yAxisKey: 'revenue',
          type: 'bar' as const,
          sqlQuery:
            'SELECT branch, SUM(revenue/1000000000) as revenue, SUM(profit/1000000000) as profit, AVG(roi_percentage) as roi FROM business_performance WHERE quarter = "Q4" AND year = 2024 GROUP BY branch ORDER BY revenue DESC',
        },
      },
    },
    { role: 'user', content: 'Phân tích chi tiết về ROI' },
    {
      role: 'assistant',
      content:
        '**Phân tích ROI (Return on Investment):**\n\n• **TP.HCM**: 28.3% - Dẫn đầu về hiệu quả đầu tư\n• **Hà Nội**: 27.1% - Ổn định, tiềm năng tăng trưởng cao\n• **Đà Nẵng**: 26.8% - Hiệu quả tốt với thị trường quy mô vừa\n• **Cần Thơ**: 25.3% - Cần cải thiện chiến lược đầu tư\n• **Hải Phòng**: 24.4% - Cần xem xét lại mô hình kinh doanh',
    },
  ],
  chat6: [
    { role: 'user', content: 'Báo cáo rủi ro tín dụng' },
    {
      role: 'assistant',
      content: 'Tôi sẽ phân tích báo cáo rủi ro tín dụng toàn hành để đánh giá tình hình hiện tại.',
      data: {
        type: 'table',
        tableData: {
          data: [
            {
              'Nhóm nợ': 'Nhóm 1 (Đủ tiêu chuẩn)',
              'Dư nợ (tỷ VND)': '2,850.5',
              'Tỷ lệ (%)': '85.2',
              'Dự phòng (%)': '0.0',
            },
            {
              'Nhóm nợ': 'Nhóm 2 (Cần chú ý)',
              'Dư nợ (tỷ VND)': '320.8',
              'Tỷ lệ (%)': '9.6',
              'Dự phòng (%)': '5.0',
            },
            {
              'Nhóm nợ': 'Nhóm 3 (Dưới tiêu chuẩn)',
              'Dư nợ (tỷ VND)': '105.3',
              'Tỷ lệ (%)': '3.1',
              'Dự phòng (%)': '20.0',
            },
            {
              'Nhóm nợ': 'Nhóm 4 (Nghi ngờ)',
              'Dư nợ (tỷ VND)': '45.2',
              'Tỷ lệ (%)': '1.4',
              'Dự phòng (%)': '50.0',
            },
            {
              'Nhóm nợ': 'Nhóm 5 (Có khả năng mất vốn)',
              'Dư nợ (tỷ VND)': '23.4',
              'Tỷ lệ (%)': '0.7',
              'Dự phòng (%)': '100.0',
            },
          ],
          columns: ['Nhóm nợ', 'Dư nợ (tỷ VND)', 'Tỷ lệ (%)', 'Dự phòng (%)'],
          title: 'Phân loại nợ theo nhóm rủi ro',
          sqlQuery:
            'SELECT debt_group, SUM(outstanding_balance/1000000000) as balance, (COUNT(*)*100.0/(SELECT COUNT(*) FROM credit_loans)) as percentage, provision_rate FROM credit_risk_classification GROUP BY debt_group, provision_rate ORDER BY debt_group',
        },
      },
    },
  ],
  chat7: [
    { role: 'user', content: 'Dashboard tổng quan ngân hàng' },
    {
      role: 'assistant',
      content:
        'Đây là dashboard tổng quan về hoạt động kinh doanh của ngân hàng trong tháng hiện tại:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { metric: 'Tổng tài sản', value: 485.2, target: 500.0 },
            { metric: 'Huy động vốn', value: 380.5, target: 400.0 },
            { metric: 'Dư nợ tín dụng', value: 295.8, target: 320.0 },
            { metric: 'Lợi nhuận', value: 45.2, target: 50.0 },
          ],
          title: 'Các chỉ số kinh doanh chính (nghìn tỷ VND)',
          xAxisKey: 'metric',
          yAxisKey: 'value',
          type: 'bar' as const,
          sqlQuery:
            'SELECT kpi_name as metric, current_value/1000000000000 as value, target_value/1000000000000 as target FROM bank_kpi_dashboard WHERE report_month = MONTH(NOW()) AND report_year = YEAR(NOW())',
        },
      },
    },
    { role: 'user', content: 'Chi tiết về tăng trưởng từng mảng' },
    {
      role: 'assistant',
      content:
        '**Phân tích tăng trưởng theo mảng kinh doanh:**\n\n• **Huy động vốn**: Đạt 95.1% kế hoạch, tăng 12.5% so với cùng kỳ\n• **Tín dụng**: Đạt 92.4% kế hoạch, tăng trưởng ổn định 8.2%\n• **Dịch vụ ngân hàng**: Thu nhập phi lãi tăng 15.8%\n• **Quản lý rủi ro**: NPL ratio duy trì ở mức 1.2%, trong tầm kiểm soát',
    },
  ],
  chat8: [
    { role: 'user', content: 'Phân tích xu hướng tiền gửi' },
    {
      role: 'assistant',
      content: 'Phân tích xu hướng tiền gửi khách hàng trong 12 tháng qua:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { month: 'T1', deposits: 285.5, casa: 180.2, term: 105.3 },
            { month: 'T2', deposits: 292.1, casa: 185.8, term: 106.3 },
            { month: 'T3', deposits: 298.7, casa: 190.5, term: 108.2 },
            { month: 'T4', deposits: 305.2, casa: 195.8, term: 109.4 },
            { month: 'T5', deposits: 312.8, casa: 201.2, term: 111.6 },
            { month: 'T6', deposits: 318.5, casa: 206.8, term: 111.7 },
            { month: 'T7', deposits: 325.1, casa: 212.5, term: 112.6 },
            { month: 'T8', deposits: 332.8, casa: 218.9, term: 113.9 },
            { month: 'T9', deposits: 340.2, casa: 225.8, term: 114.4 },
            { month: 'T10', deposits: 348.5, casa: 232.1, term: 116.4 },
            { month: 'T11', deposits: 356.8, casa: 238.9, term: 117.9 },
            { month: 'T12', deposits: 365.2, casa: 245.8, term: 119.4 },
          ],
          title: 'Xu hướng tiền gửi theo tháng (nghìn tỷ VND)',
          xAxisKey: 'month',
          yAxisKey: 'deposits',
          type: 'line' as const,
          sqlQuery:
            'SELECT DATE_FORMAT(report_date, "%m") as month, SUM(total_deposits/1000000000000) as deposits, SUM(casa_balance/1000000000000) as casa, SUM(term_deposits/1000000000000) as term FROM deposit_trends WHERE report_date >= DATE_SUB(NOW(), INTERVAL 12 MONTH) GROUP BY month ORDER BY month',
        },
      },
    },
  ],
  chat9: [
    { role: 'user', content: 'Báo cáo chất lượng tài sản' },
    {
      role: 'assistant',
      content: 'Báo cáo đánh giá chất lượng tài sản ngân hàng theo các tiêu chí quan trọng:',
      data: {
        type: 'table',
        tableData: {
          data: [
            {
              'Chỉ tiêu': 'Tỷ lệ nợ xấu (%)',
              'Giá trị hiện tại': '1.25',
              'Mục tiêu': '< 2.0',
              'Đánh giá': 'Tốt',
            },
            {
              'Chỉ tiêu': 'Tỷ lệ dự phòng/Nợ xấu',
              'Giá trị hiện tại': '125.8',
              'Mục tiêu': '> 100',
              'Đánh giá': 'Đạt',
            },
            {
              'Chỉ tiêu': 'CAR - Tỷ lệ an toàn vốn (%)',
              'Giá trị hiện tại': '12.85',
              'Mục tiêu': '> 8.0',
              'Đánh giá': 'Tốt',
            },
            {
              'Chỉ tiêu': 'ROA - Tỷ suất sinh lời/Tổng tài sản (%)',
              'Giá trị hiện tại': '1.42',
              'Mục tiêu': '> 1.0',
              'Đánh giá': 'Tốt',
            },
            {
              'Chỉ tiêu': 'ROE - Tỷ suất sinh lời/Vốn chủ sở hữu (%)',
              'Giá trị hiện tại': '18.65',
              'Mục tiêu': '> 15.0',
              'Đánh giá': 'Xuất sắc',
            },
          ],
          columns: ['Chỉ tiêu', 'Giá trị hiện tại', 'Mục tiêu', 'Đánh giá'],
          title: 'Báo cáo chất lượng tài sản',
          sqlQuery:
            'SELECT indicator_name, current_value, target_value, CASE WHEN current_value >= target_value THEN "Đạt" ELSE "Chưa đạt" END as evaluation FROM asset_quality_indicators WHERE report_date = LAST_DAY(NOW())',
        },
      },
    },
  ],
  chat10: [
    { role: 'user', content: 'Thống kê sản phẩm dịch vụ' },
    {
      role: 'assistant',
      content: 'Thống kê hiệu quả các sản phẩm dịch vụ ngân hàng:',
      data: {
        type: 'chart',
        chartData: {
          data: [
            { product: 'Thẻ tín dụng', revenue: 85.2, customers: 125000 },
            { product: 'Tín dụng cá nhân', revenue: 245.8, customers: 45000 },
            { product: 'Tín dụng doanh nghiệp', revenue: 380.5, customers: 8500 },
            { product: 'Dịch vụ thanh toán', revenue: 65.3, customers: 850000 },
            { product: 'Bảo hiểm bancassurance', revenue: 42.1, customers: 25000 },
            { product: 'Đầu tư chứng khoán', revenue: 28.9, customers: 15000 },
          ],
          title: 'Doanh thu theo sản phẩm (tỷ VND)',
          xAxisKey: 'product',
          yAxisKey: 'revenue',
          type: 'bar' as const,
          sqlQuery:
            'SELECT product_name as product, SUM(revenue/1000000000) as revenue, COUNT(DISTINCT customer_id) as customers FROM product_performance WHERE report_month = MONTH(NOW()) GROUP BY product_name ORDER BY revenue DESC',
        },
      },
    },
  ],
  chat11: [
    { role: 'user', content: 'Phân tích khách hàng VIP' },
    {
      role: 'assistant',
      content: 'Phân tích chi tiết về nhóm khách hàng VIP và đóng góp của họ:',
      data: {
        type: 'table',
        tableData: {
          data: [
            {
              'Phân khúc': 'Diamond',
              'Số lượng KH': '125',
              'Tổng tài sản (tỷ VND)': '85.2',
              'Doanh thu đóng góp (tỷ VND)': '25.8',
              'Tỷ lệ đóng góp (%)': '18.5',
            },
            {
              'Phân khúc': 'Platinum',
              'Số lượng KH': '580',
              'Tổng tài sản (tỷ VND)': '125.6',
              'Doanh thu đóng góp (tỷ VND)': '32.4',
              'Tỷ lệ đóng góp (%)': '23.2',
            },
            {
              'Phân khúc': 'Gold',
              'Số lượng KH': '1,250',
              'Tổng tài sản (tỷ VND)': '95.8',
              'Doanh thu đóng góp (tỷ VND)': '28.9',
              'Tỷ lệ đóng góp (%)': '20.7',
            },
            {
              'Phân khúc': 'Silver',
              'Số lượng KH': '3,800',
              'Tổng tài sản (tỷ VND)': '78.5',
              'Doanh thu đóng góp (tỷ VND)': '18.2',
              'Tỷ lệ đóng góp (%)': '13.0',
            },
          ],
          columns: [
            'Phân khúc',
            'Số lượng KH',
            'Tổng tài sản (tỷ VND)',
            'Doanh thu đóng góp (tỷ VND)',
            'Tỷ lệ đóng góp (%)',
          ],
          title: 'Phân tích khách hàng VIP theo phân khúc',
          sqlQuery:
            'SELECT customer_segment, COUNT(*) as customer_count, SUM(total_assets/1000000000) as total_assets, SUM(revenue_contribution/1000000000) as revenue, (SUM(revenue_contribution)*100.0/(SELECT SUM(revenue_contribution) FROM vip_customers)) as contribution_rate FROM vip_customers GROUP BY customer_segment ORDER BY revenue DESC',
        },
      },
    },
  ],
};

const Index = () => {
  const { chatId } = useParams();
  const navigate = useNavigate();
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [currentChatId, setCurrentChatId] = useState<string | null>(chatId || null);
  const [chatTitle, setChatTitle] = useState<string>('');

  // Generate random chat ID and title
  const generateChatId = () => {
    return `chat-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  };

  const generateChatTitle = (message: string) => {
    const title = message.length > 50 ? message.substring(0, 50) + '...' : message;
    return title;
  };

  const handleSendMessage = async (
    message: string,
    options?: { search?: string; data?: string },
  ) => {
    if (!message.trim()) return;

    const userMessage: Message = { role: 'user', content: message };
    setMessages((prev) => [...prev, userMessage]);

    // Show loading state
    setIsLoading(true);
    const loadingMessage: Message = {
      role: 'assistant',
      content: '',
      isLoading: true,
    };
    setMessages((prev) => [...prev, loadingMessage]);

    // Simulate API delay
    await new Promise((resolve) => setTimeout(resolve, 2000));

    // Remove loading message and add streaming response
    setMessages((prev) => prev.slice(0, -1));

    const assistantMessage: Message = {
      role: 'assistant',
      content: 'Tôi đang xử lý yêu cầu của bạn và sẽ trả về kết quả chi tiết ngay sau đây...',
      isStreaming: true,
    };
    setMessages((prev) => [...prev, assistantMessage]);

    // Simulate streaming completion
    setTimeout(() => {
      setMessages((prev) =>
        prev.map((msg, index) =>
          index === prev.length - 1 ?
            {
              ...msg,
              isStreaming: false,
              content: 'Đây là câu trả lời chi tiết cho câu hỏi của bạn.',
            }
          : msg,
        ),
      );
      setIsLoading(false);
    }, 3000);
  };

  const loadChatSession = (selectedChatId: string) => {
    const sessionMessages = mockChatSessions[selectedChatId] || [];
    setMessages(sessionMessages);
    setCurrentChatId(selectedChatId);
    // Navigate to specific chat URL
    navigate(`/${selectedChatId}`);
  };

  const startNewChat = () => {
    // Navigate to welcome page
    navigate('/');
  };

  // Load chat data when component mounts or chatId changes
  useEffect(() => {
    if (chatId) {
      // Check if this is a new chat from localStorage
      const newChatData = localStorage.getItem(`chat-${chatId}`);
      if (newChatData) {
        const { title, initialMessage, initialOptions } = JSON.parse(newChatData);
        setChatTitle(title);
        setCurrentChatId(chatId);

        // Dispatch event to notify sidebar of new chat (in case it wasn't caught from Welcome)
        const event = new CustomEvent(NEW_CHAT_EVENT_NAME, {
          detail: { chatId, title },
        });
        window.dispatchEvent(event);

        // Clear the localStorage item after processing
        localStorage.removeItem(`chat-${chatId}`);
        // Send the initial message
        handleSendMessage(initialMessage, initialOptions);
      } else if (mockChatSessions[chatId]) {
        // Load existing chat session
        setMessages(mockChatSessions[chatId]);
        setCurrentChatId(chatId);
        // Set title from mock data or generate from first message
        const firstUserMessage = mockChatSessions[chatId].find((msg) => msg.role === 'user');
        if (firstUserMessage) {
          const title = generateChatTitle(firstUserMessage.content);
          setChatTitle(title);
        }
      } else {
        // Chat not found, redirect to welcome
        navigate('/');
      }
    } else {
      // No chatId, redirect to welcome
      navigate('/');
    }
  }, [chatId]);

  // If no chatId, this shouldn't render (will redirect to welcome)
  if (!chatId) {
    return null;
  }

  return (
    <div className='flex h-screen bg-background text-foreground transition-colors duration-300'>
      {/* Sidebar */}
      <Sidebar
        isOpen={isSidebarOpen}
        onToggle={() => setIsSidebarOpen(!isSidebarOpen)}
        onChatSelect={loadChatSession}
        onNewChat={startNewChat}
        currentChatId={currentChatId}
      />

      {/* Main content area */}
      <div
        className={`flex flex-1 flex-col transition-all duration-300 ${
          isSidebarOpen ? 'ml-64' : 'ml-16'
        }`}
      >
        {/* Fixed header */}
        <div
          className='fixed right-0 top-0 z-30 transition-all duration-300'
          style={{ left: isSidebarOpen ? '256px' : '64px' }}
        >
          <ChatHeader
            isSidebarOpen={isSidebarOpen}
            chatTitle={chatTitle}
          />
        </div>

        {/* Main chat area */}
        <div className='flex-1 pt-[60px]'>
          {/* Scrollable messages area */}
          <div className='h-full overflow-y-auto pb-[120px]'>
            <MessageList messages={messages} />
          </div>

          {/* Fixed input at bottom */}
          <div
            className='fixed bottom-0 right-0 z-20 border-t border-gray-200 bg-white/95 p-4 backdrop-blur transition-all duration-300 dark:border-gray-700 dark:bg-gray-900/95'
            style={{ left: isSidebarOpen ? '256px' : '64px' }}
          >
            <ChatInput
              onSend={handleSendMessage}
              isLoading={isLoading}
            />
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
