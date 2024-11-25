import React from 'react';
import { Thermometer } from 'lucide-react';

interface TempOutputProps {
  name: string;
  currentTemp: number;
  targetTemp: number;
}

export function TempOutput({ 
  name, 
  currentTemp, 
  targetTemp
}: TempOutputProps) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 w-[40vmax] m-[2vmin]">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-100">{name}</h2>
        <span className={`px-3 py-1 rounded-full text-sm font-medium transition-colors duration-300
          ${currentTemp > targetTemp ? 'bg-red-900/50 text-red-400' : 
            currentTemp < targetTemp ? 'bg-blue-900/50 text-blue-400' : 
            'bg-green-900/50 text-green-400'}`}>
          {currentTemp}°C
        </span>
      </div>

      <div className="relative w-full h-64 mb-6 bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-6xl font-bold text-white">
            {currentTemp}°C
          </div>
        </div>
      </div>
    </div>
  );
}