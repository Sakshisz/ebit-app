
# app.py
import streamlit as st
import requests
import datetime

BACKEND_URL = "http://localhost:8000"

# Toggle: send month as index (1–12) or as Norwegian name ("Januar" ...)
SEND_MONTH_AS_INDEX = True

# IMPORTANT: Does your backend already include utlegg in its EBIT?
# - If True: we will display EBIT exactly as returned by backend (no extra subtraction)
# - If False: we will compute "EBIT (inkl. utlegg)" = backend EBIT - utlegg_cost
BACKEND_EBIT_INCLUDES_UTLEGG = False

st.set_page_config(page_title="EBIT Kalkulator", page_icon="💰", layout="wide")
st.title("💰 EBIT Kalkulator – Hovedside")

st.write(
    "Velg konsulent og prosjekt via nedtrekkslister. "
    "Lønn og timepris hentes fra registrerte data. "
    "Bruk sidemenyen for å registrere konsulenter/prosjekter og justere innstillinger."
)

# ========== Helpers & caching ==========


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


def invalidate_caches():
    try:
        fetch_consultants.clear()
    except Exception:
        pass
    try:
        fetch_projects.clear()
    except Exception:
        pass


# ========== Fetch data ==========
consultants = []
projects = []
try:
    consultants = fetch_consultants()
except requests.HTTPError as e:
    st.error(
        f"Feil ved henting av konsulenter ({e.response.status_code}): {e.response.text}")
except Exception as e:
    st.error(f"Feil ved henting av konsulenter: {e}")

try:
    projects = fetch_projects()
except requests.HTTPError as e:
    st.error(
        f"Feil ved henting av prosjekter ({e.response.status_code}): {e.response.text}")
except Exception as e:
    st.error(f"Feil ved henting av prosjekter: {e}")

if not consultants:
    st.warning(
        "Ingen konsulenter funnet. Gå til **'Konsulenter'**-siden for å legge inn.")
if not projects:
    st.warning(
        "Ingen prosjekter funnet. Gå til **'Prosjekter'**-siden for å legge inn.")
if not consultants or not projects:
    st.stop()

consultant_options = {f"{c['name']} (#{c['id']})": c['id']
                      for c in consultants}
project_options = {
    f"{p['name']} (#{p['id']}) – {int(p['hourly_rate'])} kr/t": p['id'] for p in projects}
consultant_by_id = {c["id"]: c for c in consultants}
project_by_id = {p["id"]: p for p in projects}

# ========== Month selector ==========
months = [
    "Januar", "Februar", "Mars", "April", "Mai", "Juni",
    "Juli", "August", "September", "Oktober", "November", "Desember"
]
today = datetime.date.today()
default_month_idx = max(0, min(11, today.month - 1))
selected_month = st.selectbox(
    "Velg måned", months, index=default_month_idx, key="selected_month")

# ========== Session init: rows & manual_expenses ==========
if "rows" not in st.session_state:
    default_consultant_id = consultants[0]["id"]
    default_project_id = projects[0]["id"]
    default_util = float(consultants[0].get("default_utilization", 0.8))
    st.session_state.rows = [
        {
            "consultant_id": default_consultant_id,
            "project_id": default_project_id,
            "utilization": default_util,   # 0–1 (fraction)
            "project_percent": 1.0,        # 0–1 (fraction)
            "consultant_work_pct": 100,  # 0–100 (%)
            "start_date": datetime.date.today(),
            "end_date": datetime.date.today() + datetime.timedelta(days=30),
            "utlegg_mode": "Prosent",      # "Prosent" | "Manuelt"
            "expense_pct": 0.0,            # only for Prosent (0–1)
        }
    ]

# manual_expenses is a list per row: [[{type, amount}, ...], ...]
if "manual_expenses" not in st.session_state:
    st.session_state.manual_expenses = [[] for _ in st.session_state.rows]
else:
    while len(st.session_state.manual_expenses) < len(st.session_state.rows):
        st.session_state.manual_expenses.append([])
    while len(st.session_state.manual_expenses) > len(st.session_state.rows):
        st.session_state.manual_expenses.pop()

