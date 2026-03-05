'use client';

import { useMemo, useState } from 'react';
import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const surveyData = [
  { question: 'Satisfaction', type: 'single', count: 42, mean: 4.4 },
  { question: 'Ease of Use', type: 'single', count: 38, mean: 4.1 },
  { question: 'Support Quality', type: 'single', count: 35, mean: 4.3 },
  { question: 'Preferred Channels', type: 'multi', count: 89, mean: 0 },
  { question: 'Used Features', type: 'multi', count: 71, mean: 0 },
  { question: 'Learning Resources', type: 'multi', count: 64, mean: 0 },
];

export default function SurveyDashboard() {
  const [questionType, setQuestionType] = useState('single');

  const filteredRows = useMemo(
    () => surveyData.filter((item) => item.type === questionType),
    [questionType],
  );

  const meanScore = useMemo(() => {
    if (questionType !== 'single') {
      return 'N/A';
    }

    const total = filteredRows.reduce((sum, row) => sum + row.mean, 0);
    return (total / filteredRows.length).toFixed(2);
  }, [filteredRows, questionType]);

  return (
    <>
      <section className="dashboard-header">
        <div>
          <p className="eyebrow">Survey Analytics</p>
          <h1>Response Insights</h1>
          <p className="subtitle">Single select and multi select question performance.</p>
        </div>
        <select
          value={questionType}
          onChange={(event) => setQuestionType(event.target.value)}
          className="type-select"
          aria-label="Question type selector"
        >
          <option value="single">Single Select</option>
          <option value="multi">Multi Select</option>
        </select>
      </section>

      <section className="stats-grid">
        <article className="stat-card">
          <p>Question Type</p>
          <h2>{questionType === 'single' ? 'Single Select' : 'Multi Select'}</h2>
        </article>
        <article className="stat-card">
          <p>Total Questions</p>
          <h2>{filteredRows.length}</h2>
        </article>
        <article className="stat-card">
          <p>Total Responses</p>
          <h2>{filteredRows.reduce((sum, row) => sum + row.count, 0)}</h2>
        </article>
        <article className="stat-card">
          <p>Mean Score</p>
          <h2>{meanScore}</h2>
        </article>
      </section>

      <section className="chart-card">
        <Plot
          data={[
            {
              x: filteredRows.map((row) => row.question),
              y: filteredRows.map((row) => row.count),
              type: 'bar',
              marker: { color: questionType === 'single' ? '#2563eb' : '#7c3aed' },
              name: 'Responses',
            },
          ]}
          layout={{
            title:
              questionType === 'single'
                ? 'Single Select Question Responses'
                : 'Multi Select Question Responses',
            paper_bgcolor: '#ffffff',
            plot_bgcolor: '#ffffff',
            margin: { l: 40, r: 30, t: 60, b: 40 },
            yaxis: { title: 'Response Count' },
          }}
          useResizeHandler
          style={{ width: '100%', height: '100%' }}
          config={{ responsive: true, displaylogo: false }}
        />
      </section>

      <section className="table-card">
        <h3>Survey Data Table</h3>
        <table>
          <thead>
            <tr>
              <th>Question</th>
              <th>Type</th>
              <th>Responses</th>
              <th>Mean</th>
            </tr>
          </thead>
          <tbody>
            {filteredRows.map((row) => (
              <tr key={row.question}>
                <td>{row.question}</td>
                <td>{row.type}</td>
                <td>{row.count}</td>
                <td>{row.mean ? row.mean : '-'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
