# T.H.E.M.I.S

**Tender Human-in-the-loop Evaluation & Misconduct Inspection System**

A multi-agent AI system that automates public-procurement evaluation under India's General Financial Rules (GFR 2017): eligibility verification, blind technical scoring, price schedule recomputation, fraud/collusion detection, QCBS ranking, human-in-the-loop clarification loops, and a tamper-evident SHA-256 audit trail. Built using **Microsoft Semantic Kernel** and powered by high-throughput Groq models (`openai/gpt-oss-120b`).

![Dashboard](docs/screenshots/dashboard.png)

---

## Key Features & Innovations

### 1. Multi-Agent Collaborative Architecture (Fan-out / Fan-in)
The system coordinates specialized autonomous agents executing through Microsoft Semantic Kernel plugins:
- **Tender Requirements Retrieval Agent:** Parses tender notices into formal JSON rubrics with mandatory eligibility criteria ($E_1 \dots E_n$), weighted technical criteria ($T_1 \dots T_m$), and QCBS weights.
- **Compliance Scrutiny Agent:** Performs grounded BM25 RAG retrieval over each bidder's submission. Every verdict (`PASS`, `FAIL`, `UNCLEAR`) is anchored to a verbatim cited quote from the bid, verified by string search.
- **Technical Evaluator Agent (Rubric Critic):** Evaluates proposals against technical rubrics using blind anonymization (`Bidder-A`, `Bidder-B`). Identities are cryptographically masked until unblinded by human committee action.
- **Financial Evaluator Agent:** Extracts unit prices and quantities, and executes deterministic Python arithmetic tools to recompute line items and verify quoted totals.
- **Risk & Collusion Agent:** Scans for text plagiarism across bids using 5-word shingle Jaccard similarity, detects abnormally low/high price outliers against median benchmarks, and flags ghost project claims.
- **Chair & Procurement Manager Agent:** Ranks qualified bidders using Quality and Cost Based Selection (QCBS), drafts formal rulings for each risk flag, and recommends contract awards.
- **Clarification Loop Agent:** Detects `UNCLEAR` mandatory requirements, drafts formal vendor clarification notices, and automatically re-scores submissions upon receipt of vendor replies.

```
                    ┌──────────────────────────┐
                    │      Tender Document     │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  Tender Parser (Rubric)  │
                    └────────────┬─────────────┘
                                 │
             ┌───────────────────┴───────────────────┐
             │       FAN-OUT (Parallel Execution)    │
             ▼                                       ▼
    ┌─────────────────┐                     ┌─────────────────┐
    │ Compliance Agent│                     │ Compliance Agent│
    │   (Bidder 1)    │                     │   (Bidder N)    │
    └────────┬────────┘                     └────────┬────────┘
             │                                       │
             │ (If UNCLEAR: Clarification Loop)      │
             ▼                                       ▼
    ┌─────────────────┐                     ┌─────────────────┐
    │ Technical Agent │                     │ Technical Agent │
    │ (Blind Critic)  │                     │ (Blind Critic)  │
    └────────┬────────┘                     └────────┬────────┘
             │                                       │
             └───────────────────┬───────────────────┘
                                 │
                                 ▼ FAN-IN
                    ┌──────────────────────────┐
                    │ Financial Evaluator Tool │
                    │  (Arithmetic Recompute)  │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │   Risk & Fraud Detector  │
                    │ (Collusion & Outliers)   │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  Chair & QCBS Ranking    │
                    │   (Award Recommendation) │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                    ┌──────────────────────────┐
                    │  Human Committee Sign-off│
                    │  (SHA-256 Sealed Audit)  │
                    └──────────────────────────┘
```

---

### 2. Framework-Based Development: Microsoft Semantic Kernel
The agent system is built on **Microsoft Semantic Kernel (v1.47.0)** (`backend/app/sk_kernel.py`):
- **Core AI Connector:** Integrated with Groq's OpenAI-compatible chat completion service (`OpenAIChatCompletion`) running `openai/gpt-oss-120b`.
- **Specialized Kernel Plugins:**
  - `RetrievalPlugin`: Grounded BM25 search and quote verification tools registered via `@kernel_function`.
  - `FinancialArithmeticPlugin`: Exact deterministic line-item multiplication and summation tools preventing LLM math hallucinations.
  - `TenderParserPlugin`: Prompt formatting and rubric generation.
  - `ClarificationAgentPlugin`: Formal vendor inquiry formatting and criterion re-scoring.
- **Framework Telemetry:** Exposed via `/api/health` displaying active plugins and Semantic Kernel version.

---

