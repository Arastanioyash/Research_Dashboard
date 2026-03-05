'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import SurveyDashboard from '../../components/survey-dashboard';

export default function DashboardPage() {
  const router = useRouter();
  const [authorized, setAuthorized] = useState(false);

  useEffect(() => {
    const token = localStorage.getItem('research-dashboard-auth');

    if (token !== 'authenticated') {
      router.replace('/login');
      return;
    }

    setAuthorized(true);
  }, [router]);

  const handleSignOut = () => {
    localStorage.removeItem('research-dashboard-auth');
    router.replace('/login');
  };

  if (!authorized) {
    return null;
  }

  return (
    <main className="dashboard">
      <button type="button" onClick={handleSignOut} className="secondary-btn">
        Sign out
      </button>
      <SurveyDashboard />
    </main>
  );
}
