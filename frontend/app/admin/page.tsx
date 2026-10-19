"use client";

import { FormEvent, useCallback, useEffect, useState } from "react";
import Link from "next/link";
import styles from "./page.module.css";
import { apiFetch } from "@/lib/api";

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

/**
 * O painel consome a API via o BFF do Next.js (`/api/v1/...`), e não a URL do
 * backend. Isso mantém o cookie de sessão same-origin e dispensa CORS.
 *
 * O prefixo `/api/v1` é adicionado automaticamente por `apiFetch`; aqui só é
 * necessário para o link de navegação do OAuth.
 */
const API = "/api/v1";

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

export default function AdminPage() {
  const [session, setSession] = useState<Session | null>(null);
  const [status, setStatus] = useState<GoogleStatus | null>(null);
  const [error, setError] = useState("");
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [bookingsLoading, setBookingsLoading] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [actionId, setActionId] = useState<number | null>(null);
  const [rescheduleId, setRescheduleId] = useState<number | null>(null);
  const [rescheduleDate, setRescheduleDate] = useState("");
  const [rescheduleTime, setRescheduleTime] = useState("");

  const loadSession = useCallback(async () => {
    try {
      const data = await apiFetch<Session>(`auth/me`);
      setSession(data);
    } catch {
      // 401 (sem sessão) é o estado normal de quem não está autenticado.
      setSession(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadBookings = useCallback(async () => {
    setBookingsLoading(true);
    try {
      const data = await apiFetch<Booking[]>(`admin/bookings`);
      setBookings(data);
    } catch (err) {
      setError(errorMessage(err, "Erro ao carregar reservas."));
    } finally {
      setBookingsLoading(false);
    }
  }, []);

  const loadStatus = useCallback(async () => {
    try {
      const data = await apiFetch<GoogleStatus>(`google/status`);
      setStatus(data);
    } catch (err) {
      setError(errorMessage(err, "Erro ao consultar integração."));
    }
  }, []);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  useEffect(() => {
    if (!session) return;
    void loadStatus();
    void loadBookings();
  }, [session, loadStatus, loadBookings]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setSubmitting(true);
    try {
      await apiFetch(`auth/login`, {
        method: "POST",
        body: { username, password },
      });
      setPassword("");
      await loadSession();
    } catch (err) {
      setError(errorMessage(err, "Não foi possível entrar."));
    } finally {
      setSubmitting(false);
    }
  }

  async function cancelBooking(id: number) {
    if (!window.confirm("Cancelar esta reserva? O evento também será removido da agenda.")) return;
    setActionId(id);
    setError("");
    try {
      await apiFetch(`admin/bookings/${id}/cancel`, { method: "POST" });
      await loadBookings();
    } catch (err) {
      setError(errorMessage(err, "Erro ao cancelar reserva."));
    } finally {
      setActionId(null);
    }
  }

  async function rescheduleBooking(id: number) {
    if (!rescheduleDate || !rescheduleTime) return;
    setActionId(id);
    setError("");
    try {
      await apiFetch(`admin/bookings/${id}/reschedule`, {
        method: "POST",
        // Envio a hora local chosen pelo admin sem converter para UTC: o
        // backend compara com os slots do provider, que são naive (mock).
        body: { start_at: `${rescheduleDate}T${rescheduleTime}:00` },
      });
      setRescheduleId(null);
      setRescheduleDate("");
      setRescheduleTime("");
      await loadBookings();
    } catch (err) {
      setError(errorMessage(err, "Erro ao reagendar reserva."));
    } finally {
      setActionId(null);
    }
  }

  async function handleLogout() {
    setError("");
    try {
      await apiFetch(`auth/logout`, { method: "POST" });
    } catch (err) {
      setError(errorMessage(err, "Erro ao sair."));
    } finally {
      setSession(null);
      setStatus(null);
      setBookings([]);
    }
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
            {error && <p className={styles.error} role="alert">{error}</p>}
            <button className={styles.primary} type="submit" disabled={submitting}>
              {submitting ? "Entrando..." : "Entrar"}
            </button>
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

        {error && <p className={styles.error} role="alert">{error}</p>}
        {!status?.connected && <a className={styles.primary} href={`${API}/google/authorize`}>Conectar Google Calendar</a>}
        <button className={styles.secondary} type="button" disabled={bookingsLoading} onClick={() => { void loadStatus(); void loadBookings(); }}>Atualizar painel</button>

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
                  <p>{booking.package} · R$ {Number(booking.price).toLocaleString("pt-BR", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</p>
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
                      <label htmlFor={`reschedule-date-${booking.id}`}>Data</label>
                      <input id={`reschedule-date-${booking.id}`} type="date" value={rescheduleDate} min={new Date().toISOString().slice(0, 10)} onChange={(e) => setRescheduleDate(e.target.value)} />
                      <label htmlFor={`reschedule-time-${booking.id}`}>Hora</label>
                      <input id={`reschedule-time-${booking.id}`} type="time" value={rescheduleTime} onChange={(e) => setRescheduleTime(e.target.value)} />
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
