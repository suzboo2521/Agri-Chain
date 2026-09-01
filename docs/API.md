# AgriChain v2 API

Interactive: http://127.0.0.1:8000/docs

All routes exist both at `/api/...` and `/...`.

| Method | Path | Auth |
|---|---|---|
| GET | /health | no |
| POST | /auth/login | no |
| GET | /auth/me | yes |
| GET/POST | /farmers | yes |
| GET/POST | /batches | yes |
| GET | /batches/{id} | yes |
| GET | /batches/{id}/qr | no |
| POST | /events | yes + role |
| POST | /quality | inspector |
| POST | /sensor-data | yes |
| GET | /risk/{id} | yes |
| GET | /blockchain | yes |
| GET | /blockchain/verify | yes |
| POST | /documents/hash | yes |
| POST | /documents/verify | yes |
| GET | /verify/{id} | no |
| POST | /recalls | regulator |
| GET | /analytics | yes |
| POST | /debug/tamper | admin |
| POST | /debug/restore | admin |
