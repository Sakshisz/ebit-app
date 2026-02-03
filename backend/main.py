
# backend/main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional
import json
import os
import threading
import random

# ------------------------------
# FIL-LAGRING
# ------------------------------
DATA_DIR = "data"
CONSULTANTS_FILE = os.path.join(DATA_DIR, "consultants.json")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.json")
SETTINGS_FILE = os.path.join(DATA_DIR, "settings.json")
_lock = threading.Lock()


def _ensure_data():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(CONSULTANTS_FILE):
        with open(CONSULTANTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_id": 0, "items": []}, f,
                      ensure_ascii=False, indent=2)
    if not os.path.exists(PROJECTS_FILE):
        with open(PROJECTS_FILE, "w", encoding="utf-8") as f:
            json.dump({"last_id": 0, "items": []}, f,
                      ensure_ascii=False, indent=2)
    if not os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump({
                "pex_pct": 0.32,
                "expense_pct": 0.40,
                "yearly_work_hours": 1625
            }, f, ensure_ascii=False, indent=2)


def _load(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _save(path: str, data: dict):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


_ensure_data()

# ------------------------------
# APP + CORS
# ------------------------------
app = FastAPI(title="EBIT Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # stram inn i prod
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ------------------------------
# MODELLER
# ------------------------------


class ConsultantIn(BaseModel):
    name: str
    salary: float = Field(ge=0)
    default_utilization: Optional[float] = Field(default=0.8, ge=0, le=1)


class Consultant(ConsultantIn):
    id: int


class ConsultantUpdate(BaseModel):
    name: Optional[str] = None
    salary: Optional[float] = Field(default=None, ge=0)
    default_utilization: Optional[float] = Field(default=None, ge=0, le=1)


class ProjectIn(BaseModel):
    name: str
    hourly_rate: float = Field(ge=0)


class Project(ProjectIn):
    id: int


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    hourly_rate: Optional[float] = Field(default=None, ge=0)


class Assignment(BaseModel):
    row_index: Optional[int] = None
    consultant_id: int
    project_id: int
    utilization: float = Field(ge=0, le=1)
    project_percent: float = Field(ge=0, le=1)
    consultant_work_pct: Optional[float] = Field(default=1.0, ge=0, le=1)
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    utlegg_mode: Optional[str] = None
    expense_pct: Optional[float] = Field(default=None, ge=0)


class CalculateInput(BaseModel):
    assignments: List[Assignment]
    yearly_work_hours: Optional[float] = None
    pex_pct: Optional[float] = None
    expense_pct: Optional[float] = None
    month: Optional[int] = Field(default=None, ge=1, le=12)


class Settings(BaseModel):
    pex_pct: float = Field(0.32, ge=0, le=1)
    expense_pct: float = Field(0.40, ge=0, le=1)
    yearly_work_hours: float = Field(1625, ge=500, le=3000)

# ------------------------------
# HELSE
# ------------------------------


@app.get("/health")
def health():
    return {"status": "ok"}

# ------------------------------
# SETTINGS
# ------------------------------


@app.get("/settings", response_model=Settings)
def get_settings():
    return _load(SETTINGS_FILE)


@app.post("/settings", response_model=Settings)
def save_settings(s: Settings):
    with _lock:
        _save(SETTINGS_FILE, s.dict())
    return s

# ------------------------------
# KONSULENTER
# ------------------------------


@app.get("/consultants", response_model=List[Consultant])
def get_consultants():
    data = _load(CONSULTANTS_FILE)["items"]
    return sorted(data, key=lambda x: x["id"])


@app.post("/consultants", response_model=Consultant)
def create_consultant(c: ConsultantIn):
    with _lock:
        data = _load(CONSULTANTS_FILE)
        new_id = data["last_id"] + 1
        item = {"id": new_id, **c.dict()}
        data["last_id"] = new_id
        data["items"].append(item)
        _save(CONSULTANTS_FILE, data)
    return item


@app.patch("/consultants/{cid}", response_model=Consultant)
def update_consultant(cid: int, upd: ConsultantUpdate):
    with _lock:
        data = _load(CONSULTANTS_FILE)
        for item in data["items"]:
            if item["id"] == cid:
                for k, v in upd.dict(exclude_unset=True).items():
                    if v is not None:
                        item[k] = v
                _save(CONSULTANTS_FILE, data)
                return item
    raise HTTPException(404, f"Konsulent {cid} ikke funnet")


@app.delete("/consultants/{cid}")
def delete_consultant(cid: int):
    with _lock:
        data = _load(CONSULTANTS_FILE)
        before = len(data["items"])
        data["items"] = [x for x in data["items"] if x["id"] != cid]
        if len(data["items"]) == before:
            raise HTTPException(404, f"Konsulent {cid} ikke funnet")
        _save(CONSULTANTS_FILE, data)
    return {"status": "deleted", "id": cid}


class ConsultantsBulk(BaseModel):
    items: List[ConsultantIn]


@app.post("/consultants/bulk", response_model=List[Consultant])
def create_consultants_bulk(payload: ConsultantsBulk):
    out = []
    with _lock:
        data = _load(CONSULTANTS_FILE)
        for c in payload.items:
            new_id = data["last_id"] + 1
            item = {"id": new_id, **c.dict()}
            data["last_id"] = new_id
            data["items"].append(item)
            out.append(item)
        _save(CONSULTANTS_FILE, data)
    return out

# ------------------------------
# PROSJEKTER
# ------------------------------


@app.get("/projects", response_model=List[Project])
def get_projects():
    data = _load(PROJECTS_FILE)["items"]
    return sorted(data, key=lambda x: x["id"])


@app.post("/projects", response_model=Project)
def create_project(p: ProjectIn):
    with _lock:
        data = _load(PROJECTS_FILE)
        new_id = data["last_id"] + 1
        item = {"id": new_id, **p.dict()}
        data["last_id"] = new_id
        data["items"].append(item)
        _save(PROJECTS_FILE, data)
    return item


@app.patch("/projects/{pid}", response_model=Project)
def update_project(pid: int, upd: ProjectUpdate):
    with _lock:
        data = _load(PROJECTS_FILE)
        for item in data["items"]:
            if item["id"] == pid:
                for k, v in upd.dict(exclude_unset=True).items():
                    if v is not None:
                        item[k] = v
                _save(PROJECTS_FILE, data)
                return item
    raise HTTPException(404, f"Prosjekt {pid} ikke funnet")


@app.delete("/projects/{pid}")
def delete_project(pid: int):
    with _lock:
        data = _load(PROJECTS_FILE)
        before = len(data["items"])
        data["items"] = [x for x in data["items"] if x["id"] != pid]
        if len(data["items"]) == before:
            raise HTTPException(404, f"Prosjekt {pid} ikke funnet")
        _save(PROJECTS_FILE, data)
    return {"status": "deleted", "id": pid}


class ProjectsBulk(BaseModel):
    items: List[ProjectIn]


@app.post("/projects/bulk", response_model=List[Project])
def create_projects_bulk(payload: ProjectsBulk):
    out = []
    with _lock:
        data = _load(PROJECTS_FILE)
        for p in payload.items:
            new_id = data["last_id"] + 1
            item = {"id": new_id, **p.dict()}
            data["last_id"] = new_id
            data["items"].append(item)
            out.append(item)
        _save(PROJECTS_FILE, data)
    return out


# ------------------------------
# SEED (eksempeldata) — fleksibel 5–25
# ------------------------------
_FIRST_NAMES = ["Ola", "Kari", "Per", "Anne",
                "Lars", "Eva", "Nora", "Mats", "Sofie", "Henrik"]
_LAST_NAMES = ["Nordmann", "Hansen", "Larsen",
               "Johansen", "Andersen", "Pedersen"]


@app.post("/seed/consultants")
def seed_consultants(count: int = Query(10, ge=5, le=25), reset: bool = False):
    with _lock:
        data = _load(CONSULTANTS_FILE)
        if reset:
            data = {"last_id": 0, "items": []}
        for _ in range(count):
            name = f"{random.choice(_FIRST_NAMES)} {random.choice(_LAST_NAMES)}"
            salary = random.randint(600_000, 900_000)
            util = round(random.uniform(0.7, 0.9), 2)
            new_id = data["last_id"] + 1
            data["items"].append(
                {"id": new_id, "name": name, "salary": salary, "default_utilization": util})
            data["last_id"] = new_id
        _save(CONSULTANTS_FILE, data)
        total = len(data["items"])
    return {"status": "ok", "added": count, "total": total, "reset": reset}


@app.post("/seed/projects")
def seed_projects(count: int = Query(10, ge=5, le=25), reset: bool = False):
    with _lock:
        data = _load(PROJECTS_FILE)
        if reset:
            data = {"last_id": 0, "items": []}
        for i in range(count):
            name = f"Prosjekt {random.choice(['Alpha', 'Beta', 'Gamma', 'Delta', 'Omega'])}-{random.randint(1, 99)}"
            rate = random.choice([1100, 1200, 1300, 1400, 1500, 1600])
            new_id = data["last_id"] + 1
            data["items"].append(
                {"id": new_id, "name": name, "hourly_rate": rate})
            data["last_id"] = new_id
        _save(PROJECTS_FILE, data)
        total = len(data["items"])
    return {"status": "ok", "added": count, "total": total, "reset": reset}

# (Behold felles seed begge dersom ønskelig)


@app.post("/seed")
def seed_both():
    seed_consultants(count=10, reset=True)
    seed_projects(count=10, reset=True)
    return {"status": "ok"}

# ------------------------------
# BEREGNING
# ------------------------------


@app.post("/calculate-ebit")
def calculate_ebit(body: CalculateInput):
    settings = _load(SETTINGS_FILE)
    yearly_work_hours = body.yearly_work_hours or settings["yearly_work_hours"]
    pex_pct = settings["pex_pct"] if body.pex_pct is None else body.pex_pct
    expense_pct = settings["expense_pct"] if body.expense_pct is None else body.expense_pct

    consultants = {c["id"]: c for c in _load(CONSULTANTS_FILE)["items"]}
    projects = {p["id"]: p for p in _load(PROJECTS_FILE)["items"]}

    results = []
    total_income = 0.0
    total_cost = 0.0
    total_ebit = 0.0

    for a in body.assignments:
        if a.consultant_id not in consultants:
            raise HTTPException(
                404, f"Konsulent {a.consultant_id} finnes ikke")
        if a.project_id not in projects:
            raise HTTPException(404, f"Prosjekt {a.project_id} finnes ikke")

        c = consultants[a.consultant_id]
        p = projects[a.project_id]

        billable_hours = yearly_work_hours * a.utilization * a.project_percent
        income = billable_hours * p["hourly_rate"]
        cost = c["salary"] * (1 + pex_pct + expense_pct)
        ebit = income - cost

        results.append({
            "consultant_id": c["id"],
            "consultant_name": c["name"],
            "project_id": p["id"],
            "project_name": p["name"],
            "billable_hours": billable_hours,
            "income": income,
            "cost": cost,
            "ebit": ebit
        })

        total_income += income
        total_cost += cost
        total_ebit += ebit

    return {
        "settings_used": {
            "yearly_work_hours": yearly_work_hours,
            "pex_pct": pex_pct,
            "expense_pct": expense_pct
        },
        "results": results,
        "department": {
            "income": total_income,
            "cost": total_cost,
            "ebit": total_ebit
        }
    }
