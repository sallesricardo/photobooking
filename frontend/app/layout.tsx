import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "PhotoBooking",
  description: "Agendamento de ensaios fotográficos.",
};

function DemoBanner() {
  if (process.env.ENV !== "demo") {
    return null;
  }

  return (
    <div className="demoBanner" role="status">
      <strong>Demonstração</strong>
      <span>
        Este site é uma demonstração. Os dados cadastrados não são persistentes e podem ser perdidos.
      </span>
    </div>
  );
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="pt-BR">
      <body>
        <DemoBanner />
        {children}
      </body>
    </html>
  );
}
