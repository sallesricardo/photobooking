/**
 * Cliente HTTP do frontend (BFF).
 *
 * Os componentes "use client" nunca chamam o FastAPI diretamente: eles falam
 * com a própria origem (`/api/v1/...`). O Route Handler em `app/api/[...path]`
 * faz o proxy server-side para o backend, o que remove a necessidade de CORS
 * e mantém a URL do backend fora do bundle do navegador.
 */

export const API_BASE = "/api/v1";

export class ApiError extends Error {
  readonly status: number;
  readonly requestId?: string;

  constructor(message: string, status: number, requestId?: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.requestId = requestId;
  }
}

type QueryValue = string | number | boolean | undefined | null;

export type ApiFetchOptions = Omit<RequestInit, "body"> & {
  /** Corpo enviado como JSON. */
  body?: unknown;
  /** Query string; valores nulos/undefined são ignorados. */
  query?: Record<string, QueryValue>;
  /** Chave de idempotência propagada ao backend. */
  idempotencyKey?: string;
};

/**
 * Gera uma chave de idempotência. `crypto.randomUUID` só existe em contextos
 * seguros (HTTPS ou localhost), então há um fallback para HTTP em LAN.
 */
export function newIdempotencyKey(): string {
  const cryptoApi = globalThis.crypto;
  if (cryptoApi && typeof cryptoApi.randomUUID === "function") {
    return cryptoApi.randomUUID();
  }
  return `k-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
}

/** Codifica cada segmento do caminho para evitar path traversal. */
function encodePath(path: string): string {
  return path
    .split("/")
    .filter((segment) => segment.length > 0)
    .map(encodeURIComponent)
    .join("/");
}

/** Normaliza o `detail` do FastAPI (string ou lista de erros de validação). */
function extractDetail(payload: unknown): string | undefined {
  if (!payload || typeof payload !== "object") return undefined;

  const detail = (payload as { detail?: unknown }).detail;
  if (typeof detail === "string") return detail;

  if (Array.isArray(detail)) {
    const messages = detail
      .map((item) => {
        if (item && typeof item === "object" && "msg" in item) {
          return String((item as { msg: unknown }).msg);
        }
        return String(item);
      })
      .filter((message) => message.length > 0);
    if (messages.length > 0) return messages.join("; ");
  }

  return undefined;
}

async function readJson(response: Response): Promise<unknown> {
  const text = await response.text();
  if (!text) return null;
  try {
    return JSON.parse(text) as unknown;
  } catch {
    return null;
  }
}

/**
 * Executa uma requisição contra o proxy do BFF e devolve o payload JSON.
 *
 * `path` é relativo a {@link API_BASE} (ex.: `auth/me`, `sessions/feminino`).
 * Lança {@link ApiError} com uma mensagem já pronta para exibição.
 */
export async function apiFetch<T = unknown>(
  path: string,
  options: ApiFetchOptions = {},
): Promise<T> {
  const { body, query, idempotencyKey, headers, ...rest } = options;

  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(query ?? {})) {
    if (value === undefined || value === null) continue;
    search.set(key, String(value));
  }

  const encodedPath = encodePath(path);
  const searchString = search.toString();
  const url = `${API_BASE}/${encodedPath}${searchString ? `?${searchString}` : ""}`;

  const requestHeaders = new Headers(headers);
  requestHeaders.set("accept", "application/json");
  if (body !== undefined) requestHeaders.set("content-type", "application/json");
  if (idempotencyKey) requestHeaders.set("idempotency-key", idempotencyKey);

  const response = await fetch(url, {
    ...rest,
    headers: requestHeaders,
    // Mesmo origem: o cookie de sessão do admin é enviado sem CORS.
    credentials: "include",
    body: body === undefined ? undefined : JSON.stringify(body),
  });

  const payload = await readJson(response);

  if (!response.ok) {
    const detail = extractDetail(payload);
    throw new ApiError(
      detail ?? `Não foi possível concluir a requisição (HTTP ${response.status}).`,
      response.status,
      response.headers.get("x-request-id") ?? undefined,
    );
  }

  return payload as T;
}
