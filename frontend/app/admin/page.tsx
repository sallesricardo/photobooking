"use client";

import { FormEvent, useEffect, useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";

// const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_URL = "http://localhost:8000";

type GoogleStatus = { connected: boolean; calendar_id: string };
type Session = { authenticated: boolean; username: string };
type Booking = {
  id: number;
  session: string;
  package: string;
  price: string;
  start_at: string;
  end_at: string;
  provider: string;
  provider_event_id: string | null;
  status: string;
  customer_name: string | null;
  customer_phone: string | null;
  whatsapp_url: string;
  created_at: string;
};

export default function AdminPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [error, setError] = useState("");
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [actionId, setActionId] = useState<number | null>(null);
  const [rescheduleId, setRescheduleId] = useState<number | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState("");
  const [rescheduleTime, setRescheduleTime] = useState("");

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

  async function loadBookings() {
    setBookingsLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/v1/admin/bookings`, { credentials: "include", cache: "no-store" });
      if (response.status === 401) { setSession(null); return; }
      if (!response.ok) throw new Error("Não foi possível carregar as reservas.");
      setBookings(await response.json());
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao carregar reservas.");
    } finally {
      setBookingsLoading(false);
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
    if (session) { loadStatus(); loadBookings(); }
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

  async function cancelBooking(id: number) {
    if (!window.confirm("Cancelar esta reserva? O evento também será removido da agenda.")) return;
    setActionId(id);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/admin/bookings/${id}/cancel`, {
        method: "POST",
        credentials: "include",
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Não foi possível cancelar a reserva.");
      await loadBookings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao cancelar reserva.");
    } finally {
      setActionId(null);
    }
  }

  async function rescheduleBooking(id: number) {
    if (!rescheduleDate || !rescheduleTime) return;
    setActionId(id);
    setError("");
    try {
      const localDate = new Date(`${rescheduleDate}T${rescheduleTime}:00`);
      const response = await fetch(`${API_URL}/api/v1/admin/bookings/${id}/reschedule`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "include",
        body: JSON.stringify({ start_at: localDate.toISOString() }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Não foi possível reagendar a reserva.");
      setRescheduleId(null);
      setRescheduleDate("");
      setRescheduleTime("");
      await loadBookings();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao reagendar reserva.");
    } finally {
      setActionId(null);
    }
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
          <h1>Entrar no painel</h1>
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
        <h1>Painel</h1>
        <p className={styles.lead}>Agenda, integração e reservas do PhotoBooking em um único lugar.</p>

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
        <button className={styles.secondary} type="button" onClick={() => { loadStatus(); loadBookings(); }}>Atualizar painel</button>

        <section className={styles.reservations}>
          <div className={styles.sectionHeader}>
            <div>
              <span className={styles.label}>AGENDA</span>
              <h2>Reservas recentes</h2>
            </div>
            <span className={styles.count}>{bookings.length}</span>
          </div>
          {bookingsLoading && <p className={styles.note}>Carregando reservas...</p>}
          {!bookingsLoading && bookings.length === 0 && <p className={styles.note}>Nenhuma reserva registrada ainda. Faça um agendamento pelo site para vê-lo aqui.</p>}
          <div className={styles.bookingList}>
            {bookings.map((booking) => (
              <article className={styles.booking} key={booking.id}>
                <div>
                  <span className={styles.bookingDate}>{new Date(booking.start_at).toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" })}</span>
                  <h3>{booking.session}</h3>
                  <p>{booking.package} · R$ {Number(booking.price).toLocaleString("pt-BR", { minimumFractionDigits: 2 })}</p>
                </div>
                <div className={styles.bookingMeta}>
                  <span className={booking.status === "canceled" ? styles.badge : styles.badgeOk}>{booking.status.toUpperCase()}</span>
                  <span>{booking.provider === "google" ? "Google Calendar" : "Mock Calendar"}</span>
                  <a href={booking.whatsapp_url} target="_blank" rel="noreferrer">Abrir WhatsApp</a>
                  {booking.status === "confirmed" && (
                    <>
                      <button type="button" className={styles.secondary} disabled={actionId === booking.id} onClick={() => {
                        setRescheduleId(rescheduleId === booking.id ? null : booking.id);
                        setRescheduleDate(booking.start_at.slice(0, 10));
                        setRescheduleTime(new Date(booking.start_at).toLocaleTimeString("en-CA", { hour: "2-digit", minute: "2-digit", hour12: false }));
                      }}>Reagendar</button>
                      <button type="button" className={styles.logout} disabled={actionId === booking.id} onClick={() => cancelBooking(booking.id)}>Cancelar</button>
                    </>
                  )}
                  {rescheduleId === booking.id && booking.status === "confirmed" && (
                    <div className={styles.rescheduleForm}>
                      <input type="date" value={rescheduleDate} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setRescheduleDate(e.target.value)} />
                      <input type="time" value={rescheduleTime} onChange={(e) => setRescheduleTime(e.target.value)} />
                      <button type="button" className={styles.primary} disabled={actionId === booking.id} onClick={() => rescheduleBooking(booking.id)}>Salvar horário</button>
                    </div>
                  )}
                </div>
              </article>
            ))}
          </div>
        </section>

        <p className={styles.note}>Esta tela usa sessão HttpOnly no backend; o navegador não recebe o token de autenticação em localStorage.</p>
      </div>
    </main>
  );
}
