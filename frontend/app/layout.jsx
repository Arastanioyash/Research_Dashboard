import './globals.css';

export const metadata = {
  title: 'Research Dashboard',
  description: 'Survey analytics and admin console'
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
