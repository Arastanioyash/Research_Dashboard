import './globals.css';

export const metadata = {
  title: 'Research Dashboard UI',
  description: 'Next.js survey dashboard with login and interactive charts',
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
