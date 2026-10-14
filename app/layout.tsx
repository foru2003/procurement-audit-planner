export const metadata = { title: "Procurement Audit Planner" };

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, sans-serif", margin: 0, padding: "2rem", maxWidth: 820 }}>
        {children}
      </body>
    </html>
  );
}
