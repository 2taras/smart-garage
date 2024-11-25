'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { GarageDoor } from './components/garage_door';
import { TempOutput } from './components/temp_sensor';
import { getGarages, controlGarage, getCurrentUser } from './api';
import { Garage, User } from './types';
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"

export default function Page() {
  const [garages, setGarages] = useState<Garage[]>([]);
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);
  const router = useRouter();

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const userData = await getCurrentUser();
        setUser(userData);
        fetchGarages();
      } catch (error) {
        router.push('/auth/telegram');
      }
    };

    checkAuth();
  }, [router]);

  const fetchGarages = async () => {
    try {
      const garageData = await getGarages();
      setGarages(garageData);
      setError(null);
    } catch (err) {
      setError('Failed to fetch garage data');
    } finally {
      setLoading(false);
    }
  };

  const handleToggleDoor = async (garage: Garage) => {
    setLoading(true);
    try {
      const action = garage.current_state === 'closed' ? 'open' : 'close';
      await controlGarage(garage.id, action);
      await fetchGarages(); // Refresh data
    } catch (error) {
    } finally {
      setLoading(false);
    }
  };

  if (!user) {
    return null; // Or loading spinner
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-7xl mx-auto p-6">
        <Card className="mb-6">
          <CardHeader>
            <CardTitle className="text-2xl">Smart Garage Control</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-sm text-gray-500">
              Welcome, {user.username}
            </div>
          </CardContent>
        </Card>

        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertTitle>Error</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {garages.map((garage) => (
            <Card key={garage.id} className="relative">
              <CardHeader>
                <CardTitle>{garage.name}</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <GarageDoor
                    isOpen={garage.current_state === 'open' || garage.current_state === 'opening'}
                    isLoading={loading}
                    onToggle={() => handleToggleDoor(garage)}
                  />
                  {garage.temperature && (
                    <TempOutput
                      name={`${garage.name} Temperature`}
                      currentTemp={garage.temperature}
                      targetTemp={21}
                    />
                  )}
                  <div className="text-sm text-gray-500">
                    Status: {garage.current_state}
                  </div>
                </div>
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="mt-6 flex justify-center">
          <Button
            onClick={fetchGarages}
            disabled={loading}
          >
            {loading ? "Refreshing..." : "Refresh Status"}
          </Button>
        </div>
      </div>

      {loading && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center">
          <Card className="w-[300px]">
            <CardContent className="pt-6">
              <div className="flex flex-col items-center space-y-4">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
                <p className="text-sm text-gray-500">Loading...</p>
              </div>
            </CardContent>
          </Card>
        </div>
      )}
    </div>
  );
}