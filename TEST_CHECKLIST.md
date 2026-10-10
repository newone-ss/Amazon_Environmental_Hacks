# Bhujal: Test Checklist & Verification Guide (Definition of Done)

> **Standard**: Concrete Verification Protocol for Software Changes  
> **Mandate**: **No change is "done" without running and verifying actual commands against actual expected outputs.**  
> **Rule**: *AI claiming success and code actually working are two different facts. This file is how you stop confusing them.*

---

## 1. Why It Matters: The Anti-"Vibe Check" Philosophy

When autonomous agents or developers claim a feature is "implemented", "completed", or "working", that claim is an unverified hypothesis. In real production systems, code fails in subtle ways that surface only upon rigorous execution:

1. **Python Runtime Discrepancies**: Code utilizing Python 3.11 features (such as `from datetime import UTC`) fatally crashes with `ImportError` on Python 3.10 environments if safe fallbacks (`timezone.utc`) are omitted.
2. **Encoding Traps**: Printing Unicode glyphs (such as `₹` instead of `INR`) causes fatal `UnicodeEncodeError: 'charmap'` crashes on standard Windows consoles (`cp1252`).
3. **Hidden / Silent 500 Errors**: An API route might return HTTP 500 due to an unhandled optional library (such as `python-docx`) while the server itself appears to be running.
4. **Vibe Check Fallacy**: Skimming code or seeing green syntax highlighting is not verification. Only explicit process execution with status code assertions, stdout regex matching, and invariant validation counts as proof of correctness.

Every pull request, architectural change, or agent task **must satisfy all 7 Verification Gates** below before being declared complete.

---

## 2. The 7 Verification Gates

```
+---------------------------------------------------------------------------------+
| Gate 1: Pre-Flight & Environment Sanity (Python, dependencies, virtualenv)      |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 2: Code Quality & Static Analysis (ruff check, ruff format, mypy)          |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 3: Automated Pytest Suite (100% pass across 47 tests)                      |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 4: Deterministic Scoring & Physical Invariants (13 sites, safety vetoes)   |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 5: CLI Workflows (list, evaluate, simulate, report, dpr, pathways)        |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 6: REST API Contracts & Endpoint Invariants (FastAPI TestClient / curl)   |
+---------------------------------------------------------------------------------+
                                       |
                                       v
+---------------------------------------------------------------------------------+
| Gate 7: Git Hygiene & Secret Scanning (zero credentials, clean status)          |
+---------------------------------------------------------------------------------+
```

---

### Gate 1: Pre-Flight & Environment Sanity

Ensure that the environment runs an approved Python interpreter and all core dependencies are installed.

#### Verification Command
```bash
python --version
pip show pydantic fastapi uvicorn python-docx openpyxl pytest ruff
```

#### Expected Output
* **Python Version**: `Python 3.10.x` or `Python 3.11.x`.
* **Exit Code**: `0`.
* **Required Package Presence**: All listed packages show valid installed version paths (no `WARNING: Package(s) not found`).

---

### Gate 2: Code Quality & Static Analysis

Ensure all files adhere to PEP 8 standards, formatting rules, and static type invariants.

#### Verification Command
```bash
# 1. Lint checks
ruff check .

# 2. Format checks
ruff format --check .

# 3. Type checks on core engines
mypy scoring/ backend/ --ignore-missing-imports
```

#### Expected Output
* `ruff check .`: Output ends with `All checks passed!` and Exit Code `0`.
* `ruff format --check .`: Output ends with `XX files already formatted` and Exit Code `0`.
* `mypy`: In CI, failsafe flags exist, but local changes must not introduce new type regressions into `scoring/` or `backend/models.py`.

---

### Gate 3: Automated Pytest Suite

Run the complete test suite spanning data contracts, scoring engines, multi-agent collective, and FastAPI REST endpoints.

#### Verification Command
```bash
python -m pytest tests/ -v --tb=short
```

#### Expected Output
* **Total Collected**: 47 items.
* **Result**: `47 passed` in $< 10.0$ seconds.
* **Exit Code**: `0`.
* **Failure Count**: `0 failed, 0 errors`.

