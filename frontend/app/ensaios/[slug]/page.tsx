import Link from "next/link";
import { notFound } from "next/navigation";
import styles from "./page.module.css";
import { backendApiUrl } from "@/lib/backend";

type Package = {
    id: number;
    name: string;
    description: string;
    price: string;
    duration_minutes: number
};
type Session = {
    id: number;
    slug: string;
    name: string;
    description: string;
    packages: Package[]
};

/**
 * Esta é uma Server Component: a chamada ao backend acontece no servidor,
 * usando a URL resolvida em runtime (`BACKEND_URL`). O navegador nunca vê a
 * URL do backend, e não há CORS envolvido.
 */
async function getSession(slug: string): Promise<Session | null> {
    const r = await fetch(backendApiUrl(`/sessions/${encodeURIComponent(slug)}`), {
        cache: "no-store"
    });
    if (r.status === 404) return null;
    if (!r.ok) throw new Error("Não foi possível carregar o ensaio.");
    return r.json()
}

function price(v: string) {
    const value = Number(v);
    if (!Number.isFinite(value)) return "—";
    return value.toLocaleString("pt-BR", {
        style: "currency",
        currency: "BRL",
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    });
}

export default async function SessionPage({
    params
}: {
    params: { slug: string }
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
                </header><section>
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
                                        href={`/agendamento?session=${encodeURIComponent(s.slug)}&package=${p.id}`}
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
