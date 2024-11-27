// src/pages/index.tsx
import type { NextPage } from 'next';
import { useState } from 'react';
import Layout from '../components/Layout';
import GarageControl from '../components/GarageControl';
import AccessLogs from '../components/AccessLogs';
import UserManagement from '../components/UserManagement';
import SystemLogs from '../components/SystemLogs';
import DeviceManagement from '../components/DeviceManagement';
import { useAuth } from '../contexts/AuthContext';

const Home: NextPage = () => {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState('garages');

  const tabs = [
    { id: 'garages', label: 'Garage Control', component: GarageControl },
    { id: 'access-logs', label: 'Access Logs', component: AccessLogs },
    ...(user?.role === 'admin'
      ? [
          { id: 'users', label: 'Users', component: UserManagement },
          { id: 'system-logs', label: 'System Logs', component: SystemLogs },
          { id: 'devices', label: 'Devices', component: DeviceManagement },
        ]
      : []),
  ];

  const ActiveComponent = tabs.find((tab) => tab.id === activeTab)?.component;

  return (
    <Layout>
      <div className="min-h-screen bg-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900">Smart Garage Dashboard</h1>
          </div>

          <div className="border-b border-gray-200">
            <nav className="-mb-px flex space-x-8">
              {tabs.map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`
                    whitespace-nowrap py-4 px-1 border-b-2 font-medium text-sm
                    ${
                      activeTab === tab.id
                        ? 'border-blue-500 text-blue-600'
                        : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                    }
                  `}
                >
                  {tab.label}
                </button>
              ))}
            </nav>
          </div>

          <div className="mt-6">
            {ActiveComponent && <ActiveComponent />}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default Home;