#### Module Breakdown Matrix
| Test Suite | File | Tests | Key Invariants Verified |
|---|---|:---:|---|
| Models Contract | `tests/test_models.py` | 12 | Pydantic v2 schema bounds ($0 \le score \le 100$), serialization invariance, bounds validation |
| Scoring Engine | `tests/test_scoring.py` | 13 | Monotonicity with slope, safety vetoes (`SLOPE_STEEP`, `LANDSLIDE_ZONE`), zero interventions on veto |
| Multi-Agent Collective | `tests/test_agents.py` | 7 | Domain specialist agents, Lead Orchestrator synthesis, HTML action report generation |
| REST API Endpoints | `tests/test_api.py` | 15 | Status 200 on all routes, village state filters, CRUD on observations, DPR ZIP generation |

---

### Gate 4: Deterministic Scoring & Physical Invariants

Verify that the deterministic calculation engine evaluates all 13 curated settlements across Odisha, Madhya Pradesh, and Jharkhand without runtime exceptions or missing keys.

#### Verification Command
```bash
python -m scoring.run
```

#### Expected Output
* **Exit Code**: `0`.
* **Output Snippet**:
```text
Executing deterministic scoring across 13 demonstration sites...
================================================================================
Site ID    Name             Safety       Recharge   Stress     Spring Drying
--------------------------------------------------------------------------------
site_001   Laxmipur         SAFE         72.4       35.4       33.0
site_002   Mundaguda        REJECTED     43.8       58.0       N/A
site_003   Parajam          REJECTED     61.2       66.5       12.2
site_004   Dukum            SAFE         61.9       49.8       73.4
site_005   Kotpad Town      SAFE         70.0       53.6       N/A
site_mp_001 Bichhiya         SAFE         69.8       55.2       N/A
site_mp_002 Samnapur         SAFE         66.2       43.7       57.4
site_mp_003 Meghnagar        SAFE         60.5       85.8       N/A
site_mp_004 Bajag Scarp      REJECTED     48.2       53.3       N/A
site_jh_001 Torpa            SAFE         75.0       46.2       N/A
site_jh_002 Goilkera         SAFE         66.7       43.3       51.2
site_jh_003 Chaibasa Plain   SAFE         65.9       71.6       N/A
site_jh_004 Porahat Scarp    REJECTED     44.5       61.4       N/A
================================================================================
Scoring run completed successfully.
```

#### Invariant Assertions to Inspect
1. **Physical Score Ceiling**: All scores are $\ge 0.0$ and $\le 100.0$.
2. **Geotechnical Veto Guarantee**:
   * `site_mp_004` (Bajag Scarp, slope $39.5^\circ$) **must** output `REJECTED`.
   * `site_jh_004` (Porahat Scarp, slope $42.0^\circ$) **must** output `REJECTED`.
   * `site_002` (Mundaguda, landslide susceptibility) **must** output `REJECTED`.
3. **Weight Summation**: Factor weights in `config/weights.yaml` sum to exactly $1.00$.

---

### Gate 5: CLI Workflows & Smoke Tests

Verify every primary command in `main.py` functions end-to-end without unhandled traceback.

#### 5.1. List Demonstration Villages
```bash
python main.py list
```
* **Expected**: Tabular list of 13 settlements with columns `ID`, `Name`, `District`, `State`, `Elev (m)`, `Spring`.
* **Exit Code**: `0`.

#### 5.2. Evaluate Cleared vs. Vetoed Sites
```bash
# Cleared site
python main.py evaluate site_001

# Geotechnically vetoed site
python main.py evaluate site_mp_004
```
* **Expected (`site_001`)**: `Geotechnical Safety Veto: Status: SAFE`, recommended structures include `Check Dam (Nala Bund)` with cost range in INR and labour days.
* **Expected (`site_mp_004`)**: `Status: REJECTED`, `Triggered Rules: SLOPE_STEEP, LANDSLIDE_ZONE`, `No civil structures cleared for construction.`
* **Exit Code**: `0`.

