# PhotoBooking — M7 Admin & Reservations

Projeto de portfólio inspirado em um sistema real de contratação de ensaios fotográficos.

## O que o projeto demonstra

- Next.js 14 + TypeScript + CSS Modules
- FastAPI + Python
- PostgreSQL + SQLAlchemy + Alembic
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

## Arquitetura

```text
                         ┌──────────────────┐
                         │     Next.js      │
                         └────────┬─────────┘
                                  │ HTTP
                         ┌────────▼─────────┐
                         │     FastAPI      │
                         └──────┬─────┬─────┘
                                │     │
                   ┌────────────▼─┐ ┌─▼────────────────┐
                   │ BookingService│ │ Admin API        │
                   └──────┬───────┘ └───────┬───────────┘
                          │                  │
                  ┌───────▼────────┐   ┌────▼──────────┐
                  │CalendarProvider│   │BookingRepository│
                  └───────┬────────┘   └────┬───────────┘
                    ┌─────┴─────┐            │
             ┌──────▼─────┐ ┌──▼─────────┐  │
             │ MockAgenda │ │GoogleCalendar│ │
             └────────────┘ └──────┬──────┘ │
                                   │         │
                             Google Calendar PostgreSQL
```

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

A M7 adiciona a tabela `bookings`:

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


## M8 — Idempotência e ciclo de vida das reservas

A reserva agora usa `Idempotency-Key` para tornar retries seguros e evitar duplicação de eventos. O painel administrativo permite cancelar e reagendar reservas confirmadas. O cancelamento remove o evento do Google Calendar; o reagendamento atualiza o evento existente após nova validação de disponibilidade.

Endpoints administrativos:
- `POST /api/v1/admin/bookings/{id}/cancel`
- `POST /api/v1/admin/bookings/{id}/reschedule`

Migration: `0003_booking_lifecycle`.

## M9 — Resiliência e falhas

A integração com o Google Calendar foi preparada para cenários de falha: consultas de disponibilidade são retryable em erros transitórios (HTTP 429/5xx), enquanto a criação de eventos não é repetida automaticamente por ser uma operação externa não-idempotente.

Para evitar duplicação quando uma criação externa succeeds mas o commit local falha, o evento recebe `photobooking_idempotency_key` em `extendedProperties.private`. Uma nova tentativa com a mesma chave procura primeiro o evento existente e o recupera.

Também foram adicionados testes unitários para recuperação idempotente, retry de `freebusy` e garantia de que `events.insert` não é repetido automaticamente.

Em produção, o próximo passo seria adicionar observabilidade (logs estruturados, correlation/request ID e métricas) e uma fila/outbox para coordenar de forma ainda mais robusta o PostgreSQL e o Google Calendar.

## M9 — Resiliência e idempotência externa

A integração com Google Calendar agora trata falhas transitórias com retry para operações seguras de leitura. A criação de evento não é repetida cegamente: o `Idempotency-Key` é gravado em `extendedProperties.private` do evento e pode ser usado para recuperar um evento criado antes de uma falha de rede. Erros do provider são traduzidos para respostas HTTP 502/503.

## M10 — Observabilidade e readiness

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
