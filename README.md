# PhotoBooking — M5 Portfolio

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
- Geração de mensagem e link de WhatsApp
- Painel demonstrativo para estado da integração
- Testes automatizados do adapter e serviço de WhatsApp
- Docker Compose para ambiente local

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
Gera mensagem
    ↓
WhatsApp
```

## Arquitetura

```text
                         ┌──────────────────┐
                         │     Next.js      │
                         └────────┬─────────┘
                                  │ HTTP
                         ┌────────▼─────────┐
                         │     FastAPI      │
                         └────────┬─────────┘
                                  │
                         ┌────────▼─────────┐
                         │  AgendaService   │
                         └────────┬─────────┘
                                  │ Protocol
                    ┌─────────────┴─────────────┐
                    │                           │
             ┌──────▼──────┐            ┌──────▼──────────┐
             │ MockAgenda  │            │ GoogleCalendar  │
             └─────────────┘            └──────┬──────────┘
                                                │
                                         Google Calendar
```

## Executando

```bash
docker compose up --build
```

Frontend: `http://localhost:3000`

API: `http://localhost:8000`

Swagger: `http://localhost:8000/docs`

Painel demonstrativo: `http://localhost:3000/admin`

## Mock Calendar

Para desenvolvimento local sem credenciais Google:

```env
CALENDAR_PROVIDER=mock
```

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

Depois, acesse `/api/v1/google/authorize` ou use o botão no painel `/admin`.

## Testes

```bash
cd backend
pip install -r requirements.txt
pytest
```

Os testes cobrem a geração do link/mensagem de WhatsApp e a transformação de respostas FreeBusy em slots.

## Endpoints principais

| Método | Endpoint | Finalidade |
|---|---|---|
| GET | `/api/v1/sessions` | Lista ensaios |
| GET | `/api/v1/sessions/{slug}` | Detalhes do ensaio |
| GET | `/api/v1/booking/availability` | Consulta horários |
| POST | `/api/v1/booking/whatsapp` | Valida, cria evento e gera WhatsApp |
| GET | `/api/v1/google/status` | Estado da integração |
| GET | `/api/v1/google/authorize` | Inicia OAuth |
| GET | `/api/v1/google/callback` | Finaliza OAuth |

## Próxima evolução para produção

- autenticação de clientes e fotógrafos;
- OAuth por tenant, em vez de um token global;
- criptografia dos refresh tokens;
- idempotência de reservas;
- persistência própria dos bookings;
- auditoria;
- múltiplos calendários;
- testes de integração com Google;
- observabilidade e rate limiting.
