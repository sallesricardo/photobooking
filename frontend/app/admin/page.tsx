"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";

// const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_URL = "http://localhost:8000";

type GoogleStatus = {
  connected: boolean;
  calendar_id: string;
};

export default function AdminPage() {
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [error, setError] = useState("");

  async function loadStatus() {
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/google/status`, { cache: "no-store" });
      if (!response.ok) throw new Error("Não foi possível consultar a integração.");
      setStatus(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao consultar integração.");
    }
  }

  useEffect(() => {
    loadStatus();
  }, []);

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href="/" className={styles.back}>← Voltar para o site</Link>
        <p className={styles.eyebrow}>PAINEL</p>
        <h1 className={styles.header}>Integrações</h1>
        <p className={styles.lead}>Visão rápida do estado da agenda utilizada pelo PhotoBooking.</p>

        <section className={styles.card}>
          <div>
            <span className={styles.label}>Google Calendar</span>
            <strong>{status?.connected ? "Conectado" : "Não conectado"}</strong>
            {status && <small>Calendário: {status.calendar_id}</small>}
          </div>
          <span className={status?.connected ? styles.badgeOk : styles.badge}>{status ? (status.connected ? "ONLINE" : "AÇÃO NECESSÁRIA") : "VERIFICANDO"}</span>
        </section>

        {error && <p className={styles.error}>{error}</p>}

        {!status?.connected && (
          <a className={styles.primary} href={`${API_URL}/api/v1/google/authorize`}>
            Conectar Google Calendar
          </a>
        )}

        <button className={styles.secondary} type="button" onClick={loadStatus}>
          Atualizar status
        </button>

        <p className={styles.note}>
          Esta tela é uma demonstração de portfólio. Em produção, o acesso administrativo deve ser protegido por autenticação e autorização.
        </p>
      </div>
    </main>
  );
}
