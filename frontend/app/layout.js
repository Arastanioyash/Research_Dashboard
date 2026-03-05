import './globals.css';

export const metadata = {
  title: 'Research Dashboard',
  description: 'Interactive analytics dashboard built with Next.js and Plotly',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