### 3. Automated Human-in-the-Loop Clarification Loop
When a bidder's documentation is ambiguous on a mandatory eligibility requirement, the system does not prematurely disqualify or guess. Instead, it enters an automated clarification cycle:
1. **Trigger:** The Compliance Agent flags a criterion as `UNCLEAR` (verdict: `NEEDS_HUMAN_REVIEW`).
2. **AI Question Drafting:** The Clarification Agent (`backend/app/agents/clarification.py`) drafts a formal, legally grounded clarification letter specifying:
   - The exact tender clause and requirement.
   - The specific document or certificate missing.
   - The required format of the response.
3. **Human Action:** The Evaluation Officer reviews the drafted question in the Compliance Matrix drawer and submits the vendor's reply.
4. **Automated Re-Scoring:** The Clarification Agent retrieves evidence combining the original bid and the vendor's clarification statement, re-evaluating the criterion to `PASS`, `FAIL`, or `UNCLEAR`.
5. **State Cascade:** If all criteria pass, the bidder's status automatically promotes to `ELIGIBLE` and triggers a recalculation of QCBS rankings.
6. **Audit Hash Chain:** Every stage (question drafted, reply submitted, re-score rendered) is permanently written to the tamper-evident SHA-256 audit ledger.

---

### 4. 5-Tender Synthetic Benchmark Suite
To validate evaluation accuracy and fraud detection, T.H.E.M.I.S includes a 5-tender benchmark dataset (`backend/app/benchmark_data.py`) spanning different procurement sectors, with 3–4 synthetic bids each and designated winning bids:

| # | Sector & Tender Title | Issuing Body | Bids | Designated Winner | Planted Issues & Disqualifications |
|---|---|---|:---:|---|---|
| **1** | **IoT Water Quality Telemetry** (PHED/IOT/2026/017) | Dept of Rural Water Supply, Punjab | 4 | `SecureFlow Technologies` | • `HydroNova`: Turnover below threshold, missing ISO 9001 (**Disqualified**)<br>• `AquaSense`: Text plagiarized from SecureFlow, abnormally low price<br>• `BlueRiver`: Price table line-item sum mismatch |
| **2** | **Rural Road Network (45 km)** (PWD/ROAD/2026/042) | Public Works Dept, Himachal Pradesh | 3 | `RoadBuild Pro Pvt Ltd` | • `ConstructEase`: Turnover INR 12 Cr vs 20 Cr threshold (**Disqualified**)<br>• `Pavement Masters`: Ambiguous bank solvency certificate |
| **3** | **Citizen Services IT Portal** (NIC/GOV/2026/089) | National Informatics Centre (MeitY) | 4 | `TechForge Solutions` | • `DevNest Technologies`: Missing GST registration certificate (**Disqualified**)<br>• `SoftWave India`: Near-identical plagiarized technical proposal<br>• `CodeMatrix`: INR 16.6 Cr discrepancy in quoted total |
| **4** | **Medical Diagnostic Equipment** (AIIMS/MED/2026/156) | AIIMS, New Delhi | 3 | `MedSupply Pharma` | • `HealthFirst Devices`: ISO 13485 certificate expired (**Disqualified**)<br>• `CurePoint India`: Abnormally low price (58% below median) |
| **5** | **Rooftop Solar PV (10 MW)** (MNRE/SOLAR/2026/203) | Ministry of New & Renewable Energy | 4 | `SolarEdge Power` | • `GreenVolt Systems`: Debarment self-declaration missing (**Disqualified**)<br>• `PhotonWorks`: INR 44.5 Cr arithmetic total error<br>• `SunRay Infra`: Ambiguous plant commissioning certificates |

#### Benchmark Runner (`backend/benchmark.py`)
Run the automated benchmark across all 5 tenders or individual tenders:
```bash
# Run all 5 tenders
cd backend
.\.venv\Scripts\python benchmark.py

# Run a specific tender (e.g. Tender 3)
.\.venv\Scripts\python benchmark.py --tender 3

# Export detailed benchmark report as JSON
.\.venv\Scripts\python benchmark.py --output benchmark_results.json
```
The script evaluates:
- **Top-Ranked Winner Accuracy:** Verifies whether the committee's QCBS Rank #1 matches the known winner.
- **Disqualification Detection Rate:** Verifies that 100% of non-compliant bids are disqualified with exact clause citations ($E_1 \dots E_7$).

---

## Quick Start

### Prerequisites
- Python 3.10+ (Windows, macOS, or Linux)
- A Groq API key (`https://console.groq.com`)

### 1. Setup & Launch
```bash
# Clone the repository
git clone https://github.com/your-org/themis.git
cd themis

# Windows
run.bat

# macOS / Linux
./run.sh
```
The script creates the `.venv`, installs dependencies (including `semantic-kernel` and `fastapi`), and starts the server at **http://localhost:8000**.

### 2. Configure Groq API Key
Add your key to `.env`:
```env
GROQ_API_KEY=gsk_your_groq_api_key_here
THEMIS_MODEL=openai/gpt-oss-120b
```

---

