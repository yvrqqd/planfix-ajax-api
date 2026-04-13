[RU](README.ru.md) | **EN**

# planfix-ajax-api

HTTP proxy service for executing AJAX requests against the Planfix CRM system. Authenticates via a headless Chromium browser, captures session tokens, and forwards API calls through authenticated sessions.

---

## Table of Contents

- [Docker](#docker)
- [API & Swagger](#api--swagger)
- [Environment Variables](#environment-variables)

---

## Docker

### Build and run

```bash
docker compose up
```

### Stop

```bash
docker compose down
```

Check service readiness:

```bash
curl http://localhost:8000/api/ready
```

---

## API & Swagger

> **Usage flow:** first create a client via `POST /api/clients` and save the returned `id`, then use that `id` as `client_id` in every `POST /api/run` request.

When `SWAGGER_ENABLED=true`, interactive API documentation is available at:

```
http://localhost:8000/api/ui/
```

![Swagger UI](docs/image.png)

All endpoints are served under the `/api` prefix.

### Client Management


| Method   | Path                       | Description         |
| -------- | -------------------------- | ------------------- |
| `POST`   | `/api/clients`             | Create a new client |
| `GET`    | `/api/clients`             | List all clients    |
| `DELETE` | `/api/clients/{client_id}` | Delete a client     |


**Create client** — `POST /api/clients`

`Content-Type: application/x-www-form-urlencoded`


| Field      | Required | Description             |
| ---------- | -------- | ----------------------- |
| `domain`   | yes      | Planfix instance domain |
| `login`    | yes      | Planfix username        |
| `password` | yes      | Planfix password        |


Returns `201` with `{id, login, domain}` on success.

### Query Execution


| Method | Path       | Description                  |
| ------ | ---------- | ---------------------------- |
| `POST` | `/api/run` | Execute a Planfix AJAX query |


**Execute query** — `POST /api/run`

`Content-Type: application/json`


| Field       | Required | Description                                |
| ----------- | -------- | ------------------------------------------ |
| `client_id` | yes      | ID of a previously created client          |
| `payload`   | yes      | JSON object forwarded to Planfix `/ajax/`  |


Returns `200` with the Planfix response on success.

### Health Check


| Method | Path         | Description                     |
| ------ | ------------ | ------------------------------- |
| `GET`  | `/api/ready` | `200` if ready, `404` otherwise |


---

## Environment Variables

Settings are read from environment variables or a `.env` file in the project root.


| Variable           | Default | Description                                  |
| ------------------ | ------- | -------------------------------------------- |
| `SWAGGER_ENABLED`  | `false` | Serve Swagger UI at `/api/ui/`               |
| `BROWSER_HEADLESS` | `true`  | Run Chromium in headless mode                |
| `BROWSER_TIMEOUT`  | `30000` | Playwright operation timeout in milliseconds |
