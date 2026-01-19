
# pages/3_Projects.py
import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="Prosjekter", page_icon="📁", layout="wide")
st.title("📁 Prosjekter")


def rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


# --- Opprett ett prosjekt ---
st.subheader("Legg til prosjekt manuelt")
with st.form("add_project"):
    name = st.text_input("Prosjektnavn")
    hourly_rate = st.number_input("Timepris (kr)", min_value=0, value=1200)
    submitted = st.form_submit_button("Lagre")
    if submitted:
        try:
            r = requests.post(
                f"{BACKEND_URL}/projects", json={"name": name, "hourly_rate": hourly_rate}, timeout=10)
            r.raise_for_status()
            st.success(f"Prosjekt '{name}' lagret.")
            rerun()
        except Exception as e:
            st.error(f"Feil: {e}")

# --- Masseimport ---
st.subheader("Masseimport (CSV/Excel)")
st.caption("Kolonner: `Name`, `HourlyRate`")
file = st.file_uploader("Last opp CSV/XLSX", type=["csv", "xlsx"])
if file is not None:
    try:
        df = pd.read_csv(file) if file.name.endswith(
            ".csv") else pd.read_excel(file)
        st.dataframe(df.head(20))
        if st.button("Importer prosjekter"):
            items = []
            for _, row in df.iterrows():
                items.append(
                    {"name": str(row["Name"]), "hourly_rate": float(row["HourlyRate"])})
            r = requests.post(f"{BACKEND_URL}/projects/bulk",
                              json={"items": items}, timeout=30)
            r.raise_for_status()
            st.success(f"Importert {len(items)} prosjekt(er).")
            rerun()
    except Exception as e:
        st.error(f"Feil ved import: {e}")

st.divider()

# --- Generer testdata 5–25 ---
st.subheader("Generer testdata")
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    count = st.slider("Antall (5–25)", 5, 25, 10, key="p_count")
with c2:
    reset = st.checkbox("Reset før generering", value=False, key="p_reset")
with c3:
    if st.button("Generer prosjekter"):
        try:
            r = requests.post(f"{BACKEND_URL}/seed/projects",
                              params={"count": count, "reset": reset}, timeout=20)
            r.raise_for_status()
            info = r.json()
            st.success(
                f"La til {info['added']} – totalt {info['total']} (reset={info['reset']}).")
            rerun()
        except Exception as e:
            st.error(f"Feil ved generering: {e}")

st.divider()

# --- Liste + Rediger/Slett ---
st.subheader("Registrerte prosjekter")
try:
    r = requests.get(f"{BACKEND_URL}/projects", timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        st.info("Ingen prosjekter registrert enda.")
    else:
        for item in data:
            with st.expander(f"{item['name']} (#{item['id']})", expanded=False):
                col1, col2, col3 = st.columns([2, 1, 1])
                with col1:
                    new_name = st.text_input(
                        "Prosjektnavn", value=item["name"], key=f"p_name_{item['id']}")
                with col2:
                    new_rate = st.number_input("Timepris (kr)", min_value=0, value=int(
                        item["hourly_rate"]), key=f"p_rate_{item['id']}")
                with col3:
                    if st.button("Oppdater", key=f"p_upd_{item['id']}"):
                        try:
                            r = requests.patch(f"{BACKEND_URL}/projects/{item['id']}", json={
                                "name": new_name, "hourly_rate": new_rate
                            }, timeout=10)
                            r.raise_for_status()
                            st.success("Oppdatert.")
                            rerun()
                        except Exception as e:
                            st.error(f"Feil ved oppdatering: {e}")
                d1, d2 = st.columns([1, 3])
                with d1:
                    confirm = st.checkbox(
                        "Bekreft sletting", key=f"p_conf_{item['id']}")
                with d2:
                    if st.button("Slett", key=f"p_del_{item['id']}"):
                        if not confirm:
                            st.warning("Huk av 'Bekreft sletting' først.")
                        else:
                            try:
                                r = requests.delete(
                                    f"{BACKEND_URL}/projects/{item['id']}", timeout=10)
                                r.raise_for_status()
                                st.success("Slettet.")
                                rerun()
                            except Exception as e:
                                st.error(f"Feil ved sletting: {e}")
except Exception as e:
    st.error(f"Feil: {e}")
