'use client';

import dynamic from 'next/dynamic';

const Plot = dynamic(() => import('react-plotly.js'), { ssr: false });

const monthlySubmissions = [25, 31, 42, 38, 49, 55, 61, 58, 66, 72, 79, 85];
const responseQuality = [82, 80, 84, 83, 86, 88, 89, 90, 91, 92, 93, 94];

export default function DashboardChart() {
  return (
    <Plot
      data={[
        {
          x: [
            'Jan',
            'Feb',
            'Mar',
            'Apr',
            'May',
            'Jun',
            'Jul',
            'Aug',
            'Sep',
            'Oct',
            'Nov',
            'Dec',
          ],
          y: monthlySubmissions,
          type: 'bar',
          name: 'Responses Collected',
          marker: { color: '#2563eb' },
        },
        {
          x: [
            'Jan',
            'Feb',
            'Mar',
            'Apr',
            'May',
            'Jun',
            'Jul',
            'Aug',
            'Sep',
            'Oct',
            'Nov',
            'Dec',
          ],
          y: responseQuality,
          type: 'scatter',
          mode: 'lines+markers',
          name: 'Quality Score %',
          yaxis: 'y2',
          line: { color: '#16a34a', width: 3 },
        },
      ]}
      layout={{
        autosize: true,
        title: 'Data Collection Trend',
        paper_bgcolor: '#ffffff',
        plot_bgcolor: '#ffffff',
        margin: { l: 40, r: 40, t: 60, b: 40 },
        yaxis: { title: 'Responses' },
        yaxis2: {
          title: 'Quality %',
          overlaying: 'y',
          side: 'right',
          range: [70, 100],
        },
        legend: {
          orientation: 'h',
          y: 1.15,
        },
      }}
      useResizeHandler
      style={{ width: '100%', height: '100%' }}
      config={{ responsive: true, displaylogo: false }}
    />
  );
}
