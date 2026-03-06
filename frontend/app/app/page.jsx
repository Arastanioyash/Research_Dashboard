'use client';

import dynamic from 'next/dynamic';
import { useEffect, useMemo, useState } from 'react';
import { apiDownload, apiFetch } from '../../lib/api';
import { clearSessionToken } from '../../lib/auth';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

export default function DashboardPage() {
  const projectId = 'default';
  const [pageSpec, setPageSpec] = useState(null);
  const [activePageId, setActivePageId] = useState('');
  const [questionId, setQuestionId] = useState('');
  const [bannerId, setBannerId] = useState('');
  const [searchMap, setSearchMap] = useState({});
  const [filterValues, setFilterValues] = useState({});
  const [savedViews, setSavedViews] = useState([]);
  const [viewName, setViewName] = useState('');

  useEffect(() => {
    apiFetch(`/projects/${projectId}/page_spec`).then((spec) => {
      setPageSpec(spec);
      setActivePageId(spec.pages?.[0]?.id || '');
      setQuestionId(spec.questions?.[0]?.id || '');
      setBannerId(spec.banners?.[0]?.id || '');
      setFilterValues(Object.fromEntries((spec.filters || []).map((f) => [f.id, []])));
    });
    loadViews();
  }, []);

  const loadViews = async () => {
    const views = await apiFetch(`/projects/${projectId}/views`);
    setSavedViews(views || []);
  };

  const chips = useMemo(
    () => Object.entries(filterValues).flatMap(([filterId, values]) => (values || []).map((value) => ({ key: `${filterId}:${value}`, filterId, value }))),
    [filterValues]
  );

  const toggleFilterValue = (filterId, value) => {
    setFilterValues((prev) => {
      const current = prev[filterId] || [];
      const next = current.includes(value) ? current.filter((v) => v !== value) : [...current, value];
      return { ...prev, [filterId]: next };
    });
  };

  const onPlotClick = (event) => {
    const point = event?.points?.[0];
    if (!point || !pageSpec?.filters?.[0]) return;
    const filterId = pageSpec.filters[0].id;
    const value = String(point.customdata?.value || point.label || point.x || point.y);
    toggleFilterValue(filterId, value);
  };

  const saveView = async () => {
    await apiFetch(`/projects/${projectId}/views`, {
      method: 'POST',
      body: JSON.stringify({ name: viewName, state: { pageId: activePageId, questionId, bannerId, filterValues, chips: chips.map((c) => c.key) } })
    });
    setViewName('');
    loadViews();
  };

  const applyView = (viewId) => {
    const view = savedViews.find((v) => v.id === viewId);
    if (!view) return;
    setActivePageId(view.state.pageId);
    setQuestionId(view.state.questionId);
    setBannerId(view.state.bannerId);
    setFilterValues(view.state.filterValues || {});
  };

  const renameView = async (viewId) => {
    const name = window.prompt('New view name');
    if (!name) return;
    await apiFetch(`/projects/${projectId}/views/${viewId}`, { method: 'PUT', body: JSON.stringify({ name }) });
    loadViews();
  };

  const deleteView = async (viewId) => {
    await apiFetch(`/projects/${projectId}/views/${viewId}`, { method: 'DELETE' });
    loadViews();
  };

  const exportCsv = async () => {
    const params = new URLSearchParams({ pageId: activePageId, questionId, bannerId });
    chips.forEach((chip) => params.append('filters', chip.key));
    const blob = await apiDownload(`/projects/${projectId}/export?${params.toString()}`);
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'dashboard_export.csv';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (!pageSpec) return <main className="container">Loading...</main>;

  const pageIndex = pageSpec.pages.findIndex((p) => p.id === activePageId);

  return (
    <main className="container">
      <div className="row" style={{ justifyContent: 'space-between' }}>
        <h1>Dashboard Runtime</h1>
        <button onClick={() => { clearSessionToken(); location.href = '/login'; }}>Logout</button>
      </div>

      <div className="chips">
        {chips.map((chip) => (
          <button className="chip" key={chip.key} onClick={() => toggleFilterValue(chip.filterId, chip.value)}>{chip.filterId}: {chip.value} ×</button>
        ))}
      </div>

      <div className="row" style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <label>Question</label>
        <select value={questionId} onChange={(e) => setQuestionId(e.target.value)}>{(pageSpec.questions || []).map((q) => <option key={q.id} value={q.id}>{q.label}</option>)}</select>
        <label>Banner</label>
        <select value={bannerId} onChange={(e) => setBannerId(e.target.value)}>{(pageSpec.banners || []).map((b) => <option key={b.id} value={b.id}>{b.label}</option>)}</select>
        <button disabled={pageIndex <= 0} onClick={() => setActivePageId(pageSpec.pages[pageIndex - 1].id)}>Prev Page</button>
        <span>{pageSpec.pages?.[pageIndex]?.label || ''}</span>
        <button disabled={pageIndex >= pageSpec.pages.length - 1} onClick={() => setActivePageId(pageSpec.pages[pageIndex + 1].id)}>Next Page</button>
        <button onClick={exportCsv}>Export CSV</button>
      </div>

      <div className="row" style={{ marginBottom: 12, flexWrap: 'wrap' }}>
        <input value={viewName} onChange={(e) => setViewName(e.target.value)} placeholder="View name" />
        <button onClick={saveView} disabled={!viewName}>Save View</button>
        <select onChange={(e) => applyView(e.target.value)} defaultValue=""><option value="" disabled>Load saved view</option>{savedViews.map((view) => <option key={view.id} value={view.id}>{view.name}</option>)}</select>
        {savedViews.map((view) => <div key={view.id} className="row"><small>{view.name}</small><button onClick={() => renameView(view.id)}>Rename</button><button onClick={() => deleteView(view.id)}>Delete</button></div>)}
      </div>

      <div className="layout">
        <aside className="panel card">
          <h2 className="section-title">Filters</h2>
          {(pageSpec.filters || []).map((filter) => {
            const selected = filterValues[filter.id] || [];
            const search = (searchMap[filter.id] || '').toLowerCase();
            const visible = (filter.options || []).filter((opt) => opt.toLowerCase().includes(search));
            return (
              <div key={filter.id} style={{ marginBottom: 12 }}>
                <strong>{filter.label}</strong>
                <input placeholder={`Search ${filter.label}`} style={{ width: '100%', margin: '6px 0' }} value={searchMap[filter.id] || ''} onChange={(e) => setSearchMap((prev) => ({ ...prev, [filter.id]: e.target.value }))} />
                <div className="listbox">{visible.map((opt) => <label key={opt} className="row" style={{ justifyContent: 'space-between' }}><span>{opt}</span><input type="checkbox" checked={selected.includes(opt)} onChange={() => toggleFilterValue(filter.id, opt)} /></label>)}</div>
              </div>
            );
          })}
        </aside>
        <section className="card">{(pageSpec.charts || []).map((chart) => <div key={chart.id} style={{ marginBottom: 20 }}><h3>{chart.title}</h3><Plot data={chart.data} layout={chart.layout || { autosize: true, height: 360 }} style={{ width: '100%' }} onClick={onPlotClick} /></div>)}</section>
      </div>
    </main>
  );
}
