import { Suspense } from "react";
import BookingClient from "./components/BookingClient";

export default function BookingPage() {
  return (
    <Suspense fallback={<main style={{ padding: 40 }}>Carregando agendamento...</main>}>
      <BookingClient />
    </Suspense>
  );
}
