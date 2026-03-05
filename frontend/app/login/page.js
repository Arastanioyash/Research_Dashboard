'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

const DEMO_USER = {
  email: 'admin@research.com',
  password: 'Password@123',
};

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');

  const handleSubmit = (event) => {
    event.preventDefault();

    if (email === DEMO_USER.email && password === DEMO_USER.password) {
      localStorage.setItem('research-dashboard-auth', 'authenticated');
      router.push('/dashboard');
      return;
    }

    setError('Invalid credentials. Try admin@research.com / Password@123');
  };

  return (
    <main className="auth-page">
      <section className="auth-card">
        <p className="auth-eyebrow">Research Dashboard</p>
        <h1>Sign in</h1>
        <p className="auth-subtitle">Access your survey analytics workspace.</p>

        <form onSubmit={handleSubmit} className="auth-form">
          <label htmlFor="email">Email</label>
          <input
            id="email"
            type="email"
            placeholder="admin@research.com"
            value={email}
            onChange={(event) => setEmail(event.target.value)}
            required
          />

          <label htmlFor="password">Password</label>
          <input
            id="password"
            type="password"
            placeholder="Password@123"
            value={password}
            onChange={(event) => setPassword(event.target.value)}
            required
          />

          {error ? <p className="error-message">{error}</p> : null}

          <button type="submit" className="primary-btn full-width">
            Sign in
          </button>
        </form>
      </section>
    </main>
  );
}
