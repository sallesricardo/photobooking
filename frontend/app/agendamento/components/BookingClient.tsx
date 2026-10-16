"use client";

import { useEffect, useMemo, useState } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import styles from "./BookingClient.module.css";

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

// const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const API_URL = "http://localhost:8000";

export default function BookingClient() {
  const params = useSearchParams();
  const sessionSlug = params.get("session") ?? "";
  const packageId = Number(params.get("package") ?? 0);

  const [session, setSession] = useState<Session | null>(null);
  const [date, setDate] = useState("");
  const [slots, setSlots] = useState<string[]>([]);
  const [selectedSlot, setSelectedSlot] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const selectedPackage = useMemo(
    () => session?.packages.find((item) => item.id === packageId),
    [session, packageId]
  );

  useEffect(() => {
    if (!sessionSlug) return;
    fetch(`${API_URL}/api/v1/sessions/${sessionSlug}`)
      .then((response) => {
        if (!response.ok) throw new Error("Ensaio não encontrado.");
        return response.json();
      })
      .then(setSession)
      .catch((err) => setError(err.message));
  }, [sessionSlug]);

  async function loadAvailability(value: string) {
    setDate(value);
    setSelectedSlot("");
    setSlots([]);
    setError("");
    if (!value || !selectedPackage) return;

    setLoading(true);
    try {
      const query = new URLSearchParams({
        session_slug: sessionSlug,
        package_id: String(selectedPackage.id),
        target_date: value,
      });
      const response = await fetch(`${API_URL}/api/v1/booking/availability?${query}`);
      if (!response.ok) throw new Error("Não foi possível consultar a agenda.");
      const data = await response.json();
      setSlots(data.slots);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao consultar agenda.");
    } finally {
      setLoading(false);
    }
  }

  async function continueToWhatsApp() {
    if (!selectedSlot) return;
    setLoading(true);
    setError("");
    try {
      const response = await fetch(`${API_URL}/api/v1/booking/whatsapp`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_slug: sessionSlug,
          package_id: selectedPackage?.id,
          start_at: selectedSlot,
        }),
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail ?? "Não foi possível gerar o WhatsApp.");
      window.location.href = data.whatsapp_url;
    } catch (err) {
      setError(err instanceof Error ? err.message : "Erro ao gerar mensagem.");
      setLoading(false);
    }
  }

  return (
    <main className={styles.page}>
      <div className={styles.container}>
        <Link href={`/ensaios/${sessionSlug}`} className={styles.back}>← Voltar</Link>
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
            onChange={(event) => loadAvailability(event.target.value)}
          />

          <h2>Horários disponíveis</h2>
          {loading && <p>Consultando agenda...</p>}
          {!loading && date && slots.length === 0 && <p>Nenhum horário disponível nesta data.</p>}
          <div className={styles.slots}>
            {slots.map((slot) => (
              <button
                key={slot}
                type="button"
                className={selectedSlot === slot ? styles.slotSelected : styles.slot}
                onClick={() => setSelectedSlot(slot)}
              >
                {new Date(slot).toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
              </button>
            ))}
          </div>

          {error && <p className={styles.error}>{error}</p>}

          <button
            type="button"
            className={styles.whatsapp}
            disabled={!selectedSlot || loading}
            onClick={continueToWhatsApp}
          >
            Continuar pelo WhatsApp
          </button>
        </section>
      </div>
    </main>
  );
}
