import 'maplibre-gl/dist/maplibre-gl.css';
import './globals.css';

export const metadata = {
  title: 'Thermography Agent',
  description: 'Aerial thermography → per-building insulation scoring & retrofit lead generation',
};

export const viewport = {
  themeColor: '#1b1f24',
  width: 'device-width',
  initialScale: 1,
};

export default function RootLayout({ children }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
