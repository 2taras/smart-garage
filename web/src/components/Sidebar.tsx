import React from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';

const Sidebar: React.FC = () => {
  const router = useRouter();
  const { user } = useAuth();

  const menuItems = [
    { id: 'garages', label: 'Garage Control', path: '/' },
    { id: 'access-logs', label: 'Access Logs', path: '/access-logs' },
    ...(user?.role === 'admin'
      ? [
          { id: 'users', label: 'Users', path: '/users' },
          { id: 'system-logs', label: 'System Logs', path: '/system-logs' },
          { id: 'devices', label: 'Devices', path: '/devices' },
        ]
      : []),
  ];

  return (
    <div className="w-64 bg-white shadow-sm">
      <div className="h-full px-3 py-4">
        <nav className="space-y-1">
          {menuItems.map((item) => (
            <a
              key={item.id}
              href={item.path}
              className={`
                flex items-center px-3 py-2 text-sm font-medium rounded-md
                ${
                  router.pathname === item.path
                    ? 'bg-gray-100 text-gray-900'
                    : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                }
              `}
            >
              {item.label}
            </a>
          ))}
        </nav>
      </div>
    </div>
  );
};

export default Sidebar;