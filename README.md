# FestPass 2026

College fest registration built with Flask, PostgreSQL, Nginx, and Docker Compose. This repository is the Docker and container security practical assessment for registration number `202401100100247`.

## Architecture

```text
Browser :1247
    |
    v
Nginx (frontend_backend) --> Flask (frontend_backend + backend_database) --> PostgreSQL 17 (backend_database)
```

The frontend joins only `frontend_backend`; PostgreSQL joins only `backend_database`. Flask is the only service connected to both networks. PostgreSQL data is stored in the named volume `registrations_data`; `docker compose down` preserves it.

## Stack

- Python 3.13.18 slim Bookworm, Flask, Psycopg 3, non-root `app` user
- PostgreSQL 17 Alpine
- Nginx 1.30 Alpine
- Docker Compose
- Trivy 0.76.1

## Prerequisites

- Docker Desktop with Docker Compose
- PowerShell
- Trivy is run as the pinned `aquasec/trivy:0.76.1` container
- Docker Hub authentication is needed for publishing; it is not stored in this repository

## Configuration

Create a local `.env` from `.env.example` and set a strong private `POSTGRES_PASSWORD`. The file is ignored by Git. Never place database credentials in frontend files, commits, or terminal output.

| Variable | Purpose |
| --- | --- |
| `POSTGRES_DB` | PostgreSQL database name |
| `POSTGRES_USER` | PostgreSQL application user |
| `POSTGRES_PASSWORD` | Local database password, passed to Flask as `PGPASSWORD` |
| `REGNO` | Assessment registration number, `202401100100247` |
| `APP_VERSION` | Backend image tag and health response version; defaults to `1.0.0` in Compose |

## Run and Verify

```powershell
docker compose config --quiet
docker compose up -d --build
docker compose ps
Invoke-RestMethod http://localhost:1247/api/health
Invoke-RestMethod http://localhost:1247/api/registrations
```

Open `http://localhost:1247` for the responsive registration form and attendee list. Stop and restart without deleting records:

```powershell
docker compose down
docker compose up -d
```

Do not use `docker compose down -v` when preserving assessment data.

## API

- `GET /api/health` returns service status, registration number, database connectivity, and application version.
- `GET /api/registrations` returns persisted registrations.
- `POST /api/registrations` creates a registration and returns HTTP 201.

Example request:

```powershell
$body = @{ name = 'Example Student'; event = 'Opening Ceremony' } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri http://localhost:1247/api/registrations -ContentType 'application/json' -Body $body
```

Valid events are Opening Ceremony, Battle of the Bands, Dance Showcase, Fest Tech Expo, and Photography Walk. Invalid names/events return HTTP 400; database failures return HTTP 503.

## Security Scan Results

Scans used Trivy `0.76.1` and its vulnerability database as downloaded on 2026-10-28. The Stage 1 image was reconstructed from preserved commit `bc7f086` because its original local image layers had been replaced by the Stage 2 build; therefore this is a source-equivalent rebuild, not a byte-for-byte scan of the removed image.

Reproduce the full reports from PowerShell (the Docker socket lets the pinned scanner read local images):

```powershell
$reportDir = "$($PWD.Path)\reports"
docker run --rm --mount type=volume,source=trivy-cache,target=/root/.cache --mount "type=bind,source=$reportDir,target=/reports" -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.1 image --scanners vuln --format table --output /reports/trivy-before.txt fest-backend:0.1
docker run --rm --mount type=volume,source=trivy-cache,target=/root/.cache --mount "type=bind,source=$reportDir,target=/reports" -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.1 image --scanners vuln --format table --output /reports/trivy-after.txt fest-backend:0.2
docker run --rm --mount type=volume,source=trivy-cache,target=/root/.cache -v /var/run/docker.sock:/var/run/docker.sock aquasec/trivy:0.76.1 image --severity CRITICAL --ignore-unfixed --exit-code 1 fest-backend:0.2
```

