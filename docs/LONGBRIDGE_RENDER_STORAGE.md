# Longbridge Render storage

Set the Render service environment variable:

```text
DATABASE_URL=postgresql://<user>:<password>@<host>:5432/<database>?sslmode=require
```

The application uses PostgreSQL when `DATABASE_URL` is present and keeps the
existing SQLite path for local development. `longbridge_holdings` is keyed by
`(code, data_date, ccass_id)` and uses an atomic upsert, so repeated fetches do
not duplicate participant rows. Install dependencies from `requirements.txt`
(`psycopg[binary]` is required for the PostgreSQL backend).
