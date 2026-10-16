import styles from "./page.module.css";

const sessions = [
  { slug: "feminino", title: "Ensaio Feminino / Aniversário" },
  { slug: "familia", title: "Ensaio Família" },
  { slug: "corporativo", title: "Corporativo" },
  { slug: "natal", title: "Natal" },
];

export default function Home() {
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
            <a
              key={session.slug}
              className={styles.card}
              href={`/ensaios/${session.slug}`}
            >
              <span>{session.title}</span>
              <strong>→</strong>
            </a>
          ))}
        </div>
      </section>
    </main>
  );
}
