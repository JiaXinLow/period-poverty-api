# Period Poverty API

A FastAPI service that analyses the affordability of menstrual hygiene in the UK using **CPI (personal care)**, **World Bank PIP percentiles**, and a **JMP hygiene proxy**.  
It exposes **dataset** and **analytics** endpoints and includes a full **CRUD** model to meet marking requirements.

---

## ✨ Features

- **CRUD**: `BasketItem` (Create / Read / Update / Delete) — used by analytics
- **Datasets (read-only)**
  - ONS CPI personal care monthly index (2015=100)
  - World Bank PIP percentiles (UK, PPP-adjusted daily welfare)
  - WHO/UNICEF JMP hygiene proxy (UK bathing facility, 2018)
- **Analytics**
  - Inflation trend (CPI personal care)
  - Basket cost estimate (from DB or custom payload; optional YoY CPI uplift)
  - Cost burden (annual basket cost vs PIP annual welfare)
  - Severity score (affordability ⊕ hygiene access)
- **Auto docs** at `/docs` (Swagger/OpenAPI)
- **Docs artifacts** in `docs/` (Swagger PDF, OpenAPI JSON, Postman collection)

---

## 🧠 Tech Stack & Rationale

- **FastAPI** — Pythonic typing + auto OpenAPI (great for small research APIs)
- **SQLite + SQLAlchemy** — simple, portable DB for marking, zero external infra
- **Pydantic v2** — robust request/response validation (`from_attributes=True`)
- **Pandas** — used in notebooks for data cleaning to `data/processed/`

---

## Project Structure
period-poverty-api/
├── app/
│   ├── main.py                 # app entry, mounts routers, health route
│   ├── database.py             # SQLite engine, session, Base
│   ├── models.py               # SQLAlchemy models
│   ├── schemas.py              # Pydantic v2 schemas (+ OpenAPI examples)
│   └── routers/
│       ├── basket.py           # BasketItem CRUD
│       ├── price_index.py      # /v1/price-index
│       ├── pip.py              # /v1/pip/uk/{year}
│       ├── hygiene.py          # /v1/hygiene/uk
│       └── analytics.py        # /v1/analytics/* endpoints
├── data/
│   ├── raw/                    # (ignored) raw downloads
│   └── processed/              # cleaned CSVs used for seeding
├── docs/
│   ├── api_docs.pdf            # exported Swagger UI (print-to-PDF)
│   ├── openapi.json            # exported OpenAPI (optional)
│   └── postman_collection.json # ready-to-import Postman collection
├── notebooks/
│   ├── 01_clean_cpi.ipynb
│   ├── 02_clean_pip.ipynb
│   └── 03_clean_jmp.ipynb
├── seed_data.py                # load data/processed/* into SQLite
├── period_poverty.db           # (created by seed/first run)
├── requirements.txt            # pinned runtime deps (recommended)
└── README.md 

---

## Quick Start

### 1) Create venv & install
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

# Install from requirements (preferred) or minimal stack:
pip install -r requirements.txt
# or:
pip install fastapi "uvicorn[standard]" sqlalchemy pandas pydantic