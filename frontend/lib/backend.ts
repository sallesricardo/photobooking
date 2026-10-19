/**
 * Configuração server-side do backend.
 *
 * Importante: este módulo NÃO pode ser importado por componentes "use client",
 * porque `BACKEND_URL` não é uma variável `NEXT_PUBLIC_*` e, portanto, não
 * deve ser exposta no bundle do navegador.
 */

/**
 * URL base do FastAPI, lida em tempo de execução (runtime).
 *
 * Usar uma variável de ambiente server-side — em vez de `NEXT_PUBLIC_API_URL` —
 * é o que permite trocar o backend sem reconstruir a imagem do frontend:
 * `NEXT_PUBLIC_*` é embutido no bundle durante o `next build`.
 */
export const BACKEND_URL = (
  process.env.BACKEND_URL ??
  process.env.NEXT_PUBLIC_API_URL ??
  "http://localhost:8000"
).replace(/\/+$/, "");

/** Caminho interno da API, replicado no backend sob o prefixo `/api/v1`. */
export const API_PREFIX = "/api/v1";

/** Monta a URL completa de um recurso da API no backend. */
export function backendApiUrl(path: string, search?: string): string {
  const suffix = path.startsWith("/") ? path : `/${path}`;
  const query = search && search !== "?" ? (search.startsWith("?") ? search : `?${search}`) : "";
  return `${BACKEND_URL}${API_PREFIX}${suffix}${query}`;
}