# Initialize results storage
if "hovedside_results" not in st.session_state:
    st.session_state.hovedside_results = None


def add_row():
    base_util = float(consultants[0].get("default_utilization", 0.8))
    st.session_state.rows.append({
        "consultant_id": consultants[0]["id"],
        "project_id": projects[0]["id"],
        "utilization": base_util,
        "project_percent": 1.0,
        "consultant_work_pct": 100,
        "start_date": datetime.date.today(),
        "end_date": datetime.date.today() + datetime.timedelta(days=30),
        "utlegg_mode": "Prosent",
        "expense_pct": 0.0,
    })
    st.session_state.manual_expenses.append([])


def remove_row(idx: int):
    if 0 <= idx < len(st.session_state.rows):
        st.session_state.rows.pop(idx)
        if idx < len(st.session_state.manual_expenses):
            st.session_state.manual_expenses.pop(idx)


def clear_all_data():
    """Clear all rows and manual expenses"""
    st.session_state.rows = []
    st.session_state.manual_expenses = []


# ========== Info toggles ==========
if "show_util_info" not in st.session_state:
    st.session_state["show_util_info"] = False
if "show_proj_info" not in st.session_state:
    st.session_state["show_proj_info"] = False


def toggle_util_info():
    st.session_state["show_util_info"] = not st.session_state["show_util_info"]


def toggle_proj_info():
    st.session_state["show_proj_info"] = not st.session_state["show_proj_info"]


# ========== Header ==========
st.header("Valg per rad")
col1, col2, col3 = st.columns([1, 1, 8])
with col1:
    st.button("+ Legg til rad", on_click=add_row, key="add_row")
with col2:
    if st.button("🗑️ Slett all data", key="clear_all_btn"):
        clear_all_data()
        st.rerun()

consultant_label_by_id = {v: k for k, v in consultant_options.items()}
project_label_by_id = {v: k for k, v in project_options.items()}

manual_expense_types = ["Transport", "Reise",
                        "Mat", "Hotell", "Taxi", "Kurs", "Annet"]

# # | Konsulent | Prosjekt | Utnyttelsesgrad | Prosjektbelastning
cols_spec = [1, 3, 4, 2, 2]
hcols = st.columns(cols_spec)
hcols[0].markdown("**#**")
hcols[1].markdown("**Konsulent**")
hcols[2].markdown("**Prosjekt**")

hcols[3].markdown("**Utnyttelsesgrad**")
if hcols[3].button("i", key="util_info_btn", help="Hva betyr Utnyttelsesgrad?"):
    toggle_util_info()

hcols[4].markdown("**Prosjektbelastning**")
if hcols[4].button("i", key="proj_info_btn", help="Hva betyr Prosjektbelastning?"):
    toggle_proj_info()

if st.session_state.get("show_util_info"):
    st.info(
        "**Utnyttelsesgrad:** Andel av en konsulents arbeidstid brukt til arbeid i perioden.\n"
        "Eksempel: `0.8` betyr 80% av tiden er utnyttet (tilgjengelige fakturerbare timer påvirkes)."
    )
if st.session_state.get("show_proj_info"):
    st.info(
        "**Prosjektbelastning:** Andel av den utnyttede tiden som går til dette prosjektet.\n"
        "Eksempel: `utnyttelse=0.8`, `prosjektbelastning=0.5` → 0.8 * 0.5 = 0.4 (40% av totaltid)."
    )

