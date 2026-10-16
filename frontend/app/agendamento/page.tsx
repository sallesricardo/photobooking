import Link from "next/link";


export default function BookingPage({
  searchParams,
}: {
  searchParams: { session?: string; package?: string };
}) {
  return (
    <main
      style={{
        minHeight: "100vh",
        display: "grid",
        placeItems: "center",
        padding: 24,
      }}
    >
      <section style={{ maxWidth: 620 }}>
        <p>AGENDAMENTO</p>
        <h1>Próximo passo: escolher data e horário</h1>
        <p>
          Esta etapa será conectada ao provider de agenda na próxima milestone.
        </p>
        <pre
          style={{
            padding: 20,
            borderRadius: 12,
            background: "#f1f1f1",
            overflowX: "auto",
          }}
        >
          {JSON.stringify(searchParams, null, 2)}
        </pre>
        <Link href="/">← Voltar para os ensaios</Link>
      </section>
    </main>
  );
}
