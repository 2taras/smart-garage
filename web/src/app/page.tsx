'use client';

import React, { useState, useEffect } from 'react';

import { GarageDoor } from './components/garage_door';

import axios from 'axios'

interface GarageData {
  isOpen: boolean;
  temperature: number;
  lightStatus: boolean;
  lastActivity: string;
}

const Page = () => {
  const [garageData, setGarageData] = useState<GarageData>({
    isOpen: false,
    temperature: 20,
    lightStatus: false,
    lastActivity: new Date().toLocaleString(),
  });

  const [loading, setLoading] = useState<boolean>(false);

  const [dooropen, setDooropen] = useState<boolean>(false);

  useEffect(() => {
    const fetchGarageData = async () => {
      setLoading(true);
      try {
        const apiUrl = 'http://www.filltext.com/?rows=32&id={number|1000}&firstName={firstName}&lastName={lastName}&email={email}&phone={phone|(xxx)xxx-xx-xx}&address={addressObject}&description={lorem|32}';
        axios.get(apiUrl).then((resp) => {
        setGarageData(prevData => ({
          ...prevData,
          temperature: Math.floor(Math.random() * 10) + 18,
        }));
        })
      } catch (error) {
        console.error('Error fetching garage data:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchGarageData();
    const interval = setInterval(fetchGarageData, 60000);

    return () => clearInterval(interval);
  }, []);

  const handleToggleDoor = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setGarageData(prevData => ({
        ...prevData,
        isOpen: !prevData.isOpen,
        lastActivity: new Date().toLocaleString(),
      }));
    } catch (error) {
      console.error('Error toggling door:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleLight = async () => {
    setLoading(true);
    try {
      await new Promise(resolve => setTimeout(resolve, 1000));
      setGarageData(prevData => ({
        ...prevData,
        lightStatus: !prevData.lightStatus,
        lastActivity: new Date().toLocaleString(),
      }));
    } catch (error) {
      console.error('Error toggling light:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-6xl mx-auto p-6">
      <header className="text-center mb-10">
        <h1 className="text-4xl font-bold text-gray-800">Smart Garage Control</h1>
      </header>

      {/* Status Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        {/* Garage Door Status */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-2">Garage Door</h2>
          <div className={`text-lg font-medium ${garageData.isOpen ? 'text-green-500' : 'text-red-500'}`}>
            {garageData.isOpen ? 'Open' : 'Closed'}
          </div>
        </div>

        {/* Temperature */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-2">Temperature</h2>
          <div className="text-lg font-medium text-blue-500">
            {garageData.temperature}°C
          </div>
        </div>

        {/* Light Status */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <h2 className="text-xl font-semibold mb-2">Lights</h2>
          <div className={`text-lg font-medium ${garageData.lightStatus ? 'text-yellow-500' : 'text-gray-500'}`}>
            {garageData.lightStatus ? 'On' : 'Off'}
          </div>
        </div>
      </div>

      {/* Control Buttons */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
        <button
          onClick={handleToggleDoor}
          disabled={loading}
          className={`p-4 rounded-lg text-white font-medium transition-colors
            ${loading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-blue-500 hover:bg-blue-600'}`}
        >
          {garageData.isOpen ? 'Close Garage Door' : 'Open Garage Door'}
        </button>

        <button
          onClick={handleToggleLight}
          disabled={loading}
          className={`p-4 rounded-lg text-white font-medium transition-colors
            ${loading 
              ? 'bg-gray-400 cursor-not-allowed' 
              : 'bg-yellow-500 hover:bg-yellow-600'}`}
        >
          {garageData.lightStatus ? 'Turn Off Lights' : 'Turn On Lights'}
        </button>
      </div>

      {/* Activity Log */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
        <div className="text-gray-600">
          Last activity: {garageData.lastActivity}
        </div>
      </div>

      <GarageDoor
        isOpen={dooropen}
        isLoading={false}
        onToggle={() => setDooropen(!dooropen)}
      />

      {/* Loading Indicator */}
      {loading && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center">
          <div className="bg-white p-4 rounded-lg shadow-lg">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto"></div>
            <p className="mt-2 text-gray-600">Loading...</p>
          </div>
        </div>
      )}
    </div>
  );
};

export default Page;