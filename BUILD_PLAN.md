# Build plan — make.fun github-core-clone-01

Goal: standalone GitHub-compatible git forge, one Node 22 process, no deps, no git binary, scored by a sealed suite out of 1,000 (feature 600 / agent-MCP 200 / perf 200). Deadline 2026-11-21T06:30:00Z.

## Scaffold (done)
- /workspace/ghclone — starter copied (main.ts lifecycle kept as-is, app.ts to grow), git initialized, MIT license.
- Codex configured at ~/.codex/config.toml (provider xingchi, model gpt-6.1-sol); key at /root/.xingchi_key (exists) → export XINGCHI_API_KEY when running codex.
- Kit at /workspace/github-core-clone-01-kit (sealed suite identical under sdk/ and program/env/). Local grading:
  `node --experimental-strip-types main.ts` then `node sdk/run.ts --url http://127.0.0.1:PORT --token TOK [--perf]`.

## Build order (each step verified against sdk/run.ts)
1. **Store + REST core (repos)** — in-memory store keyed by owner/repo. Routes: GET /api/v3/ (X-OAuth-Scopes), /meta, /user/repos (+ Link rel="next" pagination), POST/GET/PATCH/DELETE /repos/{owner}/{repo}. Every JSON reply with X-GitHub-Request-Id; 401 without bearer; 404 (not 403) for other owners; JSON errors only, 400 on malformed JSON, JSON 404 for unknown routes.
2. **Git object store + smart HTTP** — own packfile/loose-object storage (zlib via node:zlib, sha1 via node:crypto). upload-pack v2 (capability advertisement, ls-refs, fetch incl. shallow for depth-1 clones) with v0 fallback advertising side-band-64k; receive-pack v0 advertising report-status, side-band-64k, delete-refs; per-ref fast-forward enforcement with `ng <ref> non-fast-forward`, report-status lines ok/ng.
3. **REST contents/commits** — PUT/DELETE contents/{path} (201 create / 200 update / 409 stale sha; writes real commits so pushes/clones see them).
4. **Issues, labels, pulls (REST)** — labels before issues (422 on unknown label), issues CRUD, pulls create/get, PUT pulls/{n}/merge (squash onto default branch, 405 on conflict, 404 unknown).
5. **GraphQL** — introspection covering Issue{number,title,state,body}, PullRequest{...files,mergeable}, Repository{databaseId,nameWithOwner,issue,issues,pullRequests,...}, SearchType enum ISSUE; issues ordering CREATED_AT DESC; createPullRequest mutation wired to store; batched ops → array results; unknown field → 200 + errors; unknown repo → data.repository null.
6. **MCP** — JSON-RPC 2.0 streamable HTTP at /mcp, version negotiation (2026-07-28 + handshake revisions), tools/list ≥6 tools (create_repo, get_repo, create_issue, list_issues, create_pull_request, merge_pull_request) with prefix/suffix case-insensitive matching, arg alias mapping (full_name → owner/repo), same store as REST, -32602/-32700/401 semantics, <3s answers, deterministic tools/list.
7. **Performance** — workloads: 200 pushes, 50 concurrent shallow clones of 200-commit repo, 2000 issue reads, 200 issue writes. Score = clamp(25 − 12.5·log2(t/T_ref),0,50) each; T_ref in sdk/conformance/calibration.json. Optimize: pack-avoidance for tiny pushes, precomputed advertisement bytes, keep-alive-friendly issue reads (fast JSON serialize, no per-request allocation churn), concurrency-safe store.
8. **Determinism** — state export must be byte-identical across replay: no timestamps/ports/dates in store state, stable ordering everywhere.

## Constraints to respect
- node main.ts at repo root, stdlib only (vendor anything as source, ≤16 MiB total / 8 MiB per file), 2 CPU / 1 GiB / 900 s wall.
- Bind port 0; never 8080; POST /register; poll /done; exit 0 on done.
- Submission: public GitHub repo created after open, OSI license, README with 3 live make.fun badges + GitHub About (website on make.fun + topic makefun), ≤10 submissions, transcripts bundle via `node cli/makefun.mjs bundle`.
- Baseline (reference forge) entered 4h before deadline; a prize requires beating it.

## Risks
- git pack protocol (v2 fetch + v0 receive) implemented from scratch is the largest chunk and where most git checks (30) live.
- Replay determinism: any nondeterministic field (time, iteration order) unrankes the entry.
- Perf bar vs calibration: clone workload (50 concurrent shallow clones) needs an efficient pack protocol implementation.
- Transcript gate: build must happen in sessions that bundle can collect (run codex/build in recorded harness sessions; ≥5 assistant turns, ≥2 file writes to entrypoint, usage records).
