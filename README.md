
# 💰 EBIT Kalkulator – Komplett guide (Lokal kjøring, testing og CI/CD)

Dette prosjektet er en **EBIT‑kalkulator** bygget med **Streamlit (frontend)** og **FastAPI (backend)**.
Den beregner inntekt, kostnad og EBIT per konsulent og prosjekt, med støtte for utnyttelsesgrad, prosjektbelastning, ferie/sykefravær og utlegg (prosent/manuelt), samt månedsvis filtrering.

---

## 📁 Prosjektstruktur

```
ebit-app/
├── backend/            # FastAPI backend + forretningslogikk
│   ├── __init__.py
│   ├── main.py
│   ├── calculations.py
│   └── data_access.py  # Laster JSON-data fra ./data
├── frontend/           # Streamlit-sider
│   ├── Hovedside.py
│   └── pages/
├── data/               # JSON-data (konsulenter, prosjekter, settings)
│   ├── consultants.json
│   ├── projects.json
│   └── settings.json
├── tests/              # Pytest: unit, API og integrasjon
│   ├── unit/
│   ├── api/
│   └── integration/
├── .github/workflows/  # CI (GitHub Actions)
│   └── ci.yml
├── requirements.txt
├── pytest.ini
└── README.md
```

---

## ✅ Forutsetninger

- **Python 3.11+**
- **pip**
- **git**

Sjekk versjoner:

```bash
python --version
pip --version
git --version
```

---

## 🚀 Kom i gang (lokalt)

### 1) Klon repo og gå til prosjektmappe
```bash
git clone <REPO_URL>
cd ebit-app
```

### 2) Opprett og aktiver virtuelt miljø
**macOS / Linux**
```bash
python -m venv venv
source venv/bin/activate
```
**Windows (PowerShell)**
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3) Installer avhengigheter
```bash
pip install -r requirements.txt
```

### 4) Sjekk datafiler
Sørg for at følgende finnes:
```
data/
├── consultants.json
├── projects.json
└── settings.json
```

### 5) Start backend (FastAPI)
Fra prosjektroten:
```bash
uvicorn backend.main:app --reload
```
Backend kjører på `http://localhost:8000`.
Test raskt i nettleser eller med curl:
```
http://localhost:8000/consultants
http://localhost:8000/projects
```

### 6) Start frontend (Streamlit)
Åpne **ny terminal** (med aktivert venv) og kjør:
```bash
streamlit run frontend/Hovedside.py
```
Frontend åpnes på `http://localhost:8501`.

---

## 🧪 Testing

Prosjektet bruker **pytest** med lagdelte tester:
- **Unit**: ren forretningslogikk (f.eks. `calculate_ebit`)  
- **API**: kontraktstester av FastAPI-endepunkt (`/calculate-ebit`, `/consultants`, `/projects`)  
- **Integrasjon**: lasting av JSON-data og enkle ende‑til‑ende‑kall

### Kjør alle tester
```bash
pytest
```

### Kjør med dekningsgrad (coverage)
```bash
pytest --cov=backend --cov-report=term-missing
```

### Generer testrapporter (HTML + JUnit + Coverage HTML)
```bash
pytest \
  --html=reports/test-report.html \
  --self-contained-html \
  --cov=backend \
  --cov-report=html:reports/coverage \
  --cov-report=xml:reports/coverage.xml \
  --junitxml=reports/junit.xml
```
Åpne rapporter lokalt (macOS):
```bash
open reports/test-report.html
open reports/coverage/index.html
```

> Tips: `pytest.ini` kan inneholde standardflagg slik at `pytest` alene genererer rapporter automatisk.

---

## 🧱 Nøkkelfiler for testbarhet

### `backend/calculations.py`
Inneholder ren logikk for EBIT, lett å enhetsteste.

### `backend/data_access.py`
Sentraliserer lasting av JSON-filer relativt til prosjektroten (`./data`).
Eksempel på public API:
```python
from backend.data_access import load_consultants, load_projects, load_settings
```
Dette sikrer at både API og tester bruker samme datakilde.

---

## 🔄 CI/CD (GitHub Actions)

Workflow finnes i `.github/workflows/ci.yml` og kjører:
- installasjon av avhengigheter
- alle tester med coverage
- opplasting av rapporter som artifacts (valgfritt)

Eksempel-steg for opplasting av rapporter (kan legges til):
```yaml
- name: Upload test reports
  uses: actions/upload-artifact@v4
  with:
    name: test-reports
    path: reports/
```

### Kjøre lokalt som i CI
Kjør kun:
```bash
pytest
```
(Forutsetter at `pytest.ini` er konfigurert med ønskede flagg.)

---

## 🧹 Vanlige problemer og løsninger

### Import‑feil eller rare NameError etter filendringer
Slett cache og kjør på nytt:
```bash
rm -rf __pycache__ .pytest_cache backend/__pycache__ tests/__pycache__
pytest
```

### Backend finner ikke data
- Sørg for at du kjører kommandoer fra **prosjektroten** (mappen som inneholder `backend/` og `data/`).
- Sjekk at `data/consultants.json` og `data/projects.json` finnes og er gyldig JSON.

### Streamlit oppdaterer ikke visningen
- Trykk **R** i Streamlit
- Evt. stopp og start `streamlit run` på nytt

### Git legger ved uønskede filer i commit
Legg til/oppdater `.gitignore`:
```
# macOS
.DS_Store

# Python
__pycache__/
*.pyc
*.pyo

# Pytest / coverage
.pytest_cache/
.coverage
coverage.xml
reports/

# Virtualenv
venv/
.env
```

---

## 🧭 Anbefalte videre steg
- Øk testdekningen og sett terskel i CI: `--cov-fail-under=80`
- Legg til `pre-commit` med `black`, `ruff` og `pytest`
- Dockeriser backend for konsistent kjøring i CI og lokalt
- Legg til negative/valideringstester på API‑payloads

---

## 📞 Kontakt / Bidrag
- Opprett en **issue** for feil/ønsker
- Lag **pull request** med beskrivelse av endringer

---

## ✨ Kort oppsummering (TL;DR)
1. `python -m venv venv && source venv/bin/activate`
2. `pip install -r requirements.txt`
3. `uvicorn backend.main:app --reload`
4. `streamlit run frontend/Hovedside.py`
5. `pytest` (ev. med coverage/rapporter)

God kjøring! 🚀
