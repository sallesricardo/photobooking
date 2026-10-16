# PhotoBooking

Projeto demonstrativo de uma plataforma web para fotógrafos apresentarem seus ensaios, pacotes e conduzirem clientes até o agendamento via WhatsApp.

## M2 — Catálogo

- `PhotographySession` e `SessionPackage`
- relacionamento SQLAlchemy one-to-many
- migration Alembic
- seed inicial
- repository e schemas Pydantic
- endpoints REST
- páginas dinâmicas de ensaio
- seleção de pacote
- rota inicial de agendamento

## Executar

```bash
docker compose up --build
```

Em outro terminal:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

- Frontend: http://localhost:3000
- API: http://localhost:8000
- Swagger: http://localhost:8000/docs

Exemplo: http://localhost:3000/ensaios/familia

## API

```text
GET /api/v1/sessions
GET /api/v1/sessions/{slug}
GET /health
```

## Roadmap

- [x] Fundação
- [x] Modelos e migration
- [x] Catálogo de ensaios
- [x] Pacotes
- [ ] Provider de disponibilidade
- [ ] Agendamento
- [ ] Integração WhatsApp
- [ ] Landing page final
- [ ] Deploy/demo
