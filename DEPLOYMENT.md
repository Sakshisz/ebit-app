# 🚀 Deployment Guide - EBIT Kalkulator

## Deployment Alternativer

### ✅ **Alternativ 1: Docker Deployment (Anbefalt for produksjon)**

#### Steg 1: Test lokalt med Docker
```bash
# Bygg Docker image
docker-compose build

# Start applikasjon
docker-compose up -d

# Sjekk at det kjører
curl http://localhost:8000/health
open http://localhost:8501
```

#### Steg 2: Deploy til Cloud Provider

##### **A) Deploy til AWS (EC2 + Docker)**

1. **Opprett EC2 instans**
   ```bash
   # SSH inn til EC2
   ssh -i your-key.pem ubuntu@your-ec2-ip
   
   # Installer Docker og Docker Compose
   sudo apt update
   sudo apt install -y docker.io docker-compose
   sudo usermod -aG docker ubuntu
   ```

2. **Klon repository**
   ```bash
   git clone <your-repo-url>
   cd ebit-app
   ```

3. **Start applikasjon**
   ```bash
   docker-compose up -d
   ```

4. **Konfigurer Security Group**
   - Åpne port 8000 (Backend)
   - Åpne port 8501 (Frontend)

##### **B) Deploy til DigitalOcean App Platform**

1. **Forbered app.yaml**
   ```yaml
   name: ebit-app
   services:
   - name: backend
     github:
       repo: <your-github-repo>
       branch: main
       deploy_on_push: true
     build_command: pip install -r requirements.txt
     run_command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
     http_port: 8000
   
   - name: frontend
     github:
       repo: <your-github-repo>
       branch: main
       deploy_on_push: true
     build_command: pip install -r requirements.txt
     run_command: streamlit run frontend/Hovedside.py --server.port 8501
     http_port: 8501
   ```

2. **Deploy via CLI**
   ```bash
   doctl apps create --spec app.yaml
   ```

##### **C) Deploy til Render.com**

1. Gå til https://render.com
2. Klikk "New +" → "Web Service"
3. Koble til GitHub repository
4. Opprett to services:

   **Backend:**
   - Name: ebit-backend
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`

   **Frontend:**
   - Name: ebit-frontend
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `streamlit run frontend/Hovedside.py --server.port $PORT`

---

### ✅ **Alternativ 2: Streamlit Community Cloud (Gratis for frontend)**

#### Steg 1: Forbered backend separat

Backend må hostes separat (f.eks. Render, Railway, eller AWS Lambda)

**Deploy backend til Render.com:**
1. Gå til https://render.com
2. New Web Service → Koble GitHub
3. Settings:
   - Build: `pip install -r requirements.txt`
   - Start: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
4. Noter URL (f.eks. https://ebit-backend.onrender.com)

#### Steg 2: Deploy frontend til Streamlit Cloud

1. Gå til https://share.streamlit.io
2. Klikk "New app"
3. Velg repository: `<your-github-repo>`
4. Main file path: `frontend/Hovedside.py`
5. Legg til Secrets (Settings → Secrets):
   ```toml
   BACKEND_URL = "https://ebit-backend.onrender.com"
   ```

6. Oppdater `frontend/Hovedside.py`:
   ```python
   import os
   BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
   ```

---

### ✅ **Alternativ 3: Kubernetes (For større produksjonsmiljø)**

Se `k8s/` mappen for Kubernetes manifester.

---

## 📋 Pre-Deployment Sjekkliste

- [ ] Alle tester passerer (`pytest`)
- [ ] Sikkerhet: CORS konfigurert riktig
- [ ] Secrets: Sensitive data i environment variabler
- [ ] Database: Bruk persistent storage for `data/`
- [ ] Logging: Sett opp logging til CloudWatch/Datadog
- [ ] Monitoring: Health checks konfigurert
- [ ] Backup: Automatisk backup av data-filer

---

## 🔒 Produksjon Sikkerhet

### Oppdater CORS i backend/main.py:
```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://your-frontend-domain.com"],  # Ikke bruk "*"
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Bruk secrets for sensitive data:
```bash
# Eksempel på environment variabler
export DATABASE_URL=<your-db-url>
export SECRET_KEY=<your-secret>
export BACKEND_URL=<backend-url>
```

---

## 🔄 CI/CD Deployment

Oppdater `.github/workflows/ci.yml` for automatisk deployment:

```yaml
# Se deploy.yml for fullstendig eksempel
```

---

## 📊 Monitorering

### Health Checks
- Backend: `GET /health`
- Test: `curl https://your-backend.com/health`

### Logging
```bash
# Docker logs
docker-compose logs -f

# CloudWatch (AWS)
aws logs tail /aws/ecs/ebit-app --follow
```

---

## 🆘 Troubleshooting

**Problem: Frontend kan ikke nå backend**
- Sjekk at BACKEND_URL er satt riktig
- Verifiser CORS settings
- Test backend direkte: `curl <backend-url>/health`

**Problem: Data blir ikke lagret**
- Sjekk at `data/` katalogen er persistent
- Bruk volumes i Docker: `-v ./data:/app/data`

---

## 📞 Support

For spørsmål, opprett en issue i GitHub repository.
