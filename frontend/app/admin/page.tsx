"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";

// const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_URL = "http://localhost:8000";

type GoogleStatus = { connected: boolean; calendar_id: string };
type Session = { authenticated: boolean; username: string };

export default function AdminPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [error, setError] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);

  async function loadSession() {
    try {
      const response = await fetch(`${API_URL}/api/v1/auth/me`, { credentials: "include", cache: "no-store" });
      if (!response.ok) {
        setSession(null);
        return;
      }
      setSession(await response.json());
    } finally {
      setLoading(false);
    }
  }

  async function loadStatus() {
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/google/status`, {
        credentials: "include",
        cache: "no-store",
      });
      if (response.status === 401) {
        setSession(null);
        return;
      }
      if (!response.ok) throw new Error("Não foi possível consultar a integração.");
      setStatus(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao consultar integração.");
    }
  }

  useEffect(() => {
    loadSession();
  }, []);

  useEffect(() => {
    if (session) loadStatus();
  }, [session]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    const response = await fetch(`${API_URL}/api/v1/auth/login`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      credentials: "include",
      body: JSON.stringify({ username, password }),
    });
    if (!response.ok) {
      setError("Usuário ou senha inválidos.");
      return;
    }
    setPassword("");
    await loadSession();
  }

  async function handleLogout() {
    await fetch(`${API_URL}/api/v1/auth/logout`, { method: "POST", credentials: "include" });
    setSession(null);
    setStatus(null);
  }

  if (loading) return <main className={styles.page}><div className={styles.container}>Carregando...</div></main>;

  if (!session) {
    return (
      <main className={styles.page}>
        <div className={styles.containerNarrow}>
          <Link href="/" className={styles.back}>← Voltar para o site</Link>
          <p className={styles.eyebrow}>ÁREA RESTRITA</p>
          <h1 className={styles.header}>Entrar no painel</h1>
          <p className={styles.lead}>Acesse as configurações e integrações administrativas do PhotoBooking.</p>
          <form className={styles.loginCard} onSubmit={handleLogin}>
            <label>Usuário<input value={username} onChange={(e) => setUsername(e.target.value)} autoComplete="username" required /></label>
            <label>Senha<input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required /></label>
            {error && <p className={styles.error}>{error}</p>}
            <button className={styles.primary} type="submit">Entrar</button>
          </form>
          <p className={styles.note}>Credenciais são configuradas por variáveis de ambiente no backend.</p>
        </div>
      </main>
    );
  }

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <div className={styles.topbar}>
          <Link href="/" className={styles.back}>← Voltar para o site</Link>
          <button className={styles.logout} type="button" onClick={handleLogout}>Sair</button>
        </div>
        <p className={styles.eyebrow}>PAINEL · {session.username}</p>
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
        {!status?.connected && <a className={styles.primary} href={`${API_URL}/api/v1/google/authorize`}>Conectar Google Calendar</a>}
        <button className={styles.secondary} type="button" onClick={loadStatus}>Atualizar status</button>

        <p className={styles.note}>Esta tela usa sessão HttpOnly no backend; o navegador não recebe o token de autenticação em localStorage.</p>
      </div>
    </main>
  );
}
