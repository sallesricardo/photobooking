# PhotoBooking

Projeto demonstrativo de uma plataforma web para fotógrafos apresentarem seus ensaios,
pacotes e conduzirem clientes até o agendamento via WhatsApp.

## Stack

- Frontend: Next.js 14 + TypeScript + CSS Modules
- Backend: Python 3.11 + FastAPI
- Database: PostgreSQL 16
- ORM: SQLAlchemy
- Migrations: Alembic
- Infra: Docker Compose

## Objetivo do MVP

1. Apresentar tipos de ensaio.
2. Apresentar pacotes e preços.
3. Consultar disponibilidade por meio de um provider de agenda.
4. Registrar uma intenção de agendamento.
5. Gerar uma mensagem estruturada para WhatsApp.

## Estrutura

```text
photobooking/
├── backend/
├── frontend/
├── docker-compose.yml
└── README.md
```

## Executar

```bash
docker compose up --build
```

Frontend: http://localhost:3000

API: http://localhost:8000

Swagger: http://localhost:8000/docs

## Roadmap

- [x] Fundação Docker + PostgreSQL + FastAPI + Next.js
- [ ] Modelos e migrations
- [ ] Catálogo de ensaios
- [ ] Pacotes
- [ ] Provider de disponibilidade
- [ ] Agendamento
- [ ] Integração WhatsApp
- [ ] Landing page final
- [ ] Deploy/demo
