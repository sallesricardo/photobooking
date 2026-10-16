# PhotoBooking — M3 Agenda Provider

M3 adiciona a primeira versão do fluxo de disponibilidade e encaminhamento para WhatsApp.

## Arquitetura

```text
Frontend
   |
   +--> GET /api/v1/booking/availability
   |             |
   |             v
   |       AgendaService
   |             |
   |             v
   |       AgendaProvider <---- MockAgendaProvider
   |
   +--> POST /api/v1/booking/whatsapp
                 |
                 v
           WhatsAppService
                 |
                 v
             wa.me URL
```

A interface `AgendaProvider` foi criada para que a integração com a plataforma real de agenda seja um adapter, sem contaminar o restante da aplicação.

## Fluxo implementado

1. Cliente escolhe ensaio.
2. Cliente escolhe pacote.
3. Cliente escolhe uma data.
4. Frontend consulta horários disponíveis.
5. Cliente seleciona o horário.
6. Backend valida novamente o horário.
7. Backend monta a mensagem com ensaio, pacote, preço e data/hora.
8. Frontend redireciona para WhatsApp.

## Importante

`MockAgendaProvider` é propositalmente uma implementação local. Ele não representa a agenda real do fotógrafo.

O número usado pelo `WhatsAppService` também é fictício:

```text
5511999999999
```

Antes de publicar, transformar ambos em configuração e implementar o adapter da plataforma de agenda contratada.

## Teste

```bash
docker compose up --build
```

Em outro terminal:

```bash
docker compose exec backend alembic upgrade head
docker compose exec backend python -m app.db.seed
```

Depois acesse:

```text
http://localhost:3000
```

Escolha um ensaio → pacote → data → horário.

## Próxima milestone — M4

- descobrir/confirmar a API ou mecanismo de integração da plataforma Minha Agenda;
- implementar `MinhaAgendaProvider`;
- mover credenciais e número WhatsApp para settings;
- tratar timezone explicitamente;
- evitar double booking na integração real;
- testes automatizados do provider e do fluxo de booking;
- melhorar UX e responsividade.
