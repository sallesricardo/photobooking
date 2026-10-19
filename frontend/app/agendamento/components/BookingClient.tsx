"use client";

import { useCallback, useEffect, useMemo, useRef, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import styles from "./BookingClient.module.css";
import { apiFetch, newIdempotencyKey } from "@/lib/api";

type Package = {
  id: number;
  name: string;
  price: string;
  duration_minutes: number;
};

type Session = {
  name: string;
  packages: Package[];
};

type AvailabilityResponse = {
  date: string;
  provider: string;
  slots: string[];
};

type BookingResponse = {
  id: number;
  whatsapp_url: string;
};

/**
 * O agendamento consome a API via o BFF do Next.js (`/api/v1/...`).
 * Nenhuma URL de backend é exposta ao navegador.
 */
const API = "/api/v1";

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error && error.message ? error.message : fallback;
}

/** Formata o slot (ISO naive do backend) no formato hh:mm. */
function formatSlot(slot: string): string {
  const match = /T(\d{2}):(\d{2})/.exec(slot);
  return match ? `${match[1]}:${match[2]}` : slot;
}

export default function BookingClient() {
  const params = useSearchParams();
  const sessionSlug = params.get("session") ?? "";
  const packageId = Number(params.get("package") ?? 0);

  const [session, setSession] = useState<Session | null>(null);
  const [date, setDate] = useState("");
  const [slots, setSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  /** `true` só depois de uma consulta bem-sucedida: distingue "vazio" de "ainda não consultou". */
  const [queried, setQueried] = useState(false);

  /**
   * Chave de idempotência estável por tentativa de reserva. Se a chamada
   * falhar e o usuário tentar de novo, a mesma chave é reaproveitada para o
   * backend não duplicar a reserva nem o evento no Google Calendar.
   */
  const idempotencyKeyRef = useRef<string>("");

  /**
   * Contador de sequência das consultas de disponibilidade. Se o usuário troca
   * de data rapidamente, uma resposta mais lenta poderia chegar depois e
   * sobrescrever a grade com os slots da data anterior.
   */
  const availabilityRequestRef = useRef(0);

  const selectedPackage = useMemo(
    () => session?.packages.find((item) => item.id === packageId),
    [session, packageId]
  );

  const loadSession = useCallback(async () => {
    if (!sessionSlug) return;
    try {
      const data = await apiFetch<Session>(`sessions/${encodeURIComponent(sessionSlug)}`);
      setSession(data);
    } catch (err) {
      setError(errorMessage(err, "Ensaio não encontrado."));
    }
  }, [sessionSlug]);

  const loadAvailability = useCallback(async (value: string) => {
    if (!value || !selectedPackage) return;

    const requestId = ++availabilityRequestRef.current;
    setLoading(true);
    setError("");
    setQueried(false);
    try {
      const data = await apiFetch<AvailabilityResponse>(`booking/availability`, {
        query: {
          session_slug: sessionSlug,
          package_id: selectedPackage.id,
          target_date: value,
        },
      });
      // Resposta obsoleta: uma consulta mais recente já foi disparada.
      if (requestId !== availabilityRequestRef.current) return;
      setSlots(data.slots ?? []);
      setQueried(true);
    } catch (err) {
      if (requestId !== availabilityRequestRef.current) return;
      setError(errorMessage(err, "Erro ao consultar agenda."));
    } finally {
      if (requestId === availabilityRequestRef.current) {
        setLoading(false);
      }
    }
  }, [sessionSlug, selectedPackage]);

  useEffect(() => {
    void loadSession();
  }, [loadSession]);

  /**
   * Recarrega a disponibilidade quando o catálogo ou a data mudam. Sem isso,
   * escolher a data antes de o catálogo carregar deixaria a grade vazia.
   */
  useEffect(() => {
    if (session && date) void loadAvailability(date);
  }, [session, date, loadAvailability]);

  function handleDateChange(value: string) {
    setDate(value);
    setSelectedSlot("");
    setSlots([]);
    setQueried(false);
    setError("");
  }

  async function continueToWhatsApp() {
    if (!selectedSlot || !selectedPackage) return;

    if (!idempotencyKeyRef.current) {
      idempotencyKeyRef.current = newIdempotencyKey();
    }

    setSubmitting(true);
    setError("");
    try {
      const data = await apiFetch<BookingResponse>(`booking/whatsapp`, {
        method: "POST",
        idempotencyKey: idempotencyKeyRef.current,
        body: {
          session_slug: sessionSlug,
          package_id: selectedPackage.id,
          start_at: selectedSlot,
        },
      });

      // Valida o esquema antes de navegar: o valor vem da API.
      const url = new URL(data.whatsapp_url, window.location.origin);
      if (url.protocol !== "https:") {
        throw new Error("URL de WhatsApp inválida.");
      }
      window.location.href = url.toString();
    } catch (err) {
      setError(errorMessage(err, "Erro ao gerar mensagem."));
      setSubmitting(false);
    }
  }

  const showEmptyState = Boolean(date) && !loading && queried && slots.length === 0;

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href={`/ensaios/${encodeURIComponent(sessionSlug)}`} className={styles.back}>← Voltar</Link>
        <header className={styles.header}>
          <p className={styles.eyebrow}>AGENDAMENTO</p>
          <h1>{session?.name ?? "Escolha seu horário"}</h1>
          {selectedPackage && (
            <p>Pacote <strong>{selectedPackage.name}</strong> · {selectedPackage.duration_minutes} minutos</p>
          )}
        </header>

        <section className={styles.panel}>
          <label htmlFor="date">Escolha a data</label>
          <input
            id="date"
            type="date"
            min={new Date().toISOString().slice(0, 10)}
            value={date}
            onChange={(event) => handleDateChange(event.target.value)}
          />

          <h2>Horários disponíveis</h2>
          {loading && <p className={styles.status}>Consultando agenda...</p>}
          {!loading && showEmptyState && <p className={styles.status}>Nenhum horário disponível nesta data.</p>}
          <div className={styles.slots}>
            {slots.map((slot) => (
              <button
                key={slot}
                type="button"
                aria-pressed={selectedSlot === slot}
                className={selectedSlot === slot ? styles.slotSelected : styles.slot}
                onClick={() => setSelectedSlot(slot)}
              >
                {formatSlot(slot)}
              </button>
            ))}
          </div>

          {error && <p className={styles.error} role="alert">{error}</p>}

          <button
            type="button"
            className={styles.whatsapp}
            disabled={!selectedSlot || submitting}
            onClick={continueToWhatsApp}
          >
            {submitting ? "Gerando..." : "Continuar pelo WhatsApp"}
          </button>
        </section>
      </div>
    </main>
  );
}