# ========== Render dynamic rows ==========
for i, row in enumerate(list(st.session_state.rows)):
    cols = st.columns(cols_spec)

    # remove
    if cols[0].button("–", key=f"remove_{i}"):
        remove_row(i)
        st.rerun()

    # consultant
    current_consultant_label = consultant_label_by_id.get(
        row["consultant_id"], list(consultant_options.keys())[0]
    )
    consul_label = cols[1].selectbox(
        "", options=list(consultant_options.keys()),
        index=list(consultant_options.keys()).index(current_consultant_label),
        key=f"consultant_{i}"
    )
    consul_id = consultant_options[consul_label]
    consul = consultant_by_id[consul_id]
    cols[1].caption(
        f"Årslønn: **{int(consul['salary']):,} kr**".replace(",", " "))

    # dates under consultant
    date_cols = cols[1].columns(2)
    start_date = date_cols[0].date_input("Fra", value=row.get(
        "start_date", datetime.date.today()), key=f"start_date_{i}")
    end_date = date_cols[1].date_input(
        "Til", value=row.get("end_date", datetime.date.today() + datetime.timedelta(days=30)), key=f"end_date_{i}"
    )
    if start_date > end_date:
        cols[1].error("Ugyldig datointervall (Fra > Til).")

    # project select
    current_project_label = project_label_by_id.get(
        row["project_id"], list(project_options.keys())[0])
    proj_label = cols[2].selectbox(
        "", options=list(project_options.keys()),
        index=list(project_options.keys()).index(current_project_label),
        key=f"project_{i}"
    )
    proj_id = project_options[proj_label]
    proj = project_by_id[proj_id]
    cols[2].caption(
        f"Timepris: **{int(proj['hourly_rate']):,} kr**".replace(",", " "))

    # work percent (%) under project
    work_pct = cols[2].slider(
        "Arbeidsprosent (%)", 0, 100, value=row.get("consultant_work_pct", 100), step=5, key=f"workpct_row_{i}",
        help="Andel av tiden som faktisk jobbes i perioden (tar høyde for ferie/sykefravær)."
    )

    # utilization (0–1)
    util_default = float(
        row.get("utilization", consul.get("default_utilization", 0.8)))
    util = cols[3].slider("", 0.0, 1.0, value=util_default,
                          step=0.05, key=f"util_{i}")

    # project load (0–1)
    project_percent = cols[4].slider(
        "Prosjektbelastning", 0.0, 1.0, value=row.get("project_percent", 1.0), step=0.05, key=f"proj_pct_{i}"
    )

    # ---------- Utlegg (inline, no expander) ----------
    cols[2].markdown("**Utlegg**")
    utlegg_mode = cols[2].selectbox(
        "Modus", ["Prosent", "Manuelt"],
        index=["Prosent", "Manuelt"].index(row.get("utlegg_mode", "Prosent")),
        key=f"utlegg_mode_{i}"
    )
    expense_pct = row.get("expense_pct", 0.0)

    if utlegg_mode == "Prosent":
        expense_pct = cols[2].number_input(
            "Utlegg (%)",
            min_value=0.0, max_value=1.0,
            value=float(expense_pct), step=0.01,
            key=f"expense_pct_{i}",
            help="Andel (0–1) av inntekt som utlegg."
        )
    else:
        # Manual inline entries
        while len(st.session_state.manual_expenses) < len(st.session_state.rows):
            st.session_state.manual_expenses.append([])

        cols[2].markdown(
            "_Legg til én eller flere linjer med Type og Beløp (kr)._")

        if cols[2].button("+ Legg til utlegg", key=f"add_manual_exp_inline_{i}"):
            st.session_state.manual_expenses[i].append(
                {"type": manual_expense_types[0], "amount": 0.0})
            st.rerun()

        for ei, exp in enumerate(list(st.session_state.manual_expenses[i])):
            il_cols = cols[2].columns([3, 2, 1])  # Type | Amount | remove
            etype = il_cols[0].selectbox(
                "Type", options=manual_expense_types,
                index=manual_expense_types.index(
                    exp.get("type", manual_expense_types[0])),
                key=f"exp_type_inline_{i}_{ei}"
            )
            eamount = il_cols[1].number_input(
                "Beløp (kr)", min_value=0.0, value=float(exp.get("amount", 0.0)), key=f"exp_amount_inline_{i}_{ei}"
            )
            if il_cols[2].button("–", key=f"exp_remove_inline_{i}_{ei}"):
                st.session_state.manual_expenses[i].pop(ei)
                st.rerun()
            # update item
            st.session_state.manual_expenses[i][ei] = {
                "type": etype, "amount": float(eamount)}

        # Local sum for manual utlegg on this row
        manual_sum = sum(exp.get("amount", 0.0)
                         for exp in st.session_state.manual_expenses[i])
        cols[2].caption(
            f"**Sum utlegg (manuelt): {manual_sum:,.0f} kr**".replace(",", " "))

    # Update state row
    st.session_state.rows[i] = {
        "consultant_id": consul_id,
        "project_id": proj_id,
        "utilization": util,
        "project_percent": project_percent,
        "consultant_work_pct": work_pct,
        "start_date": start_date,
        "end_date": end_date,
        "utlegg_mode": utlegg_mode,
        "expense_pct": expense_pct,
    }

