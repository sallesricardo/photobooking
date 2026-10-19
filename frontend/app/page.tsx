import Link from "next/link";
import styles from "./page.module.css";
import { backendApiUrl } from "@/lib/backend";

type SessionSummary = {
    slug: string;
    name: string;
};

/**
 * Server Component: o catálogo vem do backend (fonte única de verdade),
 * resolvido em runtime via `BACKEND_URL`.
 */
async function getSessions(): Promise<SessionSummary[]> {
    try {
        const response = await fetch(backendApiUrl("/sessions"), { cache: "no-store" });
        if (!response.ok) return [];
        const data = (await response.json()) as SessionSummary[];
        return Array.isArray(data) ? data : [];
    } catch {
        // O site continua acessível mesmo com o backend indisponível.
        return [];
    }
}

export default async function Home() {
    const sessions = await getSessions();

    return (
        <main className={styles.page}>
            <section className={styles.hero}>
                <p className={styles.eyebrow}>PHOTObooking</p>
                <h1>Qual estilo de ensaio você busca?</h1>
                <p className={styles.subtitle}>
                    Encontre o ensaio ideal e avance para o agendamento.
                </p>

                <div className={styles.grid}>
                    {sessions.map((session) => (
                        <Link
                            key={session.slug}
                            className={styles.card}
                            href={`/ensaios/${encodeURIComponent(session.slug)}`}
                        >
                            <span>{session.name}</span>
                            <strong aria-hidden="true">→</strong>
                        </Link>
                    ))}
                </div>
            </section>
        </main>
    );
}
