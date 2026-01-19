
# app.py
import streamlit as st
import requests

BACKEND_URL = "http://localhost:8000"

st.set_page_config(page_title="EBIT Kalkulator", page_icon="💰", layout="wide")
st.title("💰 EBIT Kalkulator – Hovedside (med dropdowns)")

st.write(
    "Velg konsulent og prosjekt via nedtrekkslister. "
    "Lønn og timepris hentes automatisk fra registrerte data. "
    "Bruk sidemenyen for å registrere konsulenter/prosjekter og justere innstillinger."
)


def fetch_consultants():
    try:
        r = requests.get(f"{BACKEND_URL}/consultants", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Feil ved henting av konsulenter: {e}")
        return []


def fetch_projects():
    try:
        r = requests.get(f"{BACKEND_URL}/projects", timeout=5)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"Feil ved henting av prosjekter: {e}")
        return []


consultants = fetch_consultants()
projects = fetch_projects()

if not consultants:
    st.warning(
        "Ingen konsulenter funnet. Gå til **'Konsulenter'**-siden og legg dem inn.")
if not projects:
    st.warning(
        "Ingen prosjekter funnet. Gå til **'Prosjekter'**-siden og legg dem inn.")
if not consultants or not projects:
    st.stop()

consultant_options = {f"{c['name']} (#{c['id']})": c['id']
                      for c in consultants}
project_options = {
    f"{p['name']} (#{p['id']}) – {int(p['hourly_rate'])} kr/t": p['id'] for p in projects}
consultant_by_id = {c["id"]: c for c in consultants}
project_by_id = {p["id"]: p for p in projects}

num_rows = st.number_input(
    "Antall rader (konsulent-prosjekt-kombinasjoner)", 1, 25, 5)
assignments = []

st.header("Valg per rad")
for i in range(num_rows):
    with st.expander(f"Rad {i+1}", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            consul_label = st.selectbox("Konsulent", options=list(
                consultant_options.keys()), key=f"consultant_{i}")
            consul_id = consultant_options[consul_label]
            consul = consultant_by_id[consul_id]
            st.caption(
                f"Årslønn: **{int(consul['salary']):,} kr**".replace(",", " "))

        with col2:
            proj_label = st.selectbox("Prosjekt", options=list(
                project_options.keys()), key=f"project_{i}")
            proj_id = project_options[proj_label]
            proj = project_by_id[proj_id]
            st.caption(
                f"Timepris: **{int(proj['hourly_rate']):,} kr**".replace(",", " "))

        util = st.slider("Utnyttelsesgrad (%)", 0.0, 1.0, consul.get(
            "default_utilization", 0.8), key=f"util_{i}")
        project_percent = st.slider(
            "Prosjektbelastning (%)", 0.0, 1.0, 1.0, key=f"proj_pct_{i}")

        assignments.append({
            "consultant_id": consul_id,
            "project_id": proj_id,
            "utilization": util,
            "project_percent": project_percent
        })

left, right = st.columns([1, 1])
with left:
    yearly_hours = st.number_input(
        "Årlige arbeidstimer", min_value=1000, max_value=2200, value=1625)
with right:
    pex = st.number_input("PEX (%)", min_value=0.0,
                          max_value=1.0, value=0.32, help="Sosiale kostnader")
    expense = st.number_input(
        "Utlegg (%)", min_value=0.0, max_value=1.0, value=0.40)

if st.button("Beregn EBIT"):
    payload = {
        "assignments": assignments,
        "yearly_work_hours": yearly_hours,
        "pex_pct": pex,
        "expense_pct": expense
    }
    try:
        r = requests.post(f"{BACKEND_URL}/calculate-ebit",
                          json=payload, timeout=20)
        r.raise_for_status()
        data = r.json()

        st.success("Beregning fullført")
        st.write("## Resultater per rad")
        for row in data["results"]:
            st.write(
                f"**{row['consultant_name']}** → **{row['project_name']}** | "
                f"Inntekt: {row['income']:.0f} kr | Kostnad: {row['cost']:.0f} kr | "
                f"EBIT: **{row['ebit']:.0f} kr**"
            )

        dept = data["department"]
        st.write("---")
        st.subheader("Totalt – Avdeling")
        st.write(
            f"Inntekt: **{dept['income']:.0f} kr**, Kostnad: **{dept['cost']:.0f} kr**, EBIT: **{dept['ebit']:.0f} kr**")

        try:
            import plotly.graph_objects as go
            fig = go.Figure()
            fig.add_bar(x=["Total EBIT", "Total Kostnad", "Total Inntekt"],
                        y=[dept["ebit"], dept["cost"], dept["income"]],
                        marker_color=["green", "red", "blue"])
            fig.update_layout(title="EBIT vs Kostnad vs Inntekt",
                              yaxis_title="Beløp (NOK)")
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            st.info("Installer Plotly for graf: `pip install plotly`")

    except Exception as e:
        st.error(f"Feil ved beregning: {e}")
