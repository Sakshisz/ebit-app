
# pages/EBIT_Trends.py
import streamlit as st
import requests
import pandas as pd
import datetime
from datetime import date, timedelta

BACKEND_URL = "http://localhost:8000"

# Backend EBIT includes utlegg (same as main app.py)
BACKEND_EBIT_INCLUDES_UTLEGG = False

# ---- Plotly: robust import (app feiler ikke hvis plotly mangler) ----
try:
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except Exception:
    go = None  # type: ignore
    PLOTLY_AVAILABLE = False

# ---- Kompakt standardhøyde for grafer ----
CHART_HEIGHT = 360

# ---- Arbeidsdager (man–fre) for måned/år: enkel norsk kalender uten røddager ----


def business_days_in_month(year: int, month: int) -> int:
    """Antall arbeidsdager (man–fre) i gitt måned/år (uten røddager)."""
    first_day = date(year, month, 1)
    if month == 12:
        last_day = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        last_day = date(year, month + 1, 1) - timedelta(days=1)
    total = (last_day - first_day).days + 1
    return sum(1 for d in range(total) if (first_day + timedelta(days=d)).weekday() < 5)


def business_days_in_year(year: int) -> int:
    """Antall arbeidsdager (man–fre) i hele året (uten røddager)."""
    return sum(business_days_in_month(year, m) for m in range(1, 13))


st.set_page_config(page_title="EBIT Trends", page_icon="📈", layout="wide")
st.title("📈 EBIT Trends – Månedlig utvikling")

st.write(
    "Analyser EBIT-utvikling måned for måned basert på data fra hovedsiden. "
    "Filtrer etter konsulent eller prosjekt og se trender over tid."
)

# ========== Cache helpers ==========


@st.cache_data(ttl=60)
def fetch_consultants():
    r = requests.get(f"{BACKEND_URL}/consultants", timeout=10)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def fetch_projects():
    r = requests.get(f"{BACKEND_URL}/projects", timeout=10)
    r.raise_for_status()
    return r.json()


@st.cache_data(ttl=60)
def fetch_settings():
    r = requests.get(f"{BACKEND_URL}/settings", timeout=10)
    r.raise_for_status()
    return r.json()


# ========== Fetch data ==========
try:
    consultants = fetch_consultants()
except Exception as e:
    st.error(f"Feil ved henting av konsulenter: {e}")
    st.stop()

try:
    projects = fetch_projects()
except Exception as e:
    st.error(f"Feil ved henting av prosjekter: {e}")
    st.stop()

try:
    settings = fetch_settings()
except Exception:
    st.warning("Kunne ikke hente innstillinger, bruker defaults")
    settings = {"pex_pct": 0.32, "expense_pct": 0.40,
                "yearly_work_hours": 1625}

if not consultants:
    st.warning(
        "Ingen konsulenter funnet. Gå til **'Konsulenter'**-siden for å legge inn.")
    st.stop()

if not projects:
    st.warning(
        "Ingen prosjekter funnet. Gå til **'Prosjekter'**-siden for å legge inn.")
    st.stop()

consultant_by_id = {c["id"]: c for c in consultants}
project_by_id = {p["id"]: p for p in projects}

st.info(
    "💡 **Bruk:** Gå til **Hovedsiden**, lag konsulent/prosjekt-rader med \"Fra til\" datoer, "
    "og velg deretter hvilke måneders trend du vil se her. Data blir automatisk hentet fra hovedsiden."
)

# ========== Check if data exists from Hovedside ==========
if "rows" not in st.session_state or not st.session_state.rows:
    st.warning(
        "📌 Ingen data fra hovedsiden. Gå til **Hovedside**, legg inn konsulent/prosjekt-rader med datoer, "
        "og kom tilbake til denne siden for å analysere trend."
    )
    st.stop()

hovedside_rows = st.session_state.rows
hovedside_manual_expenses = st.session_state.get("manual_expenses", [])

# Initialize results storage
if "ebit_trends_results" not in st.session_state:
    st.session_state.ebit_trends_results = None

# ========== UI: Time period ==========
st.subheader("1. Velg tidsperiode")

