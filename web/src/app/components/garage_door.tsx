import React from 'react';
import { DoorClosed, DoorOpen, Loader2 } from 'lucide-react';

interface GarageDoorProps {
  name: string;
  isOpen: boolean;
  isLoading: boolean;
  onToggle: () => void;
}

export function GarageDoor({ name, isOpen, isLoading, onToggle }: GarageDoorProps) {
  return (
    <div className="bg-gray-800 rounded-xl p-6 shadow-lg border border-gray-700 w-[35vmax] m-[2vmin]">
      <div className="flex items-center justify-between mb-4">
        <h2 className="text-xl font-semibold text-gray-100">{name}</h2>
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium transition-colors duration-300 ${
            isOpen ? 'bg-green-900/50 text-green-400' : 'bg-red-900/50 text-red-400'
          }`}
        >
          {isOpen ? 'Open' : 'Closed'}
        </span>
      </div>

      {/* Virtual Garage Door Visualization */}
      <div className="relative w-full h-64 mb-6 bg-gray-900 rounded-lg overflow-hidden border border-gray-700">
        {/* Garage Frame */}
        <div className="absolute inset-0 border-8 border-gray-700 rounded-lg">
          {/* Door Panel */}
          <div
            className={`
              absolute inset-x-0 bg-gray-800 border-4 border-gray-700
              transition-all duration-1000 ease-in-out transform
              ${isLoading ? 'animate-pulse' : ''}
              ${isOpen ? 'h-1/6 top-0 opacity-90' : 'h-full top-0'}
            `}
            style={{
              backgroundImage: 'repeating-linear-gradient(0deg, transparent, transparent 20px, #374151 20px, #374151 40px)',
              transformOrigin: 'top',
              transition: 'transform 1.5s cubic-bezier(0.4, 0, 0.2, 1), height 1.5s cubic-bezier(0.4, 0, 0.2, 1)',
              transform: isOpen ? 'perspective(1000px) rotateX(85deg)' : 'perspective(1000px) rotateX(0deg)',
            }}
          >
            {/* Door Sections */}
            {[...Array(4)].map((_, index) => (
              <div
                key={index}
                className="absolute w-full border-b border-gray-700"
                style={{
                  top: `${(index + 1) * 25}%`,
                  transition: 'opacity 0.3s',
                  opacity: isOpen ? 0 : 1,
                }}
              />
            ))}
          </div>
        </div>

        {/* Shadow Effect */}
        <div
          className={`
            absolute bottom-0 left-0 right-0 h-12
            bg-gradient-to-t from-black to-transparent
            transition-opacity duration-1000
          `}
          style={{
            opacity: isOpen ? 0.7 : 0,
          }}
        />
      </div>
      
      <button
        onClick={onToggle}
        disabled={isLoading}
        className={`
          w-full p-4 rounded-lg flex items-center justify-center gap-3
          transition-all duration-300
          ${
            isOpen
              ? 'bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30'
              : 'bg-green-500/20 hover:bg-green-500/30 text-green-400 border border-green-500/30'
          }
          disabled:opacity-50 disabled:cursor-not-allowed
        `}
      >
        {isLoading ? (
          <Loader2 className="w-6 h-6 animate-spin" />
        ) : isOpen ? (
          <>
            <DoorClosed className="w-6 h-6 transition-transform duration-300 transform group-hover:scale-110" />
            Close Door
          </>
        ) : (
          <>
            <DoorOpen className="w-6 h-6 transition-transform duration-300 transform group-hover:scale-110" />
            Open Door
          </>
        )}
      </button>
    </div>
  );
}