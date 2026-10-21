# PhotoBooking

Projeto de portfólio de um sistema real de contratação de ensaios fotográficos.

**[Ver demonstração ao vivo →](https://photobooking-web.onrender.com)**

<img src="docs/images/home.png" alt="Landing page do PhotoBooking com o catálogo de ensaios" width="100%">

## O que o projeto demonstra

- Next.js 14 + TypeScript + CSS Modules
- FastAPI + Python
- PostgreSQL or SQLite + SQLAlchemy + Alembic
- Arquitetura com `CalendarProvider` para desacoplar o domínio do fornecedor de agenda
- Google Calendar API com OAuth 2.0
- Consulta de disponibilidade via FreeBusy
- Criação de eventos no calendário
- Validação de disponibilidade novamente antes do booking
- Persistência de reservas no PostgreSQL
- Painel administrativo protegido por sessão `HttpOnly`
- Lista de reservas recentes no painel
- Geração de mensagem e link de WhatsApp
- Docker Compose para ambiente local
- Testes automatizados do adapter e serviço de WhatsApp

## Fluxo principal

```text
Landing page
    ↓
Ensaio → Pacote
    ↓
Data
    ↓
FastAPI → CalendarProvider → Google Calendar
    ↓
Horários disponíveis
    ↓
Cliente escolhe horário
    ↓
FastAPI valida novamente
    ↓
Cria evento no Google Calendar
    ↓
Registra Booking no PostgreSQL
    ↓
Gera mensagem
    ↓
WhatsApp
```

## Telas

### Escolha do pacote

O catálogo vem do backend e cada ensaio exibe seus pacotes, duração e valor.

<img src="docs/images/packages.png" alt="Página do ensaio com os pacotes Essencial e Premium" width="100%">

### Agendamento

Os horários livres são consultados no Google Calendar (FreeBusy) e recalculados
no servidor antes de confirmar a reserva.

<img src="docs/images/booking.png" alt="Tela de agendamento com a grade de horários disponíveis" width="100%">

### Confirmação no WhatsApp

A reserva é registrada no PostgreSQL e a mensagem é pré-preenchida com o
pacote, o valor e o horário escolhidos.

<img src="docs/images/whatsapp.png" alt="Mensagem pré-preenchida com os dados da reserva no WhatsApp" width="100%">

## Painel administrativo

O `/admin` agora possui autenticação e permite acompanhar:

- estado da conexão com Google Calendar;
- reservas recentes;
- pacote e ensaio contratados;
- data e horário;
- valor;
- provider utilizado;
- ID do evento externo;
- link para continuar o atendimento no WhatsApp.

A autenticação usa uma sessão assinada em cookie `HttpOnly`, com expiração configurável.

<img src="docs/images/admin_login.png" alt="Tela de login do painel administrativo" width="100%">

Após o login, o painel lista as reservas recentes e permite cancelar ou
reagendar cada uma:

<img src="docs/images/admin.png" alt="Painel administrativo com as reservas recentes" width="100%">

## Arquitetura

```text
                         ┌──────────────────┐
   Navegador  ──────────► │     Next.js      │
   (mesma origem)         └────────┬─────────┘
                                  │ BFF: /api/v1/* (server-side)
                         ┌────────▼─────────┐
                         │     FastAPI      │
                         └──────┬──────┬────┘
                                │      │
                   ┌────────────▼──┐ ┌─▼────────────────┐
                   │ BookingService│ │ Admin API        │
                   └──────┬────────┘ └───────┬──────────┘
                          │                  │
                  ┌───────▼────────┐   ┌─────▼───────────┐
                  │CalendarProvider│   │BookingRepository│
                  └───────┬────────┘   └──────┬──────────┘
                    ┌─────┴────┐              │
             ┌──────▼─────┐ ┌──▼───────────┐  │
             │ MockAgenda │ │GoogleCalendar│  │
             └────────────┘ └──────┬───────┘  │
                                   │          │
                           Google Calendar   PostgreSQL
```

## BFF (Backend for Frontend)

O frontend expõe um proxy em `frontend/app/api/v1/[...path]/route.ts`. O
navegador chama apenas rotas da própria origem (`/api/v1/...`); o Next.js
repassa a requisição ao FastAPI no servidor.

Benefícios:

- **Nenhuma URL de backend no bundle do navegador** — a API não é exposta ao
  cliente e o CORS deixa de ser necessário.
- **Sessão same-origin** — o cookie `HttpOnly` do admin pertence ao frontend,
  que o repassa ao backend. Sem `SameSite`/`Secure` frágeis entre domínios.
- **URL do backend resolvida em runtime** — `BACKEND_URL` (não `NEXT_PUBLIC_*`)
  permite trocar de ambiente sem reconstruir a imagem do frontend.
- **Redirecionamentos preservados** — o `Location` do OAuth do Google chega
  intacto ao navegador.

```env
# Variável server-side, lida em runtime pelo proxy.
BACKEND_URL=http://backend:8000
```

O proxy repassa método, corpo, cookies e cabeçalhos (`X-Forwarded-For`,
`Idempotency-Key`), preserva o status e o corpo da resposta, e devolve `502`
quando o backend está indisponível. A lógica de negócio permanece
exclusivamente no FastAPI.

Os componentes `"use client"` usam o helper `frontend/lib/api.ts`:

```ts
import { apiFetch } from "@/lib/api";

const data = await apiFetch<Booking[]>("admin/bookings");
const created = await apiFetch("booking/whatsapp", {
  method: "POST",
  idempotencyKey: key,
  body: { session_slug, package_id, start_at },
});
```

## Ambiente de demonstração

A demonstração pública está em
[photobooking-web.onrender.com](https://photobooking-web.onrender.com).

Quando `ENV=demo`, o frontend exibe um banner no topo informando que esta é uma demonstração e que os dados cadastrados não são persistentes.

O valor pode ser alterado por ambiente: por exemplo, `ENV=development` localmente e `ENV=production` em uma instalação persistente.

## Executando

```bash
docker compose up --build
```

Depois, aplique as migrations:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

Frontend: `http://localhost:3000`
API: `http://localhost:8000`
Swagger: `http://localhost:8000/docs`
Painel: `http://localhost:3000/admin`

## Credenciais do painel

Configure no `.env`:

```env
ADMIN_USERNAME=admin
ADMIN_PASSWORD=troque-esta-senha
ADMIN_SESSION_MINUTES=60
ADMIN_COOKIE_SECURE=false
```

Em produção, use uma senha forte e HTTPS, habilitando `ADMIN_COOKIE_SECURE=true`.

## Mock Calendar

Para desenvolvimento local sem credenciais Google:

```env
CALENDAR_PROVIDER=mock
```

Mesmo usando o mock, os agendamentos são persistidos no PostgreSQL e aparecem no painel.

## Google Calendar

No Google Cloud:

1. Crie um projeto.
2. Ative a Google Calendar API.
3. Configure a tela de consentimento OAuth.
4. Crie credenciais OAuth para aplicação Web.
5. Cadastre o redirect URI `http://localhost:8000/api/v1/google/callback`.

No `.env`:

```env
CALENDAR_PROVIDER=google
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/google/callback
GOOGLE_CALENDAR_ID=primary
APP_SECRET_KEY=...
```

Depois, entre no painel `/admin` e conecte o Google Calendar.

## Migrations

Adiciona a tabela `bookings`:

```text
bookings
 ├── session_id
 ├── package_id
 ├── start_at
 ├── end_at
 ├── provider
 ├── provider_event_id
 ├── status
 ├── customer_name
 ├── customer_phone
 ├── whatsapp_url
 └── created_at
```

O `provider_event_id` permite correlacionar a reserva local com o evento criado no Google Calendar.

## Endpoints principais

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/api/v1/sessions` | Lista ensaios |
| GET | `/api/v1/sessions/{slug}` | Detalhes do ensaio |
| GET | `/api/v1/booking/availability` | Consulta horários |
| POST | `/api/v1/booking/whatsapp` | Valida, cria evento, persiste reserva e gera WhatsApp |
| POST | `/api/v1/auth/login` | Login administrativo |
| POST | `/api/v1/auth/logout` | Logout |
| GET | `/api/v1/auth/me` | Sessão atual |
| GET | `/api/v1/admin/bookings` | Lista reservas autenticada |
| GET | `/api/v1/google/status` | Estado da integração |
| GET | `/api/v1/google/authorize` | Inicia OAuth |
| GET | `/api/v1/google/callback` | Finaliza OAuth |

## Testes

```bash
cd backend
pip install -r requirements.txt
pytest
```

Os testes existentes cobrem a geração do link/mensagem de WhatsApp e a transformação de respostas FreeBusy em slots.

## Próxima evolução para produção

- usuários administrativos persistidos no PostgreSQL;
- hash de senha com Argon2;
- RBAC;
- OAuth por tenant, em vez de um token global;
- criptografia dos refresh tokens;
- idempotência de reservas;
- cancelamento e reagendamento;
- sincronização de cancelamentos do Google Calendar;
- auditoria;
- múltiplos calendários;
- observabilidade e rate limiting.


## Idempotência e ciclo de vida das reservas

A reserva agora usa `Idempotency-Key` para tornar retries seguros e evitar duplicação de eventos. O painel administrativo permite cancelar e reagendar reservas confirmadas. O cancelamento remove o evento do Google Calendar; o reagendamento atualiza o evento existente após nova validação de disponibilidade.

Endpoints administrativos:
- `POST /api/v1/admin/bookings/{id}/cancel`
- `POST /api/v1/admin/bookings/{id}/reschedule`

Migration: `0003_booking_lifecycle`.

## Resiliência e falhas

A integração com o Google Calendar foi preparada para cenários de falha: consultas de disponibilidade são retryable em erros transitórios (HTTP 429/5xx), enquanto a criação de eventos não é repetida automaticamente por ser uma operação externa não-idempotente.

Para evitar duplicação quando uma criação externa succeeds mas o commit local falha, o evento recebe `photobooking_idempotency_key` em `extendedProperties.private`. Uma nova tentativa com a mesma chave procura primeiro o evento existente e o recupera.

Também foram adicionados testes unitários para recuperação idempotente, retry de `freebusy` e garantia de que `events.insert` não é repetido automaticamente.

Em produção, o próximo passo seria adicionar observabilidade (logs estruturados, correlation/request ID e métricas) e uma fila/outbox para coordenar de forma ainda mais robusta o PostgreSQL e o Google Calendar.

## Resiliência e idempotência externa

A integração com Google Calendar agora trata falhas transitórias com retry para operações seguras de leitura. A criação de evento não é repetida cegamente: o `Idempotency-Key` é gravado em `extendedProperties.private` do evento e pode ser usado para recuperar um evento criado antes de uma falha de rede. Erros do provider são traduzidos para respostas HTTP 502/503.

## Observabilidade e readiness

A API agora possui uma camada mínima de observabilidade adequada para um serviço de portfólio/produção inicial:

- `X-Request-ID` aceito ou gerado automaticamente em cada requisição HTTP;
- `X-Request-ID` devolvido na resposta para correlação com logs;
- logs estruturados em JSON com timestamp, nível, logger e request ID;
- handler global para exceções inesperadas, sem expor stack trace ao cliente;
- handler explícito para erros de validação;
- `/health/live` para liveness;
- `/health/ready` para readiness, validando conexão com PostgreSQL;
- logs de criação, idempotência, cancelamento e reagendamento de reservas;
- testes unitários do request ID;
- teste de integração PostgreSQL separado e executado somente quando `TEST_DATABASE_URL` estiver configurado.

### Testes de integração

Os testes normais continuam independentes de infraestrutura externa:

```bash
cd backend
pytest
```

Para executar o teste real contra PostgreSQL:

```bash
export TEST_DATABASE_URL='postgresql+psycopg://photobooking:photobooking@localhost:5432/photobooking'
pytest -m integration
```

O teste de integração não cria nem destrói o banco; ele espera que o ambiente já esteja disponível e verifica a conectividade através do endpoint de readiness.

### Próximos passos de produção

- métricas (latência, taxa de erro e contadores de bookings);
- tracing distribuído, se o sistema ganhar workers/filas;
- outbox/worker para desacoplar transações locais de chamadas externas;
- rate limiting;
- usuários administrativos persistidos, Argon2 e RBAC;
- auditoria de alterações;
- OAuth Google por tenant.

## Métricas, rate limiting e auditoria

- Métricas Prometheus em `GET /metrics`.
- Contadores de requests, duração HTTP, rate-limit e ciclo de vida de reservas.
- Rate limiting em memória por cliente + endpoint, configurável por ambiente.
- Auditoria persistida em PostgreSQL para criação, cancelamento e reagendamento de reservas.
- Cada evento de auditoria registra ação, entidade, ator, `request_id`, metadados e timestamp.
- Para múltiplas réplicas, o rate limiter em memória deve ser substituído por Redis ou outro storage compartilhado.
- Em produção, o endpoint `/metrics` deve ser protegido na rede/reverse proxy.

### testes

```bash
cd backend
pytest
pytest -m integration
```

### Decisões de produção

O rate limiter atual é propositalmente simples: funciona dentro de um único processo e não exige infraestrutura adicional. Em um deployment com múltiplas réplicas, a evolução natural é Redis para compartilhar os buckets entre instâncias.

As métricas evitam usar IDs numéricos/UUIDs diretamente como labels para reduzir cardinalidade. O endpoint `/metrics` deve ficar acessível apenas para o sistema de monitoramento, normalmente por rede privada ou reverse proxy.

A auditoria é best-effort: uma falha ao gravar o log é registrada, mas não derruba uma operação de negócio já concluída. Para requisitos regulatórios mais rígidos, o próximo passo seria um mecanismo transacional/outbox.

## Deployment de produção

O projeto agora possui uma trilha de deployment separada da stack de desenvolvimento.

### Arquitetura de produção

```text
Internet
   |
 HTTPS :443
   v
 Caddy
   |
   +---- /api/* ------> Next.js :3000 --(BFF)--> FastAPI :8000 ----> PostgreSQL :5432
   |
   +---- / ------------> Next.js :3000
```

Componentes:

- **Caddy** como reverse proxy e terminador TLS, com HTTPS automático para um domínio público.
- **FastAPI** executando sem `--reload`, com múltiplos workers Uvicorn configuráveis.
- **Next.js** em imagem standalone de produção, acting as BFF for `/api/*`.
- **PostgreSQL 16** com volume persistente.
- **Alembic** executado por um serviço de migration antes do backend.
- volumes persistentes para PostgreSQL, token OAuth do Google e estado do Caddy.
- headers HTTP básicos de segurança no reverse proxy.

### Subindo em um servidor

1. Instale Docker Engine + Compose plugin.
2. Aponte o DNS do domínio para o servidor.
3. Copie `.env.prod.example` para `.env.prod` e preencha os secrets.
4. Gere valores fortes para `POSTGRES_PASSWORD`, `APP_SECRET_KEY` e `ADMIN_PASSWORD`.
5. Ajuste `APP_DOMAIN`, `FRONTEND_ORIGIN` e `GOOGLE_REDIRECT_URI`.
6. Execute:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml up -d --build
```

O serviço `migrate` executa `alembic upgrade head` antes do backend iniciar.

Para acompanhar o deployment:

```bash
docker compose --env-file .env.prod -f docker-compose.prod.yml ps
docker compose --env-file .env.prod -f docker-compose.prod.yml logs -f backend
```

### HTTPS

O Caddy solicita e renova automaticamente certificados TLS para `APP_DOMAIN`. As portas 80 e 443 precisam estar acessíveis externamente para o fluxo normal de emissão/renovação.

O endpoint `/metrics` não é publicado pelo Caddy em produção. Métricas devem ser coletadas por rede interna ou por um monitoramento que tenha acesso direto ao serviço backend.

### Backup PostgreSQL

Foi adicionado `scripts/backup_postgres.sh`:

```bash
set -a; . ./.env.prod; set +a
./scripts/backup_postgres.sh
```

O resultado é um arquivo `backups/photobooking-<timestamp>.sql.gz`.

Para restauração:

```bash
set -a; . ./.env.prod; set +a
./scripts/restore_postgres.sh backups/photobooking-YYYYMMDDTHHMMSSZ.sql.gz
```

A rotina de backup deve ser agendada externamente, por exemplo via `cron`, e os arquivos devem ser copiados para armazenamento externo. Backup local no mesmo disco do PostgreSQL não é uma estratégia suficiente contra perda do servidor.

### Secrets

`.env.prod` não deve ser versionado. O arquivo de exemplo contém apenas placeholders. Em um ambiente com secret manager, os mesmos valores podem ser injetados como variáveis de ambiente no deployment.

### Worker / jobs assíncronos

Não foi introduzido Celery/RQ/Redis artificialmente nesta etapa. O sistema atual não possui jobs assíncronos que justifiquem essa infraestrutura. Quando surgirem tarefas como envio de notificações, geração de galerias ou sincronizações periódicas, a arquitetura pode evoluir para uma fila + worker sem alterar o fluxo HTTP principal.

### Limitações conhecidas

- O rate limiter do M11 continua sendo local ao processo; múltiplas réplicas exigem Redis.
- O token do Google está em volume persistente compartilhado pela instância atual; uma implantação multi-tenant deve migrar isso para armazenamento seguro por conta/tenant.
- Backups precisam de retenção e armazenamento externo para serem realmente resilientes.
- O Caddy resolve TLS, mas observabilidade de infraestrutura (Prometheus/Grafana, alertas) continua sendo responsabilidade do ambiente de deployment.

## Banco de dados

O mecanismo de persistência é configurável por `DATABASE_URL`. Exemplos:

```env
# PostgreSQL
DATABASE_URL=postgresql+psycopg://photobooking:photobooking@localhost:5432/photobooking

# SQLite
DATABASE_URL=sqlite:///./data/photobooking.db
```

SQLAlchemy e Alembic usam a mesma camada de aplicação para as duas opções. O código habilita `foreign_keys` no SQLite e as migrations usam batch mode quando uma operação DDL não é suportada diretamente pelo SQLite.

## Deploy no Render

Uma versão de demonstração está publicada em
[photobooking-web.onrender.com](https://photobooking-web.onrender.com).

O repositório inclui `render.yaml` para criar os serviços de API e frontend. O serviço da API pode usar SQLite sem adicionar uma dependência externa:

```env
DATABASE_URL=sqlite:///./data/photobooking.db
```

O catálogo pode ser inicializado automaticamente com `RUN_SEED=true` e as migrations com `RUN_MIGRATIONS_ON_START=true`.

O arquivo `deploy/render/README.md` contém o procedimento de publicação.
