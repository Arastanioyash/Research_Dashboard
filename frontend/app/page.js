import DashboardChart from '../components/dashboard-chart';

const stats = [
  { label: 'Total Surveys', value: '128' },
  { label: 'Active Projects', value: '12' },
  { label: 'Completion Rate', value: '87%' },
  { label: 'Average Satisfaction', value: '4.4 / 5' },
];

export default function HomePage() {
  return (
    <main className="dashboard">
      <header className="dashboard-header">
        <div>
          <p className="eyebrow">Research Insights</p>
          <h1>Survey Analytics Dashboard</h1>
          <p className="subtitle">
            Track data collection volume, quality, and project health in one place.
          </p>
        </div>
        <button type="button" className="primary-btn">
          Export Report
        </button>
      </header>

      <section className="stats-grid">
        {stats.map((item) => (
          <article key={item.label} className="stat-card">
            <p>{item.label}</p>
            <h2>{item.value}</h2>
          </article>
        ))}
      </section>

      <section className="chart-card">
        <DashboardChart />
      </section>
    </main>
  );
}