## System Architecture & Workflow

1. **Intake & Hashing:** Upload tender notice and bidder proposals (`.pdf`, `.txt`, `.md`). Each document is hashed (SHA-256) on upload.
2. **Tender Rubric Extraction:** Extracts qualification rules, passing scores, and evaluation weights.
3. **Parallel Compliance Scrutiny:** Runs BM25 RAG over all bids in parallel; checks incorporation, turnover, prior experience, GST/PAN, ISO certifications, EMD, and non-blacklisting declarations.
4. **Blind Technical Evaluation:** Evaluates methodology, team, hardware/software specs, timelines, and maintenance plans on anonymized text.
5. **Deterministic Price Recomputation:** Arithmetic tools re-calculate each bidder's line items ($\text{Qty} \times \text{Unit Price}$) and compare with stated totals.
6. **Misconduct & Risk Inspection:** Scans for text collusion, abnormally low pricing (predatory bidding), and arithmetic manipulation.
7. **Chair Decisions:** Rulings are issued for all flags (`NO_ACTION`, `REQUEST_CLARIFICATION`, `PENALIZE_10`, `PENALIZE_25`, `RECOMMEND_DISQUALIFY`).
8. **QCBS Formula Scoring:**
   $$\text{Final Score} = (\text{Technical Score} \times W_{\text{tech}}) + \left(\frac{\text{Lowest Price}}{\text{Bidder Price}} \times 100 \times W_{\text{fin}}\right)$$
9. **Human Committee Approval:** The evaluation officer reviews rulings, resolves blockers, and applies a cryptographically sealed approval stamp.
10. **Tamper-Evident Audit Verification:** Every action is linked in a SHA-256 hash chain that can be independently verified with one click.

---

## API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| `GET` | `/api/health` | System status, Groq connection, and Semantic Kernel plugins |
| `GET` | `/api/sessions` | List all evaluation sessions |
| `POST` | `/api/sessions` | Multipart upload for tender and bidder files |
| `POST` | `/api/sessions/demo` | Staging of demo evaluation session |
| `POST` | `/api/sessions/{id}/run` | Starts multi-agent evaluation pipeline |
| `GET` | `/api/sessions/{id}/events` | Server-Sent Events (SSE) live execution stream |
| `GET` | `/api/sessions/{id}` | Complete evaluation data (rubric, compliance, technical, rankings) |
| `POST` | `/api/sessions/{id}/clarifications/draft` | AI drafts formal clarification question for unclear criterion |
| `POST` | `/api/sessions/{id}/clarifications/reply` | Submits vendor response and triggers automatic criterion re-scoring |
| `GET` | `/api/sessions/{id}/clarifications` | Returns all drafted questions, vendor replies, and re-scored verdicts |
| `POST` | `/api/sessions/{id}/rulings` | Concur or override Chair risk rulings |
| `POST` | `/api/sessions/{id}/approval` | Final committee sign-off (gated against unresolved blockers) |
| `DELETE` | `/api/sessions/{id}` | Deletes run data to start fresh evaluation |
| `GET` | `/api/sessions/{id}/audit/verify` | Recomputes SHA-256 audit ledger from genesis block |
| `GET` | `/api/sessions/{id}/export/{kind}` | Export `report.md`, `ranking.csv`, `audit.json`, or `full.json` |

---

## Automated Test Suite

Run the full pytest suite (10 tests covering the pipeline, security, Semantic Kernel, and benchmark data structure):

```bash
cd backend
.\.venv\Scripts\python -m pytest -v
```

Expected output:
```
tests/test_groq_path.py::test_groq_agents_parse_and_pass_model_and_effort PASSED
tests/test_groq_path.py::test_retry_after_rate_limit PASSED
tests/test_groq_path.py::test_json_mode_rejected_falls_back_to_plain_parsing PASSED
tests/test_groq_path.py::test_gives_up_after_retries PASSED
tests/test_pipeline.py::test_run_requires_api_key PASSED
tests/test_pipeline.py::test_upload_path_and_exports PASSED
tests/test_pipeline.py::test_delete_session PASSED
tests/test_pipeline.py::test_benchmark_data_structure PASSED
tests/test_pipeline.py::test_clarification_state_and_endpoints PASSED
tests/test_pipeline.py::test_semantic_kernel_integration PASSED

======================== 10 passed in 6.79s ========================
```

---

## Governance & Safety Notice

- **Human-in-the-Loop:** AI agents generate findings and recommendations; final award authority remains strictly with the human Tender Evaluation Committee.
- **Statutory Prototype:** Developed as a prototype for autonomous scrutiny and fraud detection under GFR 2017 principles. Not certified for statutory public tender awards without human oversight.
- **Data Confidentiality:** Bids are evaluated in an isolated session scope with blind anonymization during technical scoring to eliminate evaluator bias.
