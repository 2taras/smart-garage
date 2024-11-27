// src/pages/login.tsx
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import { useAuth } from '../contexts/AuthContext';
import Head from 'next/head';

declare global {
  interface Window {
    onTelegramAuth: (user: any) => void;
  }
}

export default function LoginPage() {
  const { isAuthenticated, login } = useAuth();
  const router = useRouter();
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  useEffect(() => {
    // Define the callback function for Telegram auth
    window.onTelegramAuth = async (user) => {
      setError(null);
      setIsLoading(true);
      try {
        await login(user);
        router.push('/');
      } catch (error) {
        setError('Login failed. Please try again.');
        console.error('Login failed:', error);
      } finally {
        setIsLoading(false);
      }
    };

    // Add the Telegram script
    const script = document.createElement('script');
    script.src = 'https://telegram.org/js/telegram-widget.js?22';
    script.setAttribute('data-telegram-login', process.env.NEXT_PUBLIC_TELEGRAM_BOT_NAME || '');
    script.setAttribute('data-size', 'large');
    script.setAttribute('data-onauth', 'onTelegramAuth(user)');
    script.setAttribute('data-request-access', 'write');
    script.setAttribute('data-radius', '8');
    script.async = true;

    // Add the script to the document
    document.getElementById('telegram-login-container')?.appendChild(script);

    // Cleanup
    return () => {
      const container = document.getElementById('telegram-login-container');
      if (container && container.firstChild) {
        container.removeChild(container.firstChild);
      }
      delete window.onTelegramAuth;
    };
  }, [login, router]);

  return (
    <>
      <Head>
        <title>Login - Smart Garage</title>
      </Head>
      <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <div>
            <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
              Smart Garage Control
            </h2>
            <p className="mt-2 text-center text-sm text-gray-600">
              Please sign in with Telegram to continue
            </p>
          </div>
          
          {error && (
            <div className="rounded-md bg-red-50 p-4 mt-4">
              <div className="flex">
                <div className="flex-shrink-0">
                  <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
                  </svg>
                </div>
                <div className="ml-3">
                  <p className="text-sm text-red-700">{error}</p>
                </div>
              </div>
            </div>
          )}

          <div className="mt-8 flex justify-center">
            {isLoading ? (
              <div className="flex items-center justify-center">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : (
              <div id="telegram-login-container"></div>
            )}
          </div>
        </div>
      </div>
    </>
  );
}