col1, col2, col3 = st.columns(3)

months_list = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember"
]

with col1:
    start_month = st.selectbox(
        "Start måned", options=months_list, index=0, key="start_month")

with col2:
    end_month = st.selectbox(
        "Slutt måned", options=months_list, index=11, key="end_month")

with col3:
    year = st.number_input("År", min_value=2020,
                           max_value=2030, value=datetime.date.today().year)

# ========== UI: Filter consultants and projects ==========
st.subheader("2. Velg filterkriteria")

col1, col2 = st.columns(2)

# Get unique consultants and projects from hovedside
if hovedside_rows:
    unique_consultant_ids = list(
        set([r.get("consultant_id") for r in hovedside_rows]))
    unique_project_ids = list(
        set([r.get("project_id") for r in hovedside_rows]))

    available_consultant_names = sorted([
        consultant_by_id[cid]["name"] for cid in unique_consultant_ids if cid in consultant_by_id
    ])
    available_project_names = sorted([
        project_by_id[pid]["name"] for pid in unique_project_ids if pid in project_by_id
    ])
else:
    available_consultant_names, available_project_names = [], []

with col1:
    consultant_names_options = ["Alle"] + available_consultant_names
    selected_consultants = st.multiselect(
        "Konsulenter", options=consultant_names_options, default=["Alle"], key="selected_consultants"
    )

with col2:
    project_names_options = ["Alle"] + available_project_names
    selected_projects = st.multiselect(
        "Prosjekter", options=project_names_options, default=["Alle"], key="selected_projects"
    )

# Resolve selected to IDs
if "Alle" in selected_consultants:
    filtered_consultant_ids = unique_consultant_ids if hovedside_rows else []
else:
    filtered_consultant_ids = [
        cid for cid in unique_consultant_ids
        if consultant_by_id.get(cid, {}).get("name") in selected_consultants
    ] if hovedside_rows else []

if "Alle" in selected_projects:
    filtered_project_ids = unique_project_ids if hovedside_rows else []
else:
    filtered_project_ids = [
        pid for pid in unique_project_ids
        if project_by_id.get(pid, {}).get("name") in selected_projects
    ] if hovedside_rows else []

# ========== Load settings from backend ==========
yearly_hours = float(settings.get("yearly_work_hours", 1625))
pex = float(settings.get("pex_pct", 0.32))

# ========== Calculate EBIT for each month ==========
st.subheader("3. Beregn trend")

col1, col2, col3 = st.columns([1.5, 1.5, 6])

