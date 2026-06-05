# ChartDB

Run this command after the database is up and migrations have completed:

```bash
./scripts/generate-chartdb-schema.sh
```

The generated import payload is written to:

```text
docs/chartdb/schema.json
```

When using `./dev-start.sh`, this file is generated automatically after the backend startup triggers `prestart` migrations.
