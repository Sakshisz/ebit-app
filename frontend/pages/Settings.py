
# pages/1_Settings.py
import streamlit as st
import pandas as pd
import io
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="Innstillinger", page_icon="⚙️", layout="wide")
st.title("⚙️ Innstillinger")


def get_settings():
    try:
        r = requests.get(f"{BACKEND_URL}/settings", timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Kunne ikke hente innstillinger: {e}")
        return {"pex_pct": 0.32, "expense_pct": 0.40, "yearly_work_hours": 1625}


settings = get_settings()

st.header("Standard parametre")
col1, col2, col3 = st.columns(3)
with col1:
    pex = st.number_input("PEX (andel 0–1)", min_value=0.0,
                          max_value=1.0, value=float(settings["pex_pct"]), step=0.01)
with col2:
    expense = st.number_input("Utlegg (andel 0–1)", min_value=0.0,
                              max_value=1.0, value=float(settings["expense_pct"]), step=0.01)
with col3:
    work_hours = st.number_input("Årlige arbeidstimer", min_value=500, max_value=3000, value=int(
        settings["yearly_work_hours"]), step=25)

if st.button("Lagre innstillinger"):
    try:
        r = requests.post(f"{BACKEND_URL}/settings", json={
            "pex_pct": pex, "expense_pct": expense, "yearly_work_hours": work_hours
        }, timeout=10)
        r.raise_for_status()
        st.success("Innstillinger lagret.")
    except Exception as e:
        st.error(f"Feil ved lagring: {e}")

st.divider()

st.subheader("Malfiler (CSV)")
cons_template = pd.DataFrame({
    "Name": ["Ola Nordmann", "Kari Nordmann"],
    "Salary": [800000, 750000],
    "DefaultUtilization": [0.85, 0.80],
})
proj_template = pd.DataFrame({
    "Name": ["Prosjekt Alpha", "Prosjekt Beta"],
    "HourlyRate": [1400, 1200],
})

cbuf = io.StringIO()
cons_template.to_csv(cbuf, index=False)
pbuf = io.StringIO()
proj_template.to_csv(pbuf, index=False)

cc1, cc2 = st.columns(2)
with cc1:
    st.download_button("Last ned konsulent-mal (CSV)", data=cbuf.getvalue(),
                       file_name="Consultants_template.csv", mime="text/csv")
with cc2:
    st.download_button("Last ned prosjekt-mal (CSV)", data=pbuf.getvalue(),
                       file_name="Projects_template.csv", mime="text/csv")

st.divider()

if st.button("Importer eksempeldata (seed)"):
    try:
        r = requests.post(f"{BACKEND_URL}/seed", timeout=20)
        r.raise_for_status()
        st.success("Eksempeldata for konsulenter og prosjekter ble lagt inn.")
    except Exception as e:
        st.error(f"Feil ved seed: {e}")

st.divider()

st.header("Last opp data")
tab1, tab2 = st.tabs(["Konsulenter (CSV/XLSX)", "Prosjekter (CSV/XLSX)"])

with tab1:
    st.caption(
        "Forventede kolonner: `Name`, `Salary`, valgfritt `DefaultUtilization`")
    cons_file = st.file_uploader(
        "Last opp konsulent-fil", type=["csv", "xlsx"], key="cons_file")
    if cons_file:
        try:
            cdf = pd.read_csv(cons_file) if cons_file.name.endswith(
                ".csv") else pd.read_excel(cons_file)
            st.write("Forhåndsvisning (topp 20 rader):")
            st.dataframe(cdf.head(20))
            if st.button("Importer konsulenter"):
                items = []
                for _, row in cdf.iterrows():
                    items.append({
                        "name": str(row["Name"]),
                        "salary": float(row["Salary"]),
                        "default_utilization": float(row["DefaultUtilization"]) if "DefaultUtilization" in row and not pd.isna(row["DefaultUtilization"]) else 0.8
                    })
                r = requests.post(
                    f"{BACKEND_URL}/consultants/bulk", json={"items": items}, timeout=30)
                r.raise_for_status()
                st.success(f"Importert {len(items)} konsulent(er).")
        except Exception as e:
            st.error(f"Feil ved opplasting/import av konsulenter: {e}")

with tab2:
    st.caption("Forventede kolonner: `Name`, `HourlyRate`")
    proj_file = st.file_uploader(
        "Last opp prosjekt-fil", type=["csv", "xlsx"], key="proj_file")
    if proj_file:
        try:
            pdf = pd.read_csv(proj_file) if proj_file.name.endswith(
                ".csv") else pd.read_excel(proj_file)
            st.write("Forhåndsvisning (topp 20 rader):")
            st.dataframe(pdf.head(20))
            if st.button("Importer prosjekter"):
                items = []
                for _, row in pdf.iterrows():
                    items.append(
                        {"name": str(row["Name"]), "hourly_rate": float(row["HourlyRate"])})
                r = requests.post(f"{BACKEND_URL}/projects/bulk",
                                  json={"items": items}, timeout=30)
                r.raise_for_status()
                st.success(f"Importert {len(items)} prosjekt(er).")
        except Exception as e:
            st.error(f"Feil ved opplasting/import av prosjekter: {e}")
