// src/components/GarageControl.tsx
import { FC, useEffect, useState } from 'react';
import { Garage } from '../types';
import { useWebSocket } from '../hooks/useWebSocket';

const GarageControl: FC = () => {
  const [garages, setGarages] = useState<Garage[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isConnected, lastMessage, sendMessage } = useWebSocket();

  useEffect(() => {
    fetchGarages();
  }, []);

  useEffect(() => {
    if (lastMessage && lastMessage.type === 'status') {
      updateGarageStatus(lastMessage.data);
    }
  }, [lastMessage]);

  const fetchGarages = async () => {
    try {
      const response = await fetch('/api/garages');
      const data = await response.json();
      if (data.success) {
        setGarages(data.data);
      } else {
        setError(data.error);
      }
    } catch (err) {
      setError('Failed to fetch garages');
    } finally {
      setLoading(false);
    }
  };

  const updateGarageStatus = (update: any) => {
    setGarages(prev =>
      prev.map(garage =>
        garage.espIdentifier === update.id
          ? { ...garage, currentState: update.state }
          : garage
      )
    );
  };

  const controlGarage = async (garageId: string, action: 'open' | 'close') => {
    try {
      // Send WebSocket message
      sendMessage({
        type: 'command',
        action,
        garageId,
        timestamp: new Date().toISOString()
      });

      // Also send HTTP request for redundancy
      const response = await fetch(`/api/garages/${garageId}/control`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action }),
      });
      
      const data = await response.json();
      if (!data.success) {
        throw new Error(data.error);
      }
    } catch (err) {
      setError('Failed to control garage');
    }
  };

  if (loading) return <div>Loading garages...</div>;
  if (error) return <div className="text-red-500">Error: {error}</div>;

  return (
    <div>
      {!isConnected && (
        <div className="mb-4 p-4 bg-yellow-100 text-yellow-700 rounded-md">
          Warning: Real-time connection is currently offline. Some features may be delayed.
        </div>
      )}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {garages.map((garage) => (
          <div
            key={garage.id}
            className="bg-white rounded-lg shadow-md p-6"
          >
            <h3 className="text-lg font-medium text-gray-900">{garage.name}</h3>
            <p className="mt-2 text-sm text-gray-500">
              Status: <span className="font-medium">{garage.currentState}</span>
            </p>
            <div className="mt-4 space-x-4">
              <button
                onClick={() => controlGarage(garage.id, 'open')}
                disabled={garage.currentState === 'opening' || garage.currentState === 'open'}
                className={`
                  px-4 py-2 rounded-md text-sm font-medium
                  ${
                    garage.currentState === 'opening' || garage.currentState === 'open'
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-green-600 hover:bg-green-700 text-white'
                  }
                `}
              >
                Open
              </button>
              <button
                onClick={() => controlGarage(garage.id, 'close')}
                disabled={garage.currentState === 'closing' || garage.currentState === 'closed'}
                className={`
                  px-4 py-2 rounded-md text-sm font-medium
                  ${
                    garage.currentState === 'closing' || garage.currentState === 'closed'
                      ? 'bg-gray-300 cursor-not-allowed'
                      : 'bg-red-600 hover:bg-red-700 text-white'
                  }
                `}
              >
                Close
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};

export default GarageControl;