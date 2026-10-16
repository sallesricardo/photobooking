import Link from "next/link";
import { notFound } from "next/navigation";
import styles from "./page.module.css";

type Package = {
  id: number;
  name: string;
  description: string;
  price: string;
  duration_minutes: number;
};

type Session = {
  id: number;
  slug: string;
  name: string;
  description: string;
  packages: Package[];
};

async function getSession(slug: string): Promise<Session | null> {
  const api = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
  const r = await fetch(`${api}/api/v1/sessions/${slug}`, {
    cache: "no-store",
  });
  if (r.status === 404) return null;
  if (!r.ok) throw new Error("Não foi possível carregar o ensaio.");
  return r.json();
}

function price(v: string) {
  return Number(v).toLocaleString("pt-BR", {
    style: "currency",
    currency: "BRL",
  });
}

export default async function SessionPage({
  params,
}: {
  params: { slug: string };
}) {
  const s = await getSession(params.slug);
  if (!s) notFound();

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>
          ← Voltar
        </Link>
        <header className={styles.header}>
          <p className={styles.eyebrow}>ENSAIO</p>
          <h1>{s.name}</h1>
          <p>{s.description}</p>
        </header>
        <section>
          <h2>Escolha seu pacote</h2>
          <div className={styles.packages}>
            {s.packages.map((p) => (
              <article className={styles.package} key={p.id}>
                <div>
                  <h3>{p.name}</h3>
                  <p>{p.description}</p>
                  <small>{p.duration_minutes} minutos</small>
                </div>
                <div className={styles.footer}>
                  <strong>{price(p.price)}</strong>
                  <Link
                    href={`/agendamento?session=${s.slug}&package=${p.id}`}
                    className={styles.button}
                  >
                    Agendar
                  </Link>
                </div>
              </article>
            ))}
          </div>
        </section>
      </div>
    </main>
  );
}
