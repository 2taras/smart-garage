import { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import { useRouter } from 'next/router';

export default function Home() {
  const { isAuthenticated, logout } = useAuth();
  const router = useRouter();
  const [status, setStatus] = useState<any>(null);
  const [logs, setLogs] = useState<any[]>([]);
  const [isAnimating, setIsAnimating] = useState(false);

  const formatNumber = (num: number): string => {
    return Number(num).toFixed(1);
  };
  
  // Function to format state for display
  const formatState = (state: string): string => {
    if (state == null) return "";
    return state.charAt(0).toUpperCase() + state.slice(1);
  };

  const [doorHeight, setDoorHeight] = useState(100); // Track door height percentage

  const getLogs = async () => {
    try {
      const response = await fetchWithAuth('/api/logs');
      if (response) {
        const data = await response.json();
        setLogs(data);
      }
    } catch (error) {
      console.error('Error fetching logs:', error);
    }
  };

  const getStatus = async () => {
    try {
      const response = await fetchWithAuth('/api/status');
      if (response) {
        const data = await response.json();
        setStatus(data);
        
        if (!isAnimating && (data.state == "closed" || data.state == "open")) {
          setDoorState(data.state);
          setDoorHeight(data.state === 'open' ? 10 : 100);
        }
      }
    } catch (error) {
      console.error('Error fetching status:', error);
    }
  };
  
  // Update the controlGarage function:
  const controlGarage = async (action: string) => {
    if (isAnimating) return;
  
    try {
      setIsAnimating(true);
      const newState = action === 'left' ? 'opening' : 'closing';
      setDoorState(newState);
  
      const position = await new Promise<GeolocationPosition>((resolve, reject) => {
        navigator.geolocation.getCurrentPosition(resolve, reject);
      });
  
      const response = await fetchWithAuth(
        `/api/garage/${action}`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            latitude: position.coords.latitude,
            longitude: position.coords.longitude,
          }),
        }
      );
  
      if (response) {
        const targetHeight = action === 'left' ? 10 : 100;
        const startHeight = action === 'left' ? 100 : 10;
        const startTime = Date.now();
        const duration = 7000; // 7 seconds
  
        const animate = () => {
          const elapsed = Date.now() - startTime;
          const progress = Math.min(elapsed / duration, 1);
          
          const currentHeight = startHeight + (targetHeight - startHeight) * progress;
          setDoorHeight(currentHeight);
  
          if (progress < 1) {
            requestAnimationFrame(animate);
          } else {
            setDoorState(action === 'left' ? 'open' : 'closed');
            setIsAnimating(false);
          }
        };
  
        requestAnimationFrame(animate);
      } else {
        setDoorState(action === 'left' ? 'closed' : 'open');
        setDoorHeight(action === 'left' ? 100 : 10);
        setIsAnimating(false);
      }
    } catch (error) {
      console.error('Error controlling garage:', error);
      setDoorState(doorState === 'opening' ? 'closed' : 'open');
      setDoorHeight(doorState === 'opening' ? 100 : 10);
      setIsAnimating(false);
    }
  };
  
  // Update the useEffect to include dependencies and add error handling
  useEffect(() => {
    let statusInterval: NodeJS.Timeout;
    let logsInterval: NodeJS.Timeout;

    if (isAuthenticated) {
      // Initial fetch
      getStatus();
      getLogs();

      // Set up intervals
      statusInterval = setInterval(getStatus, 1000);
      logsInterval = setInterval(getLogs, 5000); // Update logs every 5 seconds
    }

    return () => {
      if (statusInterval) clearInterval(statusInterval);
      if (logsInterval) clearInterval(logsInterval);
    };
  }, [isAuthenticated, isAnimating]);
  
  // Add this type for better type safety
  type DoorState = 'open' | 'closed' | 'opening' | 'closing';
  
  // Update the state definition with the proper type
  const [doorState, setDoorState] = useState<DoorState>('closed');

  const fetchWithAuth = async (url: string, options: RequestInit = {}) => {
    const token = localStorage.getItem('token');
    const response = await fetch(url, {
      ...options,
      headers: {
        ...options.headers,
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (response.status === 401) {
      logout();
      return null;
    }
    
    return response;
  };

  return (
    <div className="container mx-auto p-4">
      <div className="flex justify-between items-center mb-8">
        <h1 className="text-2xl font-bold">Garage Control</h1>
        <button
          onClick={logout}
          className="bg-red-500 text-white px-4 py-2 rounded"
        >
          Logout
        </button>
      </div>

      <div className="relative w-full max-w-md mx-auto h-64 mb-8 border-2 border-gray-300 rounded-lg overflow-hidden">
        {/* Garage Frame */}
        <div className="absolute inset-0 bg-gray-200">
          {/* Garage Door */}
          <div className="tenor-gif-embed h-full" data-postid="22656380" data-share-method="host" data-aspect-ratio="1" data-width="100%"><a href="https://tenor.com/view/cat-space-nyan-cat-gif-22656380">Cat Space GIF</a>from <a href="https://tenor.com/search/cat-gifs">Cat GIFs</a></div> <script type="text/javascript" async src="https://tenor.com/embed.js"></script>
          <div
            className={`absolute inset-x-0 bg-gray-400 transition-all duration-7000 ease-linear top-0 z-10
              ${doorState === 'closed' ? 'h-full' : 
                doorState === 'open' ? 'h-[10%]' : 
                doorState === 'opening' ? 'animate-door-opening' : 
                'animate-door-closing'}`}
          >
            {/* Door Pattern */}
            <div className="h-full w-full grid grid-rows-4 gap-1 p-1">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-gray-500 rounded"></div>
              ))}
            </div>
          </div>
        </div>

        {/* Status Indicator */}
        <div className={`absolute top-2 right-2 h-4 w-4 rounded-full
          ${isAnimating ? 'bg-yellow-500' : 
            doorState === 'open' ? 'bg-green-500' : 'bg-red-500'}`}
        ></div>
      </div>

      <div className="grid grid-cols-2 gap-4 mb-8">
        <button
          onClick={() => controlGarage('left')}
          disabled={isAnimating || doorState === 'open'}
          className={`p-4 rounded text-white transition-colors
            ${isAnimating || doorState === 'open' 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-green-500 hover:bg-green-600'}`}
        >
          Open
        </button>
        <button
          onClick={() => controlGarage('right')}
          disabled={isAnimating || doorState === 'closed'}
          className={`p-4 rounded text-white transition-colors
            ${isAnimating || doorState === 'closed'
              ? 'bg-gray-400 cursor-not-allowed'
              : 'bg-red-500 hover:bg-red-600'}`}
        >
          Close
        </button>
      </div>

      <div className="space-y-4">
        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-bold mb-2">Status:</h2>
          {status ? (
            <>
              <p>Temperature: {formatNumber(status.temperature)}°C</p>
              <p>Humidity: {formatNumber(status.humidity)}%</p>
              <p>State: {formatState(doorState)}</p>
            </>
          ) : (
            <p>Loading status...</p>
          )}
        </div>

        <div className="bg-gray-100 p-4 rounded">
          <h2 className="font-bold mb-2">Recent Activity:</h2>
          <div className="max-h-48 overflow-y-auto">
            {logs.length > 0 ? (
              logs.map((log, index) => (
                <div key={index} className="mb-2 text-sm">
                  {log.timestamp}: User {log.user} - {log.action}
                </div>
              ))
            ) : (
              <p>No recent activity</p>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}