#### 5.3. Dynamic Rainfall Perturbation Simulation
```bash
python main.py simulate site_001 --rainfall 0.8 --intervention check_dam
```
* **Expected**:
  * Recharge score adjusts with baseline vs adjusted delta.
  * Exit Code: `0`.

#### 5.4. Planner Action Dossier Generation
```bash
python main.py report --sites site_001
```
* **Expected**: Prints `Action Dossier Generated Successfully`, report file exists in `data/reports/rpt_*.html`.
* **Exit Code**: `0`.

#### 5.5. Adaptation Pathways Generation
```bash
# Generate pathway for site under SSP2-4.5
python main.py pathways generate site_001

# Compare pathways across SSP scenarios
python main.py pathways compare site_001
```
* **Expected**: Adaptation Pathway table spanning 2025–2050 timeline; SSP Comparison matrix with Success %, Total Cost, Final Recharge, Final Stress.
* **Exit Code**: `0`.

#### 5.6. DPR (Detailed Project Report) Package Generation
```bash
python main.py dpr generate --sites site_001 --output test_dpr.zip
```
* **Expected**: Prints `DPR Package Generated Successfully!`, shows `Contents: DOCX, XLSX, KML`.
* **Exit Code**: `0`.
* **Clean up**: `rm test_dpr.zip` (PowerShell/Bash).

---

### Gate 6: REST API Contracts & Endpoint Verification

Verify the FastAPI application handles ingress requests deterministically.

#### Verification Script (Automated TestClient Execution)
Run this single-line verification script in terminal:
```bash
python -c "
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

# 1. System Metadata
r = client.get('/meta')
assert r.status_code == 200, f'/meta failed: {r.status_code}'
assert r.json()['total_villages'] == 13
print('[PASS] GET /meta')

# 2. Village Directory & Regional Filtering
r = client.get('/villages')
assert r.status_code == 200 and len(r.json()) == 13
r_od = client.get('/villages?state=Odisha')
assert r_od.status_code == 200 and len(r_od.json()) == 5
r_mp = client.get('/villages?state=Madhya Pradesh')
assert r_mp.status_code == 200 and len(r_mp.json()) == 4
r_jh = client.get('/villages?state=Jharkhand')
assert r_jh.status_code == 200 and len(r_jh.json()) == 4
print('[PASS] GET /villages (All + State Filters: Odisha=5, MP=4, JH=4)')

# 3. Comprehensive Site Evaluation
r = client.get('/sites/site_001')
assert r.status_code == 200 and r.json()['safety_verdict']['status'] == 'SAFE'
r_veto = client.get('/sites/site_mp_004')
assert r_veto.status_code == 200 and r_veto.json()['safety_verdict']['status'] == 'REJECTED'
print('[PASS] GET /sites/{id} (SAFE vs REJECTED)')

# 4. Scenario Simulation
r = client.post('/scenarios', json={'site_id': 'site_001', 'rainfall_fraction': 0.85})
assert r.status_code == 200 and 'deltas' in r.json()
print('[PASS] POST /scenarios')

# 5. DPR Scheme Catalog & Package
r = client.get('/dpr/schemes')
assert r.status_code == 200 and 'intervention_schemes' in r.json()
r_dpr = client.post('/dpr/generate', data={'site_ids': 'site_001', 'project_name': 'CI Test'})
assert r_dpr.status_code == 200 and 'zip_base64' in r_dpr.json()
print('[PASS] /dpr/schemes and /dpr/generate')

print('\nALL API CONTRACTS VERIFIED SUCCESSFULLY!')
"
```

#### Expected Output
* All 5 blocks emit `[PASS]`.
* Output ends with `ALL API CONTRACTS VERIFIED SUCCESSFULLY!`.
* Exit Code: `0`.

---

### Gate 7: Git Hygiene & Secret Scanning

Prevent unintended file leaks, broken states, or secret exposure.

#### Verification Command
```bash
git status
```

