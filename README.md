# PhotoBooking — M4 Google Calendar

M4 substitui a agenda fake por um adapter real para o Google Calendar, mantendo o `MockAgendaProvider` para demonstração local.

## Arquitetura

```text
Next.js
   |
   v
FastAPI
   |
   +--> BookingService / AgendaService
             |
             v
       CalendarProvider
          /        \
         /          \
      Mock        GoogleCalendar
                    |
                    v
              Google Calendar API
```

A integração usa OAuth 2.0 no backend. O Google recomenda o fluxo OAuth para aplicações web server-side e a API oferece operações de free/busy e criação de eventos. Veja a documentação oficial do [Google Calendar API](https://developers.google.com/workspace/calendar/api/quickstart/python) e do [OAuth 2.0 para aplicações web](https://developers.google.com/identity/protocols/oauth2/web-server).

## Fluxo

1. Cliente escolhe ensaio e pacote.
2. Frontend consulta `/api/v1/booking/availability`.
3. `CalendarProvider` consulta a agenda configurada.
4. Cliente escolhe um horário.
5. Backend consulta novamente a disponibilidade.
6. Com `CALENDAR_PROVIDER=google`, o backend faz uma segunda verificação de free/busy imediatamente antes de criar o evento.
7. O evento é criado no Google Calendar.
8. O backend gera a mensagem e a URL do WhatsApp.

## Desenvolvimento sem Google

Por padrão:

```text
CALENDAR_PROVIDER=mock
```

Assim o projeto continua funcionando sem credenciais externas.

## Ativando Google Calendar

No Google Cloud:

1. Crie um projeto.
2. Ative a Google Calendar API.
3. Configure a tela de consentimento OAuth.
4. Crie um OAuth Client para aplicação Web.
5. Adicione este redirect URI:

```text
http://localhost:8000/api/v1/google/callback
```

O quickstart oficial do Google documenta a criação das credenciais e a ativação da API.

Configure no `.env`:

```env
CALENDAR_PROVIDER=google
GOOGLE_CLIENT_ID=...
GOOGLE_CLIENT_SECRET=...
GOOGLE_REDIRECT_URI=http://localhost:8000/api/v1/google/callback
GOOGLE_CALENDAR_ID=primary
APP_SECRET_KEY=uma-chave-aleatoria
```

Suba o projeto e abra:

```text
http://localhost:8000/api/v1/google/authorize
```

Depois da autorização, o backend salva o token em `/app/data/google_token.json`. O Docker Compose usa um volume separado para esse arquivo.

## Escopos usados

- `calendar.events`: acesso para criar e editar eventos.
- `calendar.freebusy`: consulta de disponibilidade.

Esses são escopos oficiais da API Google Calendar.

## Limitações desta milestone

Para manter o projeto adequado a um portfólio, esta primeira integração usa um único calendário e armazena o refresh token em um volume do backend.

Em uma versão de produção multi-cliente, o próximo passo seria:

- tabela de credenciais OAuth por fotógrafo/tenant;
- criptografia dos refresh tokens;
- múltiplos calendários;
- idempotência de booking;
- auditoria;
- tratamento específico de revogação de tokens;
- testes de integração com Google.