with col1:
    if st.button("🚀 Beregn EBIT-trend", type="primary"):
        start_idx = months_list.index(start_month)
        end_idx = months_list.index(end_month)

        if start_idx > end_idx:
            st.error("Start måned må være før slutt måned")
            st.stop()

        monthly_ebit_data = []

        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, month_idx in enumerate(range(start_idx, end_idx + 1)):
            month_num = month_idx + 1
            month_name = months_list[month_idx]

            progress = (idx + 1) / (end_idx - start_idx + 1)
            progress_bar.progress(progress)
            status_text.text(f"Beregner {month_name}...")

            # Finn første/siste dag i måneden
            if month_idx == 11:  # Desember
                month_start = date(year, 12, 1)
                month_end = date(year, 12, 31)
            else:
                month_start = date(year, month_idx + 1, 1)
                month_end = date(year, month_idx + 2, 1) - timedelta(days=1)

            # Bygg assignments for rader som overlapper denne måneden
            assignments = []
            row_expense_pcts = {}

            for row_idx, row in enumerate(hovedside_rows):
                row_start = row.get("start_date")
                row_end = row.get("end_date")
                if isinstance(row_start, str):
                    row_start = date.fromisoformat(row_start)
                if isinstance(row_end, str):
                    row_end = date.fromisoformat(row_end)

                # Hopper over rader som ikke overlapper måned
                if row_start > month_end or row_end < month_start:
                    continue

                consultant_id = row.get("consultant_id")
                project_id = row.get("project_id")

                # Filtrering: kun de valgte konsulentene/prosjektene
                if consultant_id not in filtered_consultant_ids or project_id not in filtered_project_ids:
                    continue

                work_pct_percent = row.get("consultant_work_pct", 100)
                work_pct_frac = max(
                    0.0, min(1.0, float(work_pct_percent) / 100.0))

                actual_start = max(row_start, month_start)
                actual_end = min(row_end, month_end)

                utlegg_mode = row.get("utlegg_mode", "Prosent")
                if utlegg_mode == "Manuelt":
                    # Summer manuelle utlegg fra hovedside for denne raden (tolkes som pr. måned)
                    manual_sum = 0.0
                    if row_idx < len(hovedside_manual_expenses):
                        manual_sum = sum(float(x.get("amount", 0.0))
                                         for x in hovedside_manual_expenses[row_idx])
                    row_expense_pcts[row_idx] = ("manual", manual_sum)
                else:
                    row_expense_pcts[row_idx] = (
                        "prosent", row.get("expense_pct", 0.0))

                assignments.append({
                    "row_index": row_idx,
                    "consultant_id": consultant_id,
                    "project_id": project_id,
                    "utilization": row.get("utilization", 0.8),
                    "project_percent": row.get("project_percent", 1.0),
                    "consultant_work_pct": work_pct_frac,
                    "start_date": actual_start.isoformat(),
                    "end_date": actual_end.isoformat(),
                    "utlegg_mode": utlegg_mode,
                    "expense_pct": row.get("expense_pct", 0.0),
                })

            # Ingen arbeid denne måneden
            if not assignments:
                monthly_ebit_data.append({
                    "Måned": month_name,
                    "Måned (num)": month_idx,
                    "Inntekt (kr)": 0.0,
                    "Kostnad (kr)": 0.0,
                    "Utlegg (kr)": 0.0,
                    "EBIT (kr)": 0.0,
                })
                continue

            payload = {
                "assignments": assignments,
                "yearly_work_hours": yearly_hours,
                "pex_pct": pex,
                "month": month_num,
            }

            try:
                r = requests.post(
                    f"{BACKEND_URL}/calculate-ebit", json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()

                # ---- Arbeidsdagsbasert skalering til månedsnivå ----
                bd_month = business_days_in_month(year, month_num)
                bd_year = business_days_in_year(year)
                month_weight = bd_month / bd_year if bd_year else 1.0

                # Avdelingstall fra backend
                dept = data.get("department", {}) or {}
                dept_income = float(dept.get("income", 0.0))
                dept_cost = float(dept.get("cost", 0.0))
                dept_ebit_backend = float(
                    dept.get("ebit", dept_income - dept_cost))

                # Skaler avdelingstall til månedsnivå (arbeidsdager)
                dept_income_m = dept_income * month_weight
                dept_cost_m = dept_cost * month_weight
                dept_ebit_backend_m = dept_ebit_backend * month_weight

                # Skaler rad-inntekter for prosent-utlegg til månedsnivå
                row_income_scaled = {}
                for result in data.get("results", []):
                    rid = result.get("row_index")
                    rincome = float(result.get("income", 0.0))
                    row_income_scaled[rid] = rincome * month_weight

                # Utlegg:
                #  - Manuelle: behandles som pr. måned (ikke skalert)
                #  - Prosent: følger skalert månedsinntekt
                utlegg_total = 0.0
                for ridx, expense_info in row_expense_pcts.items():
                    mode, value = expense_info
                    if mode == "manual":
                        utlegg_total += float(value)
                    else:
                        rincome_m = row_income_scaled.get(ridx, 0.0)
                        utlegg_total += rincome_m * float(value)

                # EBIT for visning (avdeling)
                if BACKEND_EBIT_INCLUDES_UTLEGG:
                    dept_ebit_final = dept_ebit_backend_m
                else:
                    dept_ebit_final = dept_ebit_backend_m - utlegg_total

                monthly_ebit_data.append({
                    "Måned": month_name,
                    "Måned (num)": month_idx,
                    "Inntekt (kr)": dept_income_m,
                    "Kostnad (kr)": dept_cost_m,
                    "Utlegg (kr)": utlegg_total,
                    "EBIT (kr)": dept_ebit_final,
                })
            except Exception as e:
                st.error(f"Feil ved beregning for {month_name}: {e}")
                st.session_state.ebit_trends_results = None
                st.stop()

        progress_bar.progress(1.0)
        status_text.text("✓ Ferdig!")

        # Lagre resultater i session state
        st.session_state.ebit_trends_results = monthly_ebit_data if monthly_ebit_data else None

with col2:
    if st.button("🗑️ Slett resultater"):
        st.session_state.ebit_trends_results = None
        st.rerun()

# ========== Display results if they exist ==========
if st.session_state.ebit_trends_results:
    monthly_ebit_data = st.session_state.ebit_trends_results

    # DataFrame
    df = pd.DataFrame(
        monthly_ebit_data) if monthly_ebit_data else pd.DataFrame()

    if not df.empty:
        st.success("✓ Beregning fullført!")

        # ---- Avledede KPI-er ----
        # EBIT % (måned) = EBIT / Inntekt * 100, beskytt mot deling på null
        df["EBIT % (mnd)"] = df.apply(
            lambda r: (r["EBIT (kr)"] / r["Inntekt (kr)"] * 100.0) if r["Inntekt (kr)"] else 0.0, axis=1
        )
        # YTD: kumulative tall og kumulativ EBIT %
        df["EBIT (kr) YTD"] = df["EBIT (kr)"].cumsum()
        df["Inntekt (kr) YTD"] = df["Inntekt (kr)"].cumsum()
        df["EBIT % (YTD)"] = df.apply(
            lambda r: (r["EBIT (kr) YTD"] / r["Inntekt (kr) YTD"] * 100.0) if r["Inntekt (kr) YTD"] else 0.0, axis=1
        )

        # ---- Tabell (formatert for lesbarhet) ----
        st.subheader("Månedlige resultater")
        display_df = df.copy()
        for col in ["Inntekt (kr)", "Kostnad (kr)", "Utlegg (kr)", "EBIT (kr)", "EBIT (kr) YTD", "Inntekt (kr) YTD"]:
            display_df[col] = display_df[col].apply(
                lambda x: f"{x:,.0f}".replace(",", " "))
        display_df["EBIT % (mnd)"] = display_df["EBIT % (mnd)"].map(
            lambda x: f"{x:.1f}%")
        display_df["EBIT % (YTD)"] = display_df["EBIT % (YTD)"].map(
            lambda x: f"{x:.1f}%")

        st.dataframe(
            display_df[[
                "Måned", "Inntekt (kr)", "Kostnad (kr)", "Utlegg (kr)",
                "EBIT (kr)", "EBIT % (mnd)", "EBIT (kr) YTD", "Inntekt (kr) YTD", "EBIT % (YTD)"
            ]],
            use_container_width=True
        )

        # ===========================
        #   GRAFER (OPPDELING I 2 x 2)
        # ===========================
        if not PLOTLY_AVAILABLE:
            st.info(
                "Plotly er ikke installert. Kjør `pip install plotly`, og sørg for at VS Code bruker riktig venv.")
        else:
            # ---------- RAD 1: MÅNEDLIG ----------
            c1, c2 = st.columns(2)

            with c1:
                # Venstre: EBIT trend – månedlig
                fig_m_ebit = go.Figure()
                fig_m_ebit.add_trace(go.Scatter(
                    x=df["Måned"], y=df["EBIT (kr)"], mode="lines+markers",
                    name="EBIT (inkl. utlegg)", line=dict(color="#2ecc71", width=3),
                    marker=dict(size=8, color="#27ae60"), fill="tozeroy",
                    fillcolor="rgba(46, 204, 113, 0.10)"
                ))
                fig_m_ebit.add_hline(y=0, line_dash="dash", line_color="red", line_width=2,
                                     annotation_text="Break-even", annotation_position="right")
                fig_m_ebit.update_layout(
                    title="EBIT trend – månedlig", xaxis_title="Måned", yaxis_title="EBIT (NOK)",
                    hovermode="x unified", height=CHART_HEIGHT, template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_m_ebit, use_container_width=True)

            with c2:
                # Høyre: EBIT % trend – månedlig
                fig_m_ebitpct = go.Figure()
                fig_m_ebitpct.add_trace(go.Scatter(
                    x=df["Måned"], y=df["EBIT % (mnd)"], mode="lines+markers",
                    name="EBIT % (mnd)", line=dict(color="#8e44ad", width=3),
                    marker=dict(size=8, color="#9b59b6"),
                ))
                fig_m_ebitpct.add_hline(
                    y=0, line_dash="dot", line_color="#7f8c8d", line_width=1)
                fig_m_ebitpct.update_layout(
                    title="EBIT % trend – månedlig", xaxis_title="Måned", yaxis_title="EBIT (%)",
                    hovermode="x unified", height=CHART_HEIGHT, template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_m_ebitpct, use_container_width=True)

            # ---------- RAD 2: YTD ----------
            c3, c4 = st.columns(2)

            with c3:
                # Venstre: EBIT trend – YTD (kumulativ)
                fig_ytd_ebit = go.Figure()
                fig_ytd_ebit.add_trace(go.Scatter(
                    x=df["Måned"], y=df["EBIT (kr) YTD"], mode="lines+markers",
                    name="EBIT YTD", line=dict(color="#16a085", width=3),
                    marker=dict(size=8, color="#1abc9c"), fill="tozeroy",
                    fillcolor="rgba(26, 188, 156, 0.10)"
                ))
                fig_ytd_ebit.add_hline(
                    y=0, line_dash="dash", line_color="red", line_width=2)
                fig_ytd_ebit.update_layout(
                    title="EBIT trend – YTD", xaxis_title="Måned", yaxis_title="EBIT (NOK) – kumulativ",
                    hovermode="x unified", height=CHART_HEIGHT, template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_ytd_ebit, use_container_width=True)

            with c4:
                # Høyre: EBIT % trend – YTD (kumulativ)
                fig_ytd_ebitpct = go.Figure()
                fig_ytd_ebitpct.add_trace(go.Scatter(
                    x=df["Måned"], y=df["EBIT % (YTD)"], mode="lines+markers",
                    name="EBIT % YTD", line=dict(color="#c0392b", width=3),
                    marker=dict(size=8, color="#e74c3c"),
                ))
                fig_ytd_ebitpct.add_hline(
                    y=0, line_dash="dot", line_color="#7f8c8d", line_width=1)
                fig_ytd_ebitpct.update_layout(
                    title="EBIT % trend – YTD", xaxis_title="Måned", yaxis_title="EBIT (%) – kumulativ",
                    hovermode="x unified", height=CHART_HEIGHT, template="plotly_white", showlegend=False
                )
                st.plotly_chart(fig_ytd_ebitpct, use_container_width=True)

        # ---- Sammendragskort + nedlasting ----
        st.subheader("Sammenfattende statistikk")
        c1, c2, c3, c4 = st.columns(4)
        avg_ebit = df["EBIT (kr)"].mean()
        max_ebit = df["EBIT (kr)"].max()
        min_ebit = df["EBIT (kr)"].min()
        total_ebit = df["EBIT (kr)"].sum()
        with c1:
            st.metric("Gjennomsnitt EBIT",
                      f"{avg_ebit:,.0f} kr".replace(",", " "))
        with c2:
            st.metric("Høyeste EBIT", f"{max_ebit:,.0f} kr".replace(",", " "))
        with c3:
            st.metric("Laveste EBIT", f"{min_ebit:,.0f} kr".replace(",", " "))
        with c4:
            st.metric("Total EBIT", f"{total_ebit:,.0f} kr".replace(",", " "))

        csv = df[[
            "Måned", "Inntekt (kr)", "Kostnad (kr)", "Utlegg (kr)",
            "EBIT (kr)", "EBIT % (mnd)", "Inntekt (kr) YTD", "EBIT (kr) YTD", "EBIT % (YTD)"
        ]].to_csv(index=False)
        st.download_button(
            label="📥 Last ned CSV",
            data=csv,
            file_name="ebit_trends.csv",
            mime="text/csv"
        )
