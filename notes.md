# notes.md — design assumptions & scale/ops thinking

Explains **why** the project is structured this way, plus the three scale
questions the brief asked explicitly (crawler hygiene, queueing, large-scale storage).

---

## 1. Design assumptions

### 1.1 Synthetic data only
- This is a hiring test; every profile is generated locally by
  `scripts/generate_sample_data.py`.
- `profile_url` values are **fake identifiers** (`/example-person-01` … `/example-person-10`).
  They act as IDs, not as fetch targets.
- **No HTTP, no scraping, no network** anywhere in the codebase.

### 1.2 One organization
- All 10 people work at a single fictional org so that `reports_to` / `mentor` /
  `colleague` edges form a meaningful social graph.
- Cross-company edges would need a different model (bipartite person–company).

### 1.3 Fixed schema
- The pipeline consumes exactly one shape, defined by
  `config.REQUIRED_PROFILE_KEYS`.
- Any missing key raises `ProfileValidationError`; duplicate ids are rejected.
- **Failures are raised, never signalled via `None`.**

### 1.4 Hand-tuned weights (not learned)
- `RELATION_WEIGHTS` and `INTERACTION_WEIGHTS` are opinionated heuristics
  (a repost counts more than a reaction).
- `distance = 1 / weight` so centrality treats stronger ties as shorter paths.
- `influence_score` averages three **min-max-scaled** metrics, so no metric
  dominates by scale.

### 1.5 Skill spelling is intentionally messy
- Sample data contains `"ML"`, `" Python "`, `"K8s"`, `"Postgres"`, `"CI CD"`.
- `normalize_skill` → clean_text → lowercase → `SKILL_ALIASES`.
- This is what the "ML pipeline" actually does: cleaning + feature-space build
  before TF-IDF + KMeans.

### 1.6 Reproducibility first
- `RANDOM_SEED = 42` (KMeans, spring layout).
- `REFERENCE_DATE = 2026-11-01` — open-ended jobs use this fixed date so
  `duration_months` never drifts across runs.

### 1.7 The graph is undirected
- `reports_to` and `mentor` are semantically directional, but for community
  detection and influence we want *proximity*. Directionality is preserved in
  the edge attribute `relations` (e.g. `["reports_to", "activity:comment"]`)
  for anyone who wants to rebuild a directed variant later.

---

## 2. If the data were collected online

Even though this project fetches nothing, the same pipeline would stay safe to
run online with a thin fetch layer on top.

### 2.1 HTTP client & retries
- One long-lived `httpx.Client` (or `aiohttp` in async mode) per worker.
- Exponential backoff + jitter on `429 / 5xx`; hard cap on retries.
- **Respect `Retry-After`** if present.
- Timeouts: connect 5s, read 15s; nothing hangs indefinitely.

### 2.2 User-Agent & headers
- **Descriptive User-Agent with contact info**, not a browser spoof, e.g.
  `linkedin-network-analyzer/0.1 (+mailto:you@example.com)`.
- Consistent `Accept` / `Accept-Language` across the run.
- `If-None-Match` / `If-Modified-Since` on re-fetches to save bandwidth.

### 2.3 Rate limiting
- **Client-side:** token bucket per domain (e.g. 1 req/s sustained, burst 3),
  via `asyncio.Semaphore` + sleep or `aiolimiter`.
- **Server-side:** honor `X-RateLimit-*` headers when present.
- **Aggregate:** global concurrency cap (e.g. 8 in-flight) so one job can't
  saturate the egress IP.

### 2.4 Robots & ToS
- Check `robots.txt` first (cached for the run).
- Respect `Allow` / `Disallow`.
- Where ToS forbids scraping, use the **official API** or a licensed data
  provider — same architecture, different client.

### 2.5 Failure modes & observability
- Structured JSON logs: `request_id`, `url`, `status`, `latency_ms`.
- Dead-letter bucket for **non-retryable** responses (`403`, `404`, schema mismatch).
- Alert on error-rate spikes; never silently drop a profile.

---

## 3. Queueing with Redis / Kafka

The pipeline is synchronous — 10 profiles, one file, trivial. At scale, split
into **fetch → normalize → analyze → export**, connected by queues.

### 3.1 Redis Streams (lighter, ~10⁵ msg/s)
- Streams: `profiles.raw`, `profiles.normalized`, `graph.build`, `analysis.run`.
- `XADD` to produce; consumer groups with `XREADGROUP` to consume.
- **At-least-once** + idempotent consumers keyed by `profile_id`.
- `PEL` + `XAUTOCLAIM` for crash recovery.
- Good fit for small/medium batches and simple deployment.

### 3.2 Kafka (heavier, partitioned, durable)
- Topics: `raw-profiles`, `normalized-profiles`, `graph-snapshots`.
- Partition key = `profile_id` — per-person ordering guaranteed.
- Retention acts as a replay buffer — re-run analysis without re-fetching.
- Schema management via **Avro / Protobuf** + a registry (Confluent or Apicurio).
- Exactly-once via Kafka transactions + idempotent producer; most teams start
  with at-least-once + idempotency keys.

### 3.3 Which one here?
- For this test: **none** — 10 profiles, one JSON, synchronous.
- For a real product: start with **Redis Streams** (ops-simple), move to **Kafka**
  once you need per-key ordering, replay, and multi-consumer fan-out.

---

## 4. Large-scale storage strategy

### 4.1 Raw payloads (immutable)
- **Object storage** (S3 / GCS / MinIO), partitioned
  `raw/profiles/{yyyy}/{mm}/{dd}/{profile_id}.json`.
- Write-once. Re-processing = re-reading. Cheap, replayable.

### 4.2 Processed / normalized
- **Parquet on object storage** partitioned by `snapshot_date` and a
  `profile_id` hash.
- Columnar + compression → 5–10× smaller than JSON, fast for analytics.
- Queryable via DuckDB / Athena / Spark.

### 4.3 Analytical tables (graph + centrality)
- `centrality_snapshot` table partitioned by `snapshot_date`.
- Edges as `(source_id, target_id, weight, relations[], snapshot_date)`.
- Communities / skill_clusters similarly snapshotted.
- **A time series of graphs** lets you diff "who was the top broker 6 months ago".

### 4.4 Serving layer
- Interactive queries: Postgres (`profiles`, `edges`, `centrality`, `communities`)
  with a GIN index on `relations`.
- Very large graphs (>10⁷ edges): a native graph store (Neo4j or equivalent),
  bulk-loaded from Parquet.

### 4.5 PII & retention
- Even though the current test is synthetic, a real deployment must:
  - Encrypt at rest (SSE-KMS) and in transit (TLS).
  - Store `profile_id` (hash) separately from raw content.
  - Enforce retention windows and right-to-erasure via row deletes and
    object lifecycle rules.
  - Never log full profile payloads — log only metadata.

---

## 5. What I would do next (out of scope)

- Persist snapshots over time so the report shows **trends**, not a point in time.
- `--compare` mode: diff two snapshots for added / removed / role-changed people.
- Swap `greedy_modularity` for **Leiden** past ~10³ nodes.
- Add a small FastAPI layer to serve `graph.json` to a web frontend.
- Replace hand-tuned weights with a **learned score** (logistic regression on a
  labeled "important person" set) once labels exist.