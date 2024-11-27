// src/pages/_app.tsx
import type { AppProps } from 'next/app';
import { useRouter } from 'next/router';
import { AuthProvider } from '../contexts/AuthContext';

const publicPaths = ['/login'];

function MyApp({ Component, pageProps }: AppProps) {
  const router = useRouter();
  const isPublicPath = publicPaths.includes(router.pathname);

  return (
    <AuthProvider>
      <Component {...pageProps} />
    </AuthProvider>
  );
}

export default MyApp;