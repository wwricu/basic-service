# wwr.icu service

Public blog API + admin backend, one React Router v7 (framework mode) app. The former
FastAPI service and the separate `admin-page` SPA are merged here: pages and JSON routes
run in the same process and call one shared server-side service layer, so the admin UI
no longer reaches the API over HTTP.

## Layout

```
app/
  root.tsx routes.ts            # app shell and route manifest
  routes/                       # /open/* + /image/* JSON routes, /api/* dispatcher, admin pages
  components/ web/              # admin UI (antd + CKEditor 5) and its browser-side API client
  server/
    db/                         # SQLite access (node:sqlite)
    domain/                     # enums, row/RO/VO types, request validation
    service/                    # business logic, shared by pages and API routes
    lib/ http/ task/            # config, cache, auth, storage, logging, tasks, /api dispatcher
test/
  parity.mjs                    # legacy FastAPI (:8000) vs this app (:5199) response diff
  write-smoke.mjs               # tag/post write cycles, restores the DB snapshot afterwards
```

## Dev

```
$ npm install
$ npm run dev          # react-router dev
```

Pages are served from `http://localhost:5173` and the API from the same origin
(`/open/*` public, `/api/*` admin). The admin API dispatcher keeps the URLs the old SPA
used, so `app/web/api/*` needed no rewriting.

## Scripts

| Command               | Purpose                                  |
|-----------------------|------------------------------------------|
| `npm run dev`         | dev server with HMR                      |
| `npm run build`       | production build into `build/`           |
| `npm start`           | serve the build (`react-router-serve`)   |
| `npm run typegen`     | regenerate route types                   |
| `npm run typecheck`   | `react-router typegen && tsc`            |

## Verify against the legacy backend

`node test/parity.mjs` compares ~100 request cases (status, `allow` header and JSON body)
between the Python service on `:8000` and this app on `:5199`, both pointed at the same
SQLite file. `node test/write-smoke.mjs` then exercises the write paths and checks the
database is back to its original snapshot.

The parity harness needs the removed FastAPI service, which still lives in git history:

```
$ git worktree add ../legacy-fastapi b026b2b
```

Two endpoints read per-process state, so both servers must be equally warm before they can
be compared: `/open/about` returns counters from an in-memory cache that only refreshes
behind five write endpoints, and `POST /login` consumes a per-IP token bucket.

## Environment variables

| Variable name                   | Description                        | Default                  |
|---------------------------------|------------------------------------|--------------------------|
| `AWS_ACCESS_KEY_ID`             | Credentials for S3 storage         | N/A                      |
| `AWS_SECRET_ACCESS_KEY`         | Credentials for S3 storage         | N/A                      |
| `ENV`                           | `local` / `development` / `prod`   | `development`            |
| `BASE_DOMAIN`                   | Domain used for image URLs         | `wwr.icu`                |
| `LOG_PATH`                      | Log directory                      | `logs`                   |
| `ROOT_PATH`                     | Root path the app is mounted on    | `/`                      |
| `CONFIG_FILE`                   | Config file path                   | `config.json`            |
| `VERSION`                       | Reported version                   | `0.0.1`                  |

`config.json` holds the password hash, the session secret key and the open API keys; it is
git-ignored and must stay out of the repository.

## Deploy

The container and CI chain still describe the Python service (`Dockerfile`,
`.github/workflows`) and need to be rewritten for `npm run build && npm start`. Until then,
run the app with Node 22+ (it uses the built-in `node:sqlite` module).
