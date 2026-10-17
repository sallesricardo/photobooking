# Deploy PhotoBooking on Render

This project can be deployed as two free Render Web Services:

- `photobooking-api`: FastAPI + SQLite
- `photobooking-web`: Next.js

The database engine is selected exclusively by `DATABASE_URL`. PostgreSQL remains supported; SQLite requires no extra Python dependency because it is provided by Python's standard library.

## Deploy with Blueprint

1. Push the repository to GitHub.
2. In Render, choose **New → Blueprint**.
3. Connect the repository.
4. Render reads `render.yaml` from the repository root.
5. Fill the `sync: false` values when prompted.
6. Deploy.

The API runs Alembic migrations and the catalog seed at startup. `CALENDAR_PROVIDER=mock` keeps the demo independent of Google credentials. Set it to `google` and provide the OAuth variables when a real Calendar integration is desired.

The Blueprint sets `ENV=demo` on both services. The Next.js frontend uses this flag to display the non-persistence demonstration banner.

## Important free-tier behavior

Render Free Web Services spin down after 15 minutes without inbound traffic. They take about a minute to start again. Their local filesystem is ephemeral, so the SQLite file can be lost after a restart, redeploy, or spin-down.

For a persistent database, change only `DATABASE_URL` to a PostgreSQL connection string. The application and migration layer do not require a different persistence implementation.

## Service URLs

The Blueprint uses the stable service names:

- API: `https://photobooking-api.onrender.com`
- Web: `https://photobooking-web.onrender.com`

If you rename either service, update `NEXT_PUBLIC_API_URL`, `FRONTEND_ORIGIN`, and `GOOGLE_REDIRECT_URI` accordingly.
