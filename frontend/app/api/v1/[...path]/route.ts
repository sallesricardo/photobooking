/**
 * BFF (Backend for Frontend) — proxy de `/api/v1/*` para o FastAPI.
 *
 * Por que existe:
 * - Componentes "use client" passam a chamar a própria origem (`/api/v1/...`),
 *   eliminando a URL do backend do bundle do navegador e dispensando CORS.
 * - O cookie `HttpOnly` de sessão do admin deixa de ser cross-site: o navegador
 *   conversa apenas com o frontend, que repassa o cookie ao backend.
 * - A URL do backend passa a ser resolvida em runtime (`BACKEND_URL`), o que
 *   permite trocar de ambiente sem rebuild do frontend.
 *
 * O proxy é deliberadamente "burro": repassa método, corpo, cabeçalhos
 * relevantes e o status/ corpo da resposta. A lógica de negócio continua
 * exclusivamente no FastAPI.
 */

import { NextRequest } from "next/server";

import { backendApiUrl } from "@/lib/backend";

// O proxy resolve o backend em runtime e repassa cookies/IDs: nunca cachear.
export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/** Cabeçalhos de requisição que não devem ser repassados ao backend. */
const REQUEST_HEADERS_TO_STRIP = new Set([
  "host",
  "connection",
  "content-length",
  "accept-encoding",
  "keep-alive",
  "transfer-encoding",
  "upgrade",
  "expect",
  "te",
  "trailer",
]);

/** Cabeçalhos de resposta que não devem ser repassados ao navegador. */
const RESPONSE_HEADERS_TO_STRIP = new Set([
  "connection",
  "keep-alive",
  "transfer-encoding",
  "upgrade",
  "content-encoding",
  "content-length",
]);

/**
 * `fetch` no servidor não repassa cookies automaticamente, então o header
 * `Cookie` precisa ser copiado explicitamente.
 */
function buildRequestHeaders(request: NextRequest): Headers {
  const headers = new Headers();
  request.headers.forEach((value, key) => {
    if (!REQUEST_HEADERS_TO_STRIP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}

function buildResponseHeaders(upstream: Headers): Headers {
  const headers = new Headers();
  upstream.forEach((value, key) => {
    if (!RESPONSE_HEADERS_TO_STRIP.has(key.toLowerCase())) {
      headers.set(key, value);
    }
  });
  return headers;
}

async function proxy(request: NextRequest, path: string[]): Promise<Response> {
  const suffix = path.map(encodeURIComponent).join("/");
  const target = backendApiUrl(`/${suffix}`, request.nextUrl.search);

  const method = request.method.toUpperCase();
  const hasBody = method !== "GET" && method !== "HEAD";

  let upstream: Response;
  try {
    upstream = await fetch(target, {
      method,
      headers: buildRequestHeaders(request),
      body: hasBody ? await request.arrayBuffer() : undefined,
      // Redirecionamentos (ex.: OAuth do Google) precisam chegar intactos
      // ao navegador, com o `Location` preservado.
      redirect: "manual",
      cache: "no-store",
    });
  } catch {
    // Backend indisponível: devolve um erro explícito em vez de um 500 cru.
    return Response.json(
      { detail: "Não foi possível contatar o backend." },
      { status: 502 },
    );
  }

  const headers = buildResponseHeaders(upstream.headers);

  // `Set-Cookie` pode aparecer múltiplas vezes (login/logout). `get()` as
  // juntaria numa única string inválida, por isso usamos `getSetCookie()`.
  const setCookies = upstream.headers.getSetCookie?.() ?? [];
  for (const cookie of setCookies) {
    headers.append("set-cookie", cookie);
  }

  return new Response(upstream.body, {
    status: upstream.status,
    statusText: upstream.statusText,
    headers,
  });
}

type RouteContext = { params: { path: string[] } };

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context.params.path);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context.params.path);
}

export async function PUT(request: NextRequest, context: RouteContext) {
  return proxy(request, context.params.path);
}

export async function PATCH(request: NextRequest, context: RouteContext) {
  return proxy(request, context.params.path);
}

export async function DELETE(request: NextRequest, context: RouteContext) {
  return proxy(request, context.params.path);
}