# ========== Build assignments (with row_index) ==========
assignments = []
for idx, row in enumerate(st.session_state.rows):
    if row["start_date"] > row["end_date"]:
        continue
    work_pct_percent = row.get("consultant_work_pct", 100)
    work_pct_frac = max(0.0, min(1.0, float(work_pct_percent) / 100.0))
    assignments.append({
        "row_index": idx,  # helps match results back to front-end row
        "consultant_id": row["consultant_id"],
        "project_id": row["project_id"],
        "utilization": row["utilization"],
        "project_percent": row["project_percent"],
        "consultant_work_pct": work_pct_frac,
        "start_date": row["start_date"].isoformat(),
        "end_date": row["end_date"].isoformat(),
        "utlegg_mode": row.get("utlegg_mode", "Prosent"),
        "expense_pct": row.get("expense_pct", 0.0),
    })

left, right = st.columns([1, 1])
with left:
    yearly_hours = st.number_input(
        "Årlige arbeidstimer", min_value=1000, max_value=2200, value=1625)
with right:
    pex = st.number_input("PEX (%)", min_value=0.0,
                          max_value=1.0, value=0.32, help="Sosiale kostnader")

# ========== Calculate ==========
col1, col2, col3 = st.columns([1, 1, 8])
with col1:
    if st.button("Beregn EBIT"):
        # Get selected month as number (1-12)
        selected_month_num = months.index(selected_month) + 1

        # Get current year (or you could add a year selector)
        current_year = datetime.date.today().year

        # Get the first and last day of the selected month
        if selected_month_num == 12:
            month_start = datetime.date(current_year, 12, 1)
            month_end = datetime.date(current_year, 12, 31)
        else:
            month_start = datetime.date(current_year, selected_month_num, 1)
            month_end = datetime.date(
                current_year, selected_month_num + 1, 1) - datetime.timedelta(days=1)

        # Filter assignments to only include those that overlap with selected month
        filtered_assignments = []
        for assignment in assignments:
            start_date = datetime.date.fromisoformat(assignment["start_date"])
            end_date = datetime.date.fromisoformat(assignment["end_date"])

            # Check if assignment overlaps with selected month
            if start_date <= month_end and end_date >= month_start:
                filtered_assignments.append(assignment)

        if not filtered_assignments:
            st.warning(
                f"Ingen konsulenter jobber i {selected_month}. Velg en annen måned eller legg til flere rader.")
            st.session_state.hovedside_results = None
        else:
            month_value = selected_month_num if SEND_MONTH_AS_INDEX else selected_month

            payload = {
                "assignments": filtered_assignments,
                "yearly_work_hours": yearly_hours,
                "pex_pct": pex,
                "month": month_value,
                # optional hint to backend (does not break old backends):
                "client_hints": {"utlegg_included_in_ebit": BACKEND_EBIT_INCLUDES_UTLEGG},
            }

            # Add manual expenses aligned to rows (empty lists for non-manual rows are fine)
            if "manual_expenses" in st.session_state:
                payload["manual_expenses"] = st.session_state.get(
                    "manual_expenses", [])

            try:
                r = requests.post(f"{BACKEND_URL}/calculate-ebit",
                                  json=payload, timeout=30)
                r.raise_for_status()
                data = r.json()
                st.session_state.hovedside_results = data
                st.success("Beregning fullført")
            except requests.exceptions.RequestException as e:
                st.error(
                    f"Feil ved beregning ({getattr(r, 'status_code', 'unknown')}): {getattr(r, 'text', str(e))}")
                st.session_state.hovedside_results = None
            except Exception as e:
                st.error(f"Feil ved beregning: {e}")
                st.session_state.hovedside_results = None

