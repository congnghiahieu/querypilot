import { Shield, User, Building, Database, CheckCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';

interface UserPermissionsProps {
  username: string;
}

const UserPermissions = ({ username }: UserPermissionsProps) => {
  const permissions = [
    {
      id: 'role',
      label: 'Vai trò',
      icon: User,
      value: 'Nhân viên',
      color:
        'bg-blue-50 text-blue-700 border-blue-200 dark:bg-blue-900/30 dark:text-blue-300 dark:border-blue-800',
    },
    {
      id: 'branch',
      label: 'Chi nhánh',
      icon: Building,
      value: 'Hà Nội',
      color:
        'bg-green-50 text-green-700 border-green-200 dark:bg-green-900/30 dark:text-green-300 dark:border-green-800',
    },
    {
      id: 'scope',
      label: 'Phạm vi',
      icon: Shield,
      value: 'Cá nhân',
      color:
        'bg-purple-50 text-purple-700 border-purple-200 dark:bg-purple-900/30 dark:text-purple-300 dark:border-purple-800',
    },
    {
      id: 'data_access',
      label: 'Dữ liệu được phép truy cập',
      icon: Database,
      value: 'Dữ liệu cơ bản',
      color:
        'bg-emerald-50 text-emerald-700 border-emerald-200 dark:bg-emerald-900/30 dark:text-emerald-300 dark:border-emerald-800',
    },
  ];

  return (
    <div className='space-y-4'>
      <div className='text-center'>
        <div className='mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-blue-100 dark:bg-blue-900/30'>
          <User className='h-8 w-8 text-blue-600 dark:text-blue-400' />
        </div>
        <h3 className='text-lg font-semibold text-gray-900 dark:text-gray-100'>
          Quyền truy cập của {username}
        </h3>
        <p className='text-sm text-gray-600 dark:text-gray-400'>
          Thông tin về quyền hạn và phạm vi truy cập dữ liệu
        </p>
      </div>

      <div className='space-y-3'>
        {permissions.map((permission) => (
          <div
            key={permission.id}
            className='flex items-center justify-between rounded-lg border border-gray-200 p-3 dark:border-gray-700'
          >
            <div className='flex items-center gap-3'>
              <permission.icon className='h-5 w-5 text-gray-500 dark:text-gray-400' />
              <span className='font-medium text-gray-700 dark:text-gray-300'>
                {permission.label}
              </span>
            </div>
            <Badge className={`${permission.color} pointer-events-none cursor-default`}>
              {permission.value}
            </Badge>
          </div>
        ))}
      </div>

      <div className='rounded-lg border border-green-200 bg-green-50/50 p-4 dark:border-green-800/50 dark:bg-green-900/20'>
        <div className='flex items-center gap-2'>
          <CheckCircle className='h-5 w-5 text-green-600 dark:text-green-400' />
          <span className='font-medium text-green-800 dark:text-green-300'>
            Tài khoản đã được xác thực
          </span>
        </div>
        <p className='mt-2 text-sm text-green-700 dark:text-green-400'>
          Quyền truy cập đã được cấp phát và kích hoạt thành công. Bạn có thể sử dụng hệ thống với
          các quyền hạn được phân công.
        </p>
      </div>
    </div>
  );
};

export default UserPermissions;
