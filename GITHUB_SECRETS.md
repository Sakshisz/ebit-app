# 🔐 GitHub Secrets Setup Guide

## Hvorfor trenger vi GitHub Secrets?

GitHub Secrets lar deg lagre sensitiv informasjon (API keys, tokens, URLs) trygt i GitHub, slik at de kan brukes i CI/CD workflows uten å eksponere dem i koden.

---

## 📋 Secrets du trenger å sette opp

### **For Render.com Deployment:**

1. **RENDER_API_KEY**
   - Hva: Din Render API key for automatisk deployment
   - Hvordan få den:
     1. Gå til https://dashboard.render.com
     2. Klikk på profilikonet → Account Settings
     3. Gå til "API Keys"
     4. Klikk "Create API Key"
     5. Gi den et navn (f.eks. "GitHub Actions")
     6. Kopier nøkkelen

2. **RENDER_BACKEND_SERVICE_ID**
   - Hva: Service ID for backend-tjenesten
   - Hvordan få den:
     1. Gå til backend-servicen i Render dashboard
     2. URL vil se slik ut: `https://dashboard.render.com/web/srv-XXXXXXXXXXXX`
     3. `srv-XXXXXXXXXXXX` er din SERVICE_ID

3. **RENDER_FRONTEND_SERVICE_ID** (valgfritt)
   - Samme prosess som backend, men for frontend-tjenesten

---

### **For Docker Hub Deployment:**

4. **DOCKER_USERNAME**
   - Hva: Ditt Docker Hub brukernavn
   - Hvordan få den: Se på https://hub.docker.com

5. **DOCKER_PASSWORD**
   - Hva: Docker Hub access token (IKKE passord)
   - Hvordan få den:
     1. Gå til https://hub.docker.com
     2. Klikk på brukernavnet → Account Settings → Security
     3. Klikk "New Access Token"
     4. Navn: "GitHub Actions"
     5. Kopier token (vises kun én gang!)

---

### **For EC2 Deployment (valgfritt):**

6. **EC2_HOST**
   - Hva: Din EC2 public IP eller hostname
   - Eksempel: `ec2-12-34-56-78.compute-1.amazonaws.com`

7. **EC2_USER**
   - Hva: SSH brukernavn (vanligvis `ubuntu` eller `ec2-user`)
   - Eksempel: `ubuntu`

8. **EC2_SSH_KEY**
   - Hva: Privat SSH key for å koble til EC2
   - Hvordan få den:
     1. Åpne din `.pem` fil lokalt
     2. Kopier hele innholdet (inkludert `-----BEGIN` og `-----END` linjer)

---

## 🔧 Hvordan legge til Secrets i GitHub

### Steg 1: Gå til GitHub repository
1. Åpne https://github.com/[DIN-BRUKER]/ebit-app
2. Klikk på "Settings" (øverst i menyen)

### Steg 2: Legg til Secrets
1. I venstre meny: klikk "Secrets and variables" → "Actions"
2. Klikk "New repository secret"
3. For hver secret:
   - **Name**: Skriv navnet (f.eks. `RENDER_API_KEY`)
   - **Value**: Lim inn verdien
   - Klikk "Add secret"

### Steg 3: Gjenta for alle secrets
Legg til alle secrets fra listen ovenfor som er relevant for din deployment-strategi.

---

## ✅ Verifiser at Secrets er satt opp

### I GitHub:
1. Gå til Settings → Secrets and variables → Actions
2. Du skal se alle secrets listet (verdiene er skjult)

### Test deployment:
```bash
# Push en endring til main branch
git add .
git commit -m "Test deployment"
git push origin main
```

Gå til "Actions" tab i GitHub for å se deployment-prosessen.

---

## 🔒 Sikkerhetstips

1. **ALDRI commit secrets til git**
   - Sjekk at `.env` er i `.gitignore`
   - Bruk `.env.example` for å vise struktur uten verdier

2. **Roter secrets regelmessig**
   - Spesielt API keys og tokens

3. **Bruk minst privilegerte tilganger**
   - Gi kun de tilgangene som trengs

4. **Overvåk secret-bruk**
   - Sjekk GitHub Actions logs for mistenkelig aktivitet

---

## 📝 Environment Variables i Produksjon

### For Render.com:
1. Gå til din service i Render dashboard
2. Klikk "Environment" tab
3. Legg til:
   - **For Backend:**
     ```
     ALLOWED_ORIGINS=https://your-frontend.onrender.com
     ```
   
   - **For Frontend:**
     ```
     BACKEND_URL=https://your-backend.onrender.com
     ```

### For Streamlit Cloud:
1. Gå til app settings
2. Klikk "Secrets"
3. Legg til i TOML format:
   ```toml
   BACKEND_URL = "https://your-backend.onrender.com"
   ```

---

## 🆘 Troubleshooting

**Problem: "Secret not found" error i Actions**
- Sjekk at secret-navnet matcher NØYAKTIG (case-sensitive)
- Verifiser at secret er lagt til i repository (ikke organization)

**Problem: Deployment feiler med "Unauthorized"**
- Sjekk at API key/token er gyldig
- Verifiser at token har riktige permissions

**Problem: CORS errors i produksjon**
- Sjekk at `ALLOWED_ORIGINS` inneholder frontend URL
- Husk å inkludere protokoll (https://)
- Ingen trailing slash

---

## 📞 Neste steg

1. ✅ Sett opp alle relevante secrets i GitHub
2. ✅ Push kode til main branch
3. ✅ Verifiser at CI/CD kjører i "Actions" tab
4. ✅ Test applikasjonen i produksjon

For spørsmål, se [DEPLOYMENT.md](DEPLOYMENT.md)
