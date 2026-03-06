'use client';

import { useState } from 'react';
import { apiFetch } from '../../lib/api';

const modules = ['upload', 'schema', 'banner', 'net', 'page', 'refresh'];

export default function AdminPage() {
  const [projectId, setProjectId] = useState('default');
  const [message, setMessage] = useState('');

  const onAction = async (e, action) => {
    e.preventDefault();
    const formData = new FormData(e.currentTarget);
    const payload = Object.fromEntries(formData.entries());
    try {
      await apiFetch(`/projects/${projectId}/admin/${action}`, {
        method: 'POST',
        body: JSON.stringify(payload)
      });
      setMessage(`${action} action completed.`);
      e.currentTarget.reset();
    } catch (err) {
      setMessage(err.message);
    }
  };

  return (
    <main className="container">
      <h1>Admin</h1>
      <div className="row" style={{ marginBottom: 16 }}>
        <label>Project ID</label>
        <input value={projectId} onChange={(e) => setProjectId(e.target.value)} />
      </div>
      <div className="admin-grid">
        {modules.map((module) => (
          <form key={module} className="card" onSubmit={(e) => onAction(e, module)}>
            <h3>{module.toUpperCase()}</h3>
            <input name="name" placeholder={`${module} payload name`} required style={{ width: '100%', marginBottom: 8 }} />
            <button type="submit">Submit</button>
          </form>
        ))}
      </div>
      {message && <p>{message}</p>}
    </main>
  );
}