#### Invariant Checks
1. **No Tracked Secrets**: Ensure `.env` is never staged or committed (only `.env.example`).
2. **No Ephemeral Blobs**: Ensure no generated `.zip`, `.html` test dossiers, `.pytest_cache`, or `__pycache__` folders are unstaged or untracked.
3. **No Unintended Edits**: Run `git diff` to confirm only the expected files are modified.

---

## 3. Pull Request & Handoff Verification Checklist

Copy and paste this checklist into every GitHub Pull Request description or agent execution summary:

```markdown
### Verification Checklist (Definition of "Done")

- [ ] **Gate 1: Environment & Dependencies**
  - [ ] Tested on target Python runtime (Python 3.10 / 3.11)
  - [ ] Required dependencies installed (`python-docx`, `openpyxl`, `fastapi`, `pydantic`)
- [ ] **Gate 2: Code Quality & Linters**
  - [ ] `ruff check .` returns 0 errors
  - [ ] `ruff format --check .` passes
  - [ ] `mypy scoring/ backend/ --ignore-missing-imports` passes without new regressions
- [ ] **Gate 3: Automated Unit & Integration Tests**
  - [ ] `python -m pytest tests/ -v` passes 100% (47/47 tests green)
  - [ ] Zero skipped tests, zero unhandled collection errors
- [ ] **Gate 4: Deterministic Scoring & Physical Invariants**
  - [ ] `python -m scoring.run` executes across all 13 sites
  - [ ] All scores bounded in [0.0, 100.0]
  - [ ] Geotechnical vetoes enforced (`site_002`, `site_mp_004`, `site_jh_004` strictly REJECTED)
- [ ] **Gate 5: Command-Line Interface (CLI)**
  - [ ] `python main.py list` lists all 13 settlements
  - [ ] `python main.py evaluate <site_id>` works for cleared & vetoed sites
  - [ ] `python main.py simulate <site_id> --rainfall <fraction>` executes cleanly
  - [ ] `python main.py dpr generate --sites <site_ids>` generates valid ZIP package
  - [ ] No Unicode/charmap stdout crashes on Windows (uses `INR` instead of raw symbol)
- [ ] **Gate 6: API Service Contracts**
  - [ ] `GET /meta` returns valid schema and `supported_states`
  - [ ] `GET /villages` supports state filtering (`Odisha`, `Madhya Pradesh`, `Jharkhand`)
  - [ ] `POST /dpr/generate` and `POST /dpr/download` return 200 with valid binary/base64
- [ ] **Gate 7: Git & Repository Hygiene**
  - [ ] Zero uncommitted test artifacts, zero committed credentials or keys
  - [ ] `git status` clean and verified
```

---

## 4. Troubleshooting & Diagnostic Matrix

| Symptom / Error | Root Cause | Exact Remediation Command |
|---|---|---|
| `ImportError: cannot import name 'UTC' from 'datetime'` | Python 3.10 runtime does not export `UTC` from `datetime` (added in 3.11). | Use `try: from datetime import UTC except ImportError: UTC = timezone.utc  # noqa: UP017` |
| `UnicodeEncodeError: 'charmap' codec can't encode character '\u20b9'` | Windows standard console (`cp1252`) cannot render Indian Rupee symbol `₹`. | Replace `₹` with `INR` in CLI print statements. |
| `RuntimeError: python-docx is required for Word document generation` (HTTP 500 on `/dpr/generate`) | Missing optional dependency `python-docx`. | Run `pip install python-docx` and verify `requirements.txt`. |
| `AssertionError: assert 500 == 200` in `test_dpr_generate` | Word document generation failure inside `dpr_generator.py`. | Ensure `python-docx` is installed and run `python -m pytest tests/test_api.py -k dpr -vv --tb=long`. |
| `UP017 Use 'datetime.UTC' alias` in `ruff check` | Ruff pyupgrade rule flagging `timezone.utc` under Python 3.11 target. | Append `# noqa: UP017` to the Python 3.10 fallback line. |
| Test collection fails with missing module | Working directory is not project root or virtualenv is inactive. | Run `cd /path/to/Amazon_Environmental_Hacks` and execute via `python -m pytest tests/`. |
