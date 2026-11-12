

# LinkedIn Network Analyzer (Synthetic)

Builds a weighted people-graph from **10 synthetic LinkedIn-style profiles** of one
fictional organization ("Nimbus Analytics"), runs **graph analytics** (centrality,
communities) and **ML analysis** (TF-IDF + KMeans skill clustering), and exports
CSV / JSON / PNG / Markdown artifacts.

> **No scraping. No real people. No network access.**
> `profile_url` values are fake identifiers only. All data is generated locally by
> `scripts/generate_sample_data.py`.

---

## Project structure

```

26-linkedin-network-analyzer/
├── data/
│   ├── raw/profiles.json         # generated synthetic input (committed)
│   └── processed/                # CSV + tables.json (regenerable)
├── output/                       # centrality.csv, graph.json, graph.png, report.md
├── scripts/
│   └── generate_sample_data.py   # builds data/raw/profiles.json
├── src/
│   ├── config.py                 # paths, constants, weights, skill aliases
│   ├── exceptions.py             # project error types
│   ├── loader.py                 # read + validate raw JSON
│   ├── normalizer.py             # flatten to pandas DataFrames
│   ├── graph_builder.py          # weighted networkx graph
│   ├── analysis.py               # centrality, communities, TF-IDF + KMeans
│   ├── exporter.py               # CSV/JSON/PNG/report.md
│   └── pipeline.py               # end-to-end orchestration
├── tests/                        # pytest smoke tests
├── main.py                       # CLI entry point
├── requirements.txt
├── notes.md                      # design notes + scale/ops answers
└── README.md

```

---

## Requirements

- Python **3.10+** (uses `X | None`, `from __future__ import annotations`)
- Dependencies in `requirements.txt`:

```

pandas>=2.0,<3.0
networkx>=3.0,<4.0
scikit-learn>=1.3,<2.0
matplotlib>=3.8,<4.0
pytest>=8.0,<9.0

```

---

## How to run

From the project root:

```powershell
# 1) create & activate virtualenv
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt

# 2) generate the synthetic input (10 profiles → data/raw/profiles.json)
python scripts/generate_sample_data.py
#   or equivalently:
python -m scripts.generate_sample_data

# 3) run the full pipeline
python main.py

# 4) run tests
python -m pytest -q
```

Point `--input` at a different JSON (same schema):

```powershell
python main.py --input path\to\profiles.json
```

After step 3 you should see:

- `data/processed/profiles.csv`, `experience.csv`, `education.csv`,
  `skills.csv`, `activity.csv`, `connections.csv`, `tables.json`
- `output/centrality.csv`
- `output/graph.json`
- `output/graph.png`
- `output/report.md`

---

## Data source

Input is **one fixed local file**: `data/raw/profiles.json`, produced by
`scripts/generate_sample_data.py`. It contains 10 synthetic profiles of a single
fictional organization, each with:

- `basic_info` — full_name, headline, location, summary
- `experience` — current + previous role, `start`/`end` as `YYYY-MM`
- `education` — school, degree, field, start_year, end_year
- `skills` — some intentionally messy (`"ML"`, `" Python "`, `"K8s"`, `"Postgres"`)
- `interests`
- `activity` — posts, comments, reactions, reposts; target person when applicable
- `connections` — declared `reports_to` / `mentor` / `colleague` links

`profile_url` values only act as IDs. There is **no scraping and no HTTP**.

---

## Analysis logic

### 1) Normalization

- Whitespace collapsed; case normalized.
- Skills pass through `SKILL_ALIASES` (`ML → machine learning`, `K8s → kubernetes`,
  `Postgres → postgresql`, `UX → ux design`, …); duplicates per profile removed.
- Experience rows compute `duration_months` (open end = fixed `REFERENCE_DATE = 2026-11-01`)
  and `is_current`.

### 2) Graph construction (NetworkX)

- **Nodes**: 10 people (id, name, title, company, location).
- **Edges** from two sources:
  - Declared connections — `reports_to=2.0`, `mentor=2.0`, `colleague=1.0`
  - Targeted activity — `reaction=1.0`, `comment=2.0`, `repost=3.0`
- A `(pair, relation)` is counted once; existing edges accumulate weight.
- Each edge gets `distance = 1 / weight`, so **strong ties become short paths**
  for centrality.

### 3) Centrality — who matters

- `degree_centrality`, `weighted_degree`, `betweenness` (weighted by `distance`),
  `closeness` (weighted by `distance`).
- `influence_score` = mean of **min-max-scaled** degree, weighted-degree and
  betweenness. Min-max keeps three different scales comparable.

### 4) Communities

- `networkx.algorithms.community.greedy_modularity_communities` on the weighted graph.
- Report shows community sizes, members, and modularity score.

### 5) Skill clustering (ML)

- Each person → bag of normalized skill tokens.
- `TfidfVectorizer(analyzer=identity)` — each document is already a token list.
- KMeans for `k ∈ [2, 5]`; keep the `k` with the best silhouette score.
- Report lists, per cluster, the top-5 centroid terms and member names.

### 6) Exports

- `data/processed/*.csv` + `tables.json`
- `output/centrality.csv`
- `output/graph.json` — nodes + edges with `influence_score`, `community`, `skill_cluster`
- `output/graph.png` — node size = influence, color = community, edge width = weight
- `output/report.md` — overview, key people, communities, skill clusters, reading guide

Current sample run (deterministic with `RANDOM_SEED = 42`):

- **10 nodes, 19 edges**, density `0.42`, connected
- Best KMeans `k = 4`, silhouette ≈ `0.12`
- Pipeline finishes in ~1s on a laptop

---

## Reproducibility

- `RANDOM_SEED = 42` — used by KMeans and the spring layout
- `REFERENCE_DATE = 2026-11-01` — nothing calls `date.today()`
- Deterministic JSON output ordering (sorted relations, sorted skills)

---

## Design decisions & scale thinking

See **`notes.md`** for:

- Design assumptions (why synthetic data, why fixed weights, why aliases)
- How a **crawler** would handle user-agent, headers, HTTP and rate limiting
- How **Redis Streams / Kafka** would queue the processing
- **Storage at scale** (object storage → Parquet → snapshots → serving layer)

---

