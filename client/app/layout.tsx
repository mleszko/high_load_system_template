export const metadata = {
  title: "High Load AI Client",
  description: "Streaming demo client for high_load_system_template",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