| Image | Debian HIGH | Debian CRITICAL | Python HIGH | Python CRITICAL | Total HIGH | Total CRITICAL | Image size |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `fest-backend:0.1` | 2,243 | 234 | 3 | 0 | 2,246 | 234 | 1,596,418,096 bytes |
| `fest-backend:0.2` | 59 | 2 | 5 | 0 | 64 | 2 | 216,353,451 bytes |

The total columns sum the separate Debian OS and Python package summary sections from each Trivy report.

The required critical gate passed for `0.2` with exit code 0 using `--severity CRITICAL --ignore-unfixed --exit-code 1`. The full report still lists two CRITICAL OS findings; they are unfixed and are excluded by that gate. This does not mean the image has no critical findings.

Full scan reports: [before](reports/trivy-before.txt) and [after](reports/trivy-after.txt).

## Docker Hub Releases

- [`shubham34970/fest-backend:1.0.0`](https://hub.docker.com/r/shubham34970/fest-backend/tags?name=1.0.0)
- [`shubham34970/fest-backend:1.0`](https://hub.docker.com/r/shubham34970/fest-backend/tags?name=1.0)
- `1.0.0` and `1.0` resolve to manifest digest `sha256:65eb8317605319902f63389348c2fd7f46b132f7498ca826610fb4227b33cc6a`.

Compose pulls `shubham34970/fest-backend:${APP_VERSION:-1.0.0}` rather than building the backend. The image was freshly pulled from Docker Hub and verified to run as UID 999, connect to PostgreSQL, report version `1.0.0`, and list registrations retained in the named volume.

## Cosign

Cosign `v3.1.4` was used. `*.key` is ignored before key generation. Generate a password-protected key pair locally and never share the password or `cosign.key`:

```powershell
cosign generate-key-pair
```

Sign the immutable 1.0.0 digest, then verify using the public key:

```powershell
cosign sign --key cosign.key --yes docker.io/shubham34970/fest-backend@sha256:65eb8317605319902f63389348c2fd7f46b132f7498ca826610fb4227b33cc6a
cosign verify --key cosign.pub docker.io/shubham34970/fest-backend@sha256:65eb8317605319902f63389348c2fd7f46b132f7498ca826610fb4227b33cc6a
```

The 1.0.0 signature verified successfully against `cosign.pub`. Version `1.0.1` was separately built and pushed without signing; its actual digest is `sha256:4a570fb4ffc47812c1e5d231ce1abec387fab6e76c1cf1bcaf445e1733860a02`. Verification against that digest returned `no signatures found` with exit code 10, as expected:

```powershell
cosign verify --key cosign.pub docker.io/shubham34970/fest-backend@sha256:4a570fb4ffc47812c1e5d231ce1abec387fab6e76c1cf1bcaf445e1733860a02
```

`cosign.pub` is safe to publish; `cosign.key` and its password are private. The key password was not recorded in this repository.

## Stage Status

- Stage 1: complete, local commit `bc7f086`.
- Stage 2: complete. Compose, UI, database health, two-network isolation, and persistence across `down`/`up` were verified. Test registrations remain in the local named volume.
- Stage 3: complete. Baseline and hardened reports were generated, non-root execution was verified, and the critical-only gate passed. Two unfixed CRITICAL findings remain in the complete after-report.
- Stage 4: complete. Both 1.0.0 tags are published; the registry digest and fresh-pull runtime were verified.
- Stage 5: complete. The 1.0.0 digest verifies; unsigned 1.0.1 was rejected.

## Screenshots

- [FestPass registration page and persisted attendee list](screenshots/image-1793172490479.png)

This screenshot shows the running FestPass interface. Other images supplied alongside it showed a different registration number or host port and are not included as evidence for this repository.

GitHub contains the completed assessment commit. The screenshot addition will be published in a separate follow-up commit.

## AI Tools

GitHub Copilot was used to assist with implementation, documentation, and validation. Docker, Compose, Trivy, and browser/runtime checks were executed locally; results above reflect observed command output.
