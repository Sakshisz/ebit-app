# pages/EBIT_Trends.py
import streamlit as st
import requests
import pandas as pd
import datetime

BACKEND_URL = "http://localhost:8000"

# Backend EBIT includes utlegg (same as main app.py)
BACKEND_EBIT_INCLUDES_UTLEGG = False

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
except Exception as e:
    st.warning(f"Kunne ikke hente innstillinger, bruker defaults")
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

months_list = ["Januar", "Februar", "Mars", "April", "Mai", "Juni",
               "Juli", "August", "September", "Oktober", "November", "Desember"]

with col1:
    start_month = st.selectbox(
        "Start måned",
        options=months_list,
        index=0,
        key="start_month"
    )

with col2:
    end_month = st.selectbox(
        "Slutt måned",
        options=months_list,
        index=11,
        key="end_month"
    )

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
    available_consultant_names = []
    available_project_names = []

with col1:
    consultant_names_options = ["Alle"] + available_consultant_names
    selected_consultants = st.multiselect(
        "Konsulenter",
        options=consultant_names_options,
        default=["Alle"],
        key="selected_consultants"
    )

with col2:
    project_names_options = ["Alle"] + available_project_names
    selected_projects = st.multiselect(
        "Prosjekter",
        options=project_names_options,
        default=["Alle"],
        key="selected_projects"
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
expense_pct_fixed = float(settings.get("expense_pct", 0.40))

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

        # Build results storage
        monthly_ebit_data = []

        # For each month in the range
        progress_bar = st.progress(0)
        status_text = st.empty()

        for idx, month_idx in enumerate(range(start_idx, end_idx + 1)):
            month_num = month_idx + 1
            month_name = months_list[month_idx]

            progress = idx / (end_idx - start_idx + 1)
            progress_bar.progress(progress)
            status_text.text(f"Beregner {month_name}...")

            # Get the first and last day of the month
            if month_idx == 11:  # December
                month_start = datetime.date(year, 12, 1)
                month_end = datetime.date(year, 12, 31)
            else:
                month_start = datetime.date(year, month_idx + 1, 1)
                month_end = datetime.date(
                    year, month_idx + 2, 1) - datetime.timedelta(days=1)

            # Build assignments from hovedside rows that overlap with this month
            assignments = []
            row_expense_pcts = {}  # Store actual expense_pct per row

            for row_idx, row in enumerate(hovedside_rows):
                row_start = row.get("start_date")
                row_end = row.get("end_date")

                # Convert to date if needed
                if isinstance(row_start, str):
                    row_start = datetime.date.fromisoformat(row_start)
                if isinstance(row_end, str):
                    row_end = datetime.date.fromisoformat(row_end)

                # Check if this row overlaps with the current month
                if row_start > month_end or row_end < month_start:
                    # This consultant doesn't work in this month
                    continue

                # Check if consultant/project is filtered
                consultant_id = row.get("consultant_id")
                project_id = row.get("project_id")

                if consultant_id not in filtered_consultant_ids or project_id not in filtered_project_ids:
                    continue

                work_pct_percent = row.get("consultant_work_pct", 100)
                work_pct_frac = max(
                    0.0, min(1.0, float(work_pct_percent) / 100.0))

                # Use actual dates from hovedside but limit to this month
                actual_start = max(row_start, month_start)
                actual_end = min(row_end, month_end)

                # Store the expense_pct for this row
                utlegg_mode = row.get("utlegg_mode", "Prosent")
                if utlegg_mode == "Manuelt":
                    # For manual mode, get from session state
                    manual_sum = 0.0
                    if row_idx < len(hovedside_manual_expenses):
                        manual_sum = sum(
                            float(x.get("amount", 0.0)) for x in hovedside_manual_expenses[row_idx]
                        )
                    row_expense_pcts[row_idx] = ("manual", manual_sum)
                else:
                    # For percentage mode
                    expense_pct = row.get("expense_pct", 0.0)
                    row_expense_pcts[row_idx] = ("prosent", expense_pct)

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

            if not assignments:
                # No consultants work in this month, add zero values
                monthly_ebit_data.append({
                    "Måned": month_name,
                    "Måned (num)": month_idx,
                    "Inntekt (kr)": 0.0,
                    "Kostnad (kr)": 0.0,
                    "Utlegg (kr)": 0.0,
                    "EBIT (kr)": 0.0,
                })
                continue

            # Call backend
            payload = {
                "assignments": assignments,
                "yearly_work_hours": yearly_hours,
                "pex_pct": pex,
                "month": month_num,
            }

            try:
                r = requests.post(f"{BACKEND_URL}/calculate-ebit",
                                  json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()

                dept = data.get("department", {}) or {}
                dept_income = float(dept.get("income", 0.0))
                dept_cost = float(dept.get("cost", 0.0))
                dept_ebit_backend = float(
                    dept.get("ebit", dept_income - dept_cost))

                # Calculate utlegg based on actual rows (not global expense_pct_fixed)
                utlegg_total = 0.0
                for row_idx, expense_info in row_expense_pcts.items():
                    mode, value = expense_info
                    if mode == "manual":
                        utlegg_total += value
                    else:  # prosent
                        # Find the income for this specific row
                        for result in data.get("results", []):
                            if result.get("row_index") == row_idx:
                                row_income = float(result.get("income", 0.0))
                                utlegg_total += row_income * value
                                break

                if BACKEND_EBIT_INCLUDES_UTLEGG:
                    dept_ebit_final = dept_ebit_backend
                else:
                    dept_ebit_final = dept_ebit_backend - utlegg_total

                monthly_ebit_data.append({
                    "Måned": month_name,
                    "Måned (num)": month_idx,
                    "Inntekt (kr)": dept_income,
                    "Kostnad (kr)": dept_cost,
                    "Utlegg (kr)": utlegg_total,
                    "EBIT (kr)": dept_ebit_final,
                })
            except Exception as e:
                st.error(f"Feil ved beregning for {month_name}: {e}")
                st.session_state.ebit_trends_results = None
                st.stop()

        progress_bar.progress(1.0)
        status_text.text("✓ Ferdig!")

        # Store results in session state
        if monthly_ebit_data:
            st.session_state.ebit_trends_results = monthly_ebit_data
        else:
            st.session_state.ebit_trends_results = None

with col2:
    if st.button("🗑️ Slett resultater"):
        st.session_state.ebit_trends_results = None
        st.rerun()

# ========== Display results if they exist ==========
if st.session_state.ebit_trends_results:
    monthly_ebit_data = st.session_state.ebit_trends_results

    # Create DataFrame
    if monthly_ebit_data:
        df = pd.DataFrame(monthly_ebit_data)

        # Display results
        st.success("✓ Beregning fullført!")

        st.subheader("Månedlige resultater")

        # Format display (create a copy for display, keep original for calculations)
        display_df = df.copy()
        display_df["Inntekt (kr)"] = display_df["Inntekt (kr)"].apply(
            lambda x: f"{x:,.0f}".replace(",", " "))
        display_df["Kostnad (kr)"] = display_df["Kostnad (kr)"].apply(
            lambda x: f"{x:,.0f}".replace(",", " "))
        display_df["Utlegg (kr)"] = display_df["Utlegg (kr)"].apply(
            lambda x: f"{x:,.0f}".replace(",", " "))
        display_df["EBIT (kr)"] = display_df["EBIT (kr)"].apply(
            lambda x: f"{x:,.0f}".replace(",", " "))

        st.dataframe(display_df[["Måned", "Inntekt (kr)", "Kostnad (kr)", "Utlegg (kr)", "EBIT (kr)"]],
                     use_container_width=True)

        # Chart: EBIT trend
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            # EBIT line
            fig.add_trace(go.Scatter(
                x=df["Måned"],
                y=df["EBIT (kr)"],
                mode='lines+markers',
                name='EBIT (inkl. utlegg)',
                line=dict(color='#2ecc71', width=3),
                marker=dict(size=10, color='#27ae60'),
                fill='tozeroy',
                fillcolor='rgba(46, 204, 113, 0.1)'
            ))

            # Add a zero line for break-even
            fig.add_hline(y=0, line_dash="dash", line_color="red",
                          line_width=2, annotation_text="Break-even", annotation_position="right")

            fig.update_layout(
                title="EBIT Trend – Månedlig utvikling",
                xaxis_title="Måned",
                yaxis_title="EBIT (NOK)",
                hovermode='x unified',
                height=450,
                template='plotly_white',
                font=dict(size=12),
                showlegend=True
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"Kunne ikke tegne EBIT trend graf: {e}")

        # Chart: Income vs Cost comparison
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df["Måned"],
                y=df["Inntekt (kr)"],
                name='Inntekt',
                marker_color='#3498db',
                text=df["Inntekt (kr)"].apply(
                    lambda x: f'{x:,.0f}'.replace(',', ' ')),
                textposition='outside',
                hovertemplate='<b>Inntekt</b><br>%{text}<extra></extra>'
            ))

            fig.add_trace(go.Bar(
                x=df["Måned"],
                y=df["Kostnad (kr)"],
                name='Kostnad',
                marker_color='#e74c3c',
                text=df["Kostnad (kr)"].apply(
                    lambda x: f'{x:,.0f}'.replace(',', ' ')),
                textposition='outside',
                hovertemplate='<b>Kostnad</b><br>%{text}<extra></extra>'
            ))

            fig.add_trace(go.Scatter(
                x=df["Måned"],
                y=df["EBIT (kr)"],
                mode='lines+markers',
                name='EBIT (inkl. utlegg)',
                line=dict(color='#2ecc71', width=3),
                marker=dict(size=10),
                yaxis='y2',
                hovertemplate='<b>EBIT</b><br>%{y:,.0f} kr<extra></extra>'
            ))

            fig.update_layout(
                title="Inntekt, Kostnad & EBIT – Månedlig oversikt",
                xaxis_title="Måned",
                yaxis_title="Inntekt & Kostnad (NOK)",
                yaxis2=dict(
                    title="EBIT (NOK)",
                    overlaying="y",
                    side="right"
                ),
                hovermode='x unified',
                height=500,
                template='plotly_white',
                barmode='group',
                font=dict(size=11)
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"Kunne ikke tegne sammenligning graf: {e}")

        # Chart: Detailed breakdown per month
        try:
            import plotly.graph_objects as go

            fig = go.Figure()

            fig.add_trace(go.Bar(
                x=df["Måned"],
                y=df["Inntekt (kr)"],
                name='Inntekt',
                marker_color='#3498db'
            ))

            fig.add_trace(go.Bar(
                x=df["Måned"],
                y=-df["Kostnad (kr)"],
                name='Kostnad',
                marker_color='#e74c3c'
            ))

            fig.add_trace(go.Bar(
                x=df["Måned"],
                y=-df["Utlegg (kr)"],
                name='Utlegg',
                marker_color='#f39c12'
            ))

            fig.update_layout(
                title="Inntekt minus Kostnad og Utlegg – Månedsvis",
                xaxis_title="Måned",
                yaxis_title="Beløp (NOK)",
                hovermode='x unified',
                height=450,
                template='plotly_white',
                barmode='relative',
                font=dict(size=11)
            )

            st.plotly_chart(fig, use_container_width=True)
        except Exception as e:
            st.info(f"Kunne ikke tegne detalj graf: {e}")

        # Summary statistics (using original numeric df, not formatted display_df)
        st.subheader("Sammenfattende statistikk")

        col1, col2, col3, col4 = st.columns(4)

        avg_ebit = df["EBIT (kr)"].mean()
        max_ebit = df["EBIT (kr)"].max()
        min_ebit = df["EBIT (kr)"].min()
        total_ebit = df["EBIT (kr)"].sum()

        with col1:
            st.metric("Gjennomsnitt EBIT",
                      f"{avg_ebit:,.0f} kr".replace(",", " "))
        with col2:
            st.metric("Høyeste EBIT", f"{max_ebit:,.0f} kr".replace(",", " "))
        with col3:
            st.metric("Laveste EBIT", f"{min_ebit:,.0f} kr".replace(",", " "))
        with col4:
            st.metric("Total EBIT", f"{total_ebit:,.0f} kr".replace(",", " "))

        # Download CSV (using original numeric df)
        csv = df[["Måned", "Inntekt (kr)", "Kostnad (kr)",
                 "Utlegg (kr)", "EBIT (kr)"]].to_csv(index=False)
        st.download_button(
            label="📥 Last ned CSV",
            data=csv,
            file_name="ebit_trends.csv",
            mime="text/csv"
        )
