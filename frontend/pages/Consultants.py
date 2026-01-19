
# pages/2_Consultants.py
import streamlit as st
import requests
import pandas as pd

BACKEND_URL = "http://localhost:8000"
st.set_page_config(page_title="Konsulenter", page_icon="👤", layout="wide")
st.title("👤 Konsulenter")


def rerun():
    try:
        st.rerun()
    except Exception:
        st.experimental_rerun()


# --- Opprett én konsulent ---
st.subheader("Legg til konsulent manuelt")
with st.form("add_consultant"):
    name = st.text_input("Navn")
    salary = st.number_input("Årslønn (kr)", min_value=0, value=700000)
    default_util = st.slider("Standard utnyttelsesgrad", 0.0, 1.0, 0.8)
    submitted = st.form_submit_button("Lagre")
    if submitted:
        try:
            r = requests.post(f"{BACKEND_URL}/consultants", json={
                "name": name, "salary": salary, "default_utilization": default_util
            }, timeout=10)
            r.raise_for_status()
            st.success(f"Konsulent '{name}' lagret.")
            rerun()
        except Exception as e:
            st.error(f"Feil: {e}")

# --- Masseimport ---
st.subheader("Masseimport (CSV/Excel)")
st.caption("Kolonner: `Name`, `Salary`, (valgfritt) `DefaultUtilization`")
file = st.file_uploader("Last opp CSV/XLSX", type=["csv", "xlsx"])
if file is not None:
    try:
        df = pd.read_csv(file) if file.name.endswith(
            ".csv") else pd.read_excel(file)
        st.dataframe(df.head(20))
        if st.button("Importer konsulenter"):
            items = []
            for _, row in df.iterrows():
                items.append({
                    "name": str(row["Name"]),
                    "salary": float(row["Salary"]),
                    "default_utilization": float(row.get("DefaultUtilization", 0.8))
                })
            r = requests.post(f"{BACKEND_URL}/consultants/bulk",
                              json={"items": items}, timeout=30)
            r.raise_for_status()
            st.success(f"Importert {len(items)} konsulent(er).")
            rerun()
    except Exception as e:
        st.error(f"Feil ved import: {e}")

st.divider()

# --- Generer testdata 5–25 ---
st.subheader("Generer testdata")
c1, c2, c3 = st.columns([1, 1, 2])
with c1:
    count = st.slider("Antall (5–25)", 5, 25, 10)
with c2:
    reset = st.checkbox("Reset før generering", value=False)
with c3:
    if st.button("Generer konsulenter"):
        try:
            r = requests.post(f"{BACKEND_URL}/seed/consultants",
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
st.subheader("Registrerte konsulenter")
try:
    r = requests.get(f"{BACKEND_URL}/consultants", timeout=10)
    r.raise_for_status()
    data = r.json()
    if not data:
        st.info("Ingen konsulenter registrert enda.")
    else:
        for item in data:
            with st.expander(f"{item['name']} (#{item['id']})", expanded=False):
                col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
                with col1:
                    new_name = st.text_input(
                        "Navn", value=item["name"], key=f"c_name_{item['id']}")
                with col2:
                    new_salary = st.number_input("Årslønn (kr)", min_value=0, value=int(
                        item["salary"]), key=f"c_sal_{item['id']}")
                with col3:
                    new_util = st.slider("Utnyttelse", 0.0, 1.0, float(
                        item.get("default_utilization", 0.8)), key=f"c_util_{item['id']}")
                with col4:
                    if st.button("Oppdater", key=f"c_upd_{item['id']}"):
                        try:
                            r = requests.patch(f"{BACKEND_URL}/consultants/{item['id']}", json={
                                "name": new_name,
                                "salary": new_salary,
                                "default_utilization": new_util
                            }, timeout=10)
                            r.raise_for_status()
                            st.success("Oppdatert.")
                            rerun()
                        except Exception as e:
                            st.error(f"Feil ved oppdatering: {e}")
                d1, d2 = st.columns([1, 3])
                with d1:
                    confirm = st.checkbox(
                        "Bekreft sletting", key=f"c_conf_{item['id']}")
                with d2:
                    if st.button("Slett", key=f"c_del_{item['id']}"):
                        if not confirm:
                            st.warning("Huk av 'Bekreft sletting' først.")
                        else:
                            try:
                                r = requests.delete(
                                    f"{BACKEND_URL}/consultants/{item['id']}", timeout=10)
                                r.raise_for_status()
                                st.success("Slettet.")
                                rerun()
                            except Exception as e:
                                st.error(f"Feil ved sletting: {e}")
except Exception as e:
    st.error(f"Feil: {e}")
