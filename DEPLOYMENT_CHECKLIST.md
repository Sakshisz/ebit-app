# ✅ Deployment Checklist - EBIT Kalkulator

Bruk denne sjekklisten før hver deployment til produksjon.

---

## 📋 PRE-DEPLOYMENT

### Kode & Testing
- [ ] Alle tester passerer lokalt: `pytest`
- [ ] Koden er committed og pushet til GitHub
- [ ] CI/CD pipeline er grønn (sjekk Actions tab)
- [ ] Ingen merge conflicts på main branch

### Sikkerhet
- [ ] `.env` er IKKE committed til Git
- [ ] CORS settings er oppdatert i `backend/main.py`
- [ ] Sensitive data bruker environment variables
- [ ] GitHub Secrets er satt opp (se [GITHUB_SECRETS.md](GITHUB_SECRETS.md))

### Docker (hvis du bruker Docker)
- [ ] `docker-compose up` fungerer lokalt
- [ ] Healthcheck endepunkt `/health` returnerer 200 OK
- [ ] Data persister ved restart

---

## 🚀 DEPLOYMENT (Render.com)

### Backend Deployment
1. - [ ] Gå til https://dashboard.render.com
2. - [ ] Opprett ny Web Service
3. - [ ] Koble til GitHub repository
4. - [ ] Konfigurer:
   - **Name**: `ebit-backend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. - [ ] Legg til Environment Variable:
   - `ALLOWED_ORIGINS` = (frontend URL når den er klar)
6. - [ ] Deploy og noter URL: `https://ebit-backend.onrender.com`

### Frontend Deployment
1. - [ ] Opprett ny Web Service i Render
2. - [ ] Konfigurer:
   - **Name**: `ebit-frontend`
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `streamlit run frontend/Hovedside.py --server.port $PORT --server.address 0.0.0.0`
3. - [ ] Legg til Environment Variable:
   - `BACKEND_URL` = `https://ebit-backend.onrender.com`
4. - [ ] Deploy og noter URL: `https://ebit-frontend.onrender.com`

### Oppdater Backend CORS
5. - [ ] Gå tilbake til backend i Render
6. - [ ] Oppdater Environment Variable:
   - `ALLOWED_ORIGINS` = `https://ebit-frontend.onrender.com`
7. - [ ] Trigger redeploy

---

## 🧪 POST-DEPLOYMENT TESTING

### Backend Testing
- [ ] Test health endpoint: `curl https://ebit-backend.onrender.com/health`
- [ ] Test consultants endpoint: `curl https://ebit-backend.onrender.com/consultants`
- [ ] Test projects endpoint: `curl https://ebit-backend.onrender.com/projects`
- [ ] Sjekk logs for feil i Render dashboard

### Frontend Testing
- [ ] Åpne frontend URL i nettleser
- [ ] Verifiser at konsulenter lastes
- [ ] Verifiser at prosjekter lastes
- [ ] Test EBIT kalkulator med test-data
- [ ] Sjekk browser console for CORS errors (skal være ingen)

### Integration Testing
- [ ] Test full workflow: legg til konsulent → legg til prosjekt → beregn EBIT
- [ ] Test alle sider i sidemenyen
- [ ] Test på mobil/tablet (responsive design)

---

## 📊 MONITORING

### Første 24 timer
- [ ] Sjekk Render logs hver 2. time
- [ ] Overvåk response times
- [ ] Se etter crashes eller errors
- [ ] Test at auto-restart fungerer (hvis app crasher)

### Ongoing
- [ ] Sett opp Uptime monitoring (f.eks. UptimeRobot)
- [ ] Konfigurer alerts for downtime
- [ ] Sjekk logs ukentlig

---

## 🔄 CI/CD SETUP (Valgfritt)

For automatisk deployment ved hver push til main:

1. - [ ] Sett opp GitHub Secrets (se [GITHUB_SECRETS.md](GITHUB_SECRETS.md))
2. - [ ] Verifiser `.github/workflows/deploy.yml` er korrekt
3. - [ ] Test med en liten endring:
   ```bash
   git commit -m "Test CI/CD" --allow-empty
   git push origin main
   ```
4. - [ ] Sjekk at deployment kjører i GitHub Actions tab

---

## 🔐 SECURITY CHECKLIST

- [ ] API keys lagret kun i GitHub Secrets
- [ ] CORS settings begrenser til kun frontend URL
- [ ] Ingen hardkodet passord eller tokens i kode
- [ ] HTTPS aktivert (Render gjør dette automatisk)
- [ ] Rate limiting vurdert (hvis nødvendig)

---

## 📝 POST-DEPLOYMENT

- [ ] Oppdater README.md med production URLs
- [ ] Dokumenter deployment-dato og versjon
- [ ] Informer team om ny production URL
- [ ] Ta backup av data-filer

---

## 🆘 ROLLBACK PLAN

Hvis noe går galt i produksjon:

1. **Via Render Dashboard:**
   - Gå til servicen → "Events" tab
   - Klikk "Rollback" på forrige vellykket deployment

2. **Via Git:**
   ```bash
   git revert HEAD
   git push origin main
   ```

3. **Emergency:**
   - Pause auto-deployment i Render
   - Fix issues lokalt
   - Test grundig
   - Deploy manuelt

---

## ✨ FERDIG!

Gratulerer! 🎉 Applikasjonen er nå live i produksjon.

**Production URLs:**
- Backend: `https://ebit-backend.onrender.com`
- Frontend: `https://ebit-frontend.onrender.com`

**Neste steg:**
- Del URL med brukere
- Samle feedback
- Planlegg neste features

---

**Dato for deployment:** _______________
**Deployed av:** _______________
**Versjon/Commit:** _______________
