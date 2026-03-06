'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { apiFetch } from '../../lib/api';
import { setSessionToken } from '../../lib/auth';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(null);

  const onSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    try {
      const session = await apiFetch('/auth/login', {
        method: 'POST',
        body: JSON.stringify({ email, password })
      });
      setSessionToken(session.token);
      router.push(session?.user?.role === 'admin' ? '/admin' : '/app');
    } catch (err) {
      setError(err.message);
    }
  };

  return (
    <main className="container" style={{ maxWidth: 420 }}>
      <div className="card">
        <h1>Login</h1>
        <form onSubmit={onSubmit}>
          <label>Email</label>
          <input value={email} onChange={(e) => setEmail(e.target.value)} style={{ width: '100%', marginBottom: 8 }} required />
          <label>Password</label>
          <input type="password" value={password} onChange={(e) => setPassword(e.target.value)} style={{ width: '100%', marginBottom: 12 }} required />
          <button type="submit">Sign in</button>
        </form>
        {error && <p style={{ color: '#b91c1c' }}>{error}</p>}
      </div>
    </main>
  );
}
