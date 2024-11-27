import { useState, useEffect } from 'react';

interface Device {
  id: string;
  espIdentifier: string;
  name: string;
  status: 'online' | 'offline';
  lastSeen: string;
  approved: boolean;
}

export default function DeviceManagement() {
  const [devices, setDevices] = useState<Device[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [editingDevice, setEditingDevice] = useState<string | null>(null);
  const [newName, setNewName] = useState('');

  useEffect(() => {
    fetchDevices();
  }, []);

  const fetchDevices = async () => {
    try {
      const response = await fetch('/api/admin/devices');
      const data = await response.json();
      if (data.success) {
        setDevices(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch devices');
    } finally {
      setLoading(false);
    }
  };

  const approveDevice = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/admin/devices/${deviceId}/approve`, {
        method: 'POST',
      });
      
      const data = await response.json();
      if (data.success) {
        setDevices(prev =>
          prev.map(device =>
            device.id === deviceId ? { ...device, approved: true } : device
          )
        );
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to approve device');
    }
  };

  const updateDeviceName = async (deviceId: string) => {
    try {
      const response = await fetch(`/api/admin/devices/${deviceId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: newName }),
      });
      
      const data = await response.json();
      if (data.success) {
        setDevices(prev =>
          prev.map(device =>
            device.id === deviceId ? { ...device, name: newName } : device
          )
        );
        setEditingDevice(null);
        setNewName('');
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to update device name');
    }
  };

  if (loading) return <div>Loading devices...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Device Management</h2>
      
      <div className="bg-white shadow-md rounded-lg overflow-hidden">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Name
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                ESP Identifier
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Status
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Last Seen
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {devices.map((device) => (
              <tr key={device.id}>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {editingDevice === device.id ? (
                    <div className="flex items-center space-x-2">
                      <input
                        type="text"
                        value={newName}
                        onChange={(e) => setNewName(e.target.value)}
                        className="border rounded px-2 py-1"
                      />
                      <button
                        onClick={() => updateDeviceName(device.id)}
                        className="text-blue-600 hover:text-blue-800"
                      >
                        Save
                      </button>
                      <button
                        onClick={() => {
                          setEditingDevice(null);
                          setNewName('');
                        }}
                        className="text-gray-600 hover:text-gray-800"
                      >
                        Cancel
                      </button>
                    </div>
                  ) : (
                    <div className="flex items-center space-x-2">
                      {device.name}
                      <button
                        onClick={() => {
                          setEditingDevice(device.id);
                          setNewName(device.name);
                        }}
                        className="text-gray-400 hover:text-gray-600"
                      >
                        ✏️
                      </button>
                    </div>
                  )}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {device.espIdentifier}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">
                  <span className={`px-2 py-1 rounded-full ${
                    device.status === 'online' 
                      ? 'bg-green-100 text-green-800' 
                      : 'bg-red-100 text-red-800'
                  }`}>
                    {device.status}
                  </span>
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {new Date(device.lastSeen).toLocaleString()}
                </td>
                <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                  {!device.approved && (
                    <button
                      onClick={() => approveDevice(device.id)}
                      className="bg-blue-500 text-white px-3 py-1 rounded-md hover:bg-blue-600"
                    >
                      Approve
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}