with col2:
    if st.button("🗑️ Slett resultater"):
        st.session_state.hovedside_results = None
        st.rerun()

# ========== Display results if they exist ==========
if st.session_state.hovedside_results:
    data = st.session_state.hovedside_results
    st.write("## Resultater per rad")

    results = data.get("results", [])
    total_utlegg = 0.0

    # Display per-row with utlegg and EBIT adjusted if needed
    for pos, rowres in enumerate(results):
        ridx = rowres.get("row_index", pos)
        if ridx >= len(st.session_state.rows):
            continue
        frontend_row = st.session_state.rows[ridx]
        mode = frontend_row.get("utlegg_mode", "Prosent")
        exp_pct = float(frontend_row.get("expense_pct", 0.0))

        income = float(rowres.get("income", 0.0))
        cost = float(rowres.get("cost", 0.0))
        ebit_backend = float(rowres.get("ebit", income - cost))

        # Compute utlegg cost for the row
        if mode == "Manuelt":
            manual_sum = 0.0
            if "manual_expenses" in st.session_state and ridx < len(st.session_state.manual_expenses):
                manual_sum = sum(
                    float(x.get("amount", 0.0)) for x in st.session_state.manual_expenses[ridx]
                )
            utlegg_cost = manual_sum
        else:
            utlegg_cost = income * exp_pct

        total_utlegg += utlegg_cost

        # Final EBIT to show
        if BACKEND_EBIT_INCLUDES_UTLEGG:
            ebit_to_show = ebit_backend  # already includes utlegg
        else:
            ebit_to_show = ebit_backend - utlegg_cost  # adjust to include utlegg

        # Row line
        row_line = (
            f"**{rowres.get('consultant_name', 'Konsulent')}** → **{rowres.get('project_name', 'Prosjekt')}** | "
            f"Inntekt: {income:,.0f} kr | Kostnad: {cost:,.0f} kr | "
            f"Utlegg: **{utlegg_cost:,.0f} kr** | "
            f"EBIT (inkl. utlegg): **{ebit_to_show:,.0f} kr**"
        ).replace(",", " ")
        st.write(row_line)

    # Totals
    st.write("---")
    st.subheader("Totalt – Avdeling")

    dept = data.get("department", {}) or {}
    dept_income = float(dept.get("income", 0.0))
    dept_cost = float(dept.get("cost", 0.0))
    dept_ebit_backend = float(dept.get("ebit", dept_income - dept_cost))

    if BACKEND_EBIT_INCLUDES_UTLEGG:
        dept_ebit_to_show = dept_ebit_backend
    else:
        dept_ebit_to_show = dept_ebit_backend - total_utlegg

    st.write(
        f"Inntekt: **{dept_income:,.0f} kr**, "
        f"Kostnad: **{dept_cost:,.0f} kr**, "
        f"Utlegg: **{total_utlegg:,.0f} kr**, "
        f"EBIT (inkl. utlegg): **{dept_ebit_to_show:,.0f} kr**"
        .replace(",", " ")
    )

    # Optional chart
    try:
        import plotly.graph_objects as go
        bars_x = ["EBIT (inkl. utlegg)", "Kostnad", "Inntekt", "Utlegg"]
        bars_y = [dept_ebit_to_show, dept_cost, dept_income, total_utlegg]
        colors = ["green", "red", "blue", "orange"]
        fig = go.Figure()
        fig.add_bar(x=bars_x, y=bars_y, marker_color=colors)
        fig.update_layout(
            title="EBIT (inkl. utlegg) vs Kostnad vs Inntekt vs Utlegg", yaxis_title="Beløp (NOK)")
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        st.info("Installer Plotly for graf: `pip install plotly`")
