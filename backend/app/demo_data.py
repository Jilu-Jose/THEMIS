"""Synthetic demo tender + four bids with planted issues (all names and numbers are fictional).

  SecureFlow - strong, fully compliant bid (submitted first)
  HydroNova  - turnover below threshold and no ISO certificate (eligibility fail)
  AquaSense  - technical text largely copied from SecureFlow, abnormally low price, claims projects it never lists
  BlueRiver  - compliant, but its stated total does not match its own line items
"""
import re
from .documents import inr

TENDER_TEXT = """
# TENDER NOTICE
Tender No: PHED/IOT/2026/017
Title: Supply, Installation and 3-Year Maintenance of an IoT-based Water Quality Monitoring System for 50 Villages
Issued by: Department of Rural Water Supply, Government of Punjab

## 1. Scope of Work
Supply, install and commission 50 IoT water-quality sensor nodes (pH, turbidity, TDS, residual chlorine) with gateways, a cloud dashboard with alerting, and 3 years of comprehensive maintenance.

## 2. Mandatory Eligibility Criteria
E1. The bidder must be a company registered in India for at least 5 years. Evidence: certificate of incorporation.
E2. Average annual turnover of at least INR 5 crore over the last three financial years. Evidence: CA-certified turnover statement.
E3. At least 2 similar projects (IoT or environmental monitoring), each of value INR 1 crore or more, completed in the last 5 years. Evidence: completion certificates or work orders.
E4. Valid GST registration and PAN. Evidence: copies of both.
E5. Valid ISO 9001 certification. Evidence: certificate.
E6. Earnest Money Deposit (EMD) of INR 2,00,000. Evidence: demand draft or bank guarantee details.
E7. Self-declaration that the bidder is not blacklisted or debarred. Evidence: signed declaration.

## 3. Technical Evaluation Criteria (100 marks)
T1. Technical approach and methodology - 25 marks
T2. Team qualifications and relevant experience - 20 marks
T3. Sensor accuracy and hardware specifications - 25 marks
T4. Implementation plan and timeline - 15 marks
T5. Support, maintenance and training plan - 15 marks
Minimum technical qualifying score: 60 out of 100.

## 4. Selection Method
Quality and Cost Based Selection (QCBS). Weightage: Technical 70, Financial 30. Financial bids are opened only for technically qualified bidders. Financial score = (lowest price / bidder price) x 100. Arithmetical errors are corrected by recomputing from unit prices.
"""

def build_bid(name, incorporated, turnover, projects, iso, emd, tech, rows, stated_total):
    lines = ["| Item | Qty | Unit Price (INR) | Amount (INR) |"]
    for item, qty, unit in rows:
        lines.append(f"| {item} | {qty} | {inr(unit)} | {inr(qty * unit)} |")
    table = "\n".join(lines) + f"\nTotal Quoted Price (INR, as stated by bidder): {inr(stated_total)}"
    return f"""# Bid Submission: {name}

## Company Profile
{name} was incorporated in {incorporated} and is registered as a company under the Companies Act, 2013.

## Eligibility Documents
Turnover statement certified by a Chartered Accountant: {turnover}.

Similar completed projects: {projects}

GST registration and PAN copies are attached and valid.

{iso}

{emd}

Self-declaration: the company has not been blacklisted or debarred by any government agency.

## Technical Proposal
{tech}

## Financial Bid
{table}
"""

ALPHA_TECH = """### 1. Technical Approach and Methodology
The system uses a three-layer architecture: LoRaWAN-connected sensor nodes at each village source, solar-powered gateways with 4G backhaul, and a cloud platform for ingestion, analytics and alerting. Data is sampled every 15 minutes, validated at the edge, and pushed over MQTT with TLS encryption. Machine-learning anomaly detection flags contamination events within 5 minutes of detection, and each alert is routed to the district engineer by SMS and app notification.

### 2. Team Qualifications and Experience
The project team of 12 is led by a PMP-certified project manager with 15 years of experience. It includes 3 IoT hardware engineers, 2 cloud engineers, 2 data scientists and 4 field technicians. Team members delivered the Ludhiana and PPCB projects and hold relevant certifications in embedded systems and cloud architecture.

### 3. Sensor Accuracy and Hardware Specifications
Sensors: pH range 0-14 with accuracy +/-0.05; turbidity 0-1000 NTU with accuracy +/-2%; TDS 0-5000 ppm with accuracy +/-2%; residual chlorine 0-5 mg/L with accuracy +/-0.05 mg/L. All probes are IP68 rated, factory-calibrated against NABL-traceable standards, and designed for 3 years between recalibrations with auto-cleaning wipers to reduce biofouling.

### 4. Implementation Plan and Timeline
Implementation runs 6 months: month 1 survey and design, months 2-4 phased installation of 50 nodes in 5 batches of 10, month 5 integration and user acceptance testing, month 6 training and go-live. A named site coordinator is assigned per district, and weekly progress reports are shared with the department.

### 5. Support, Maintenance and Training Plan
A 3-year comprehensive maintenance contract includes quarterly preventive visits, 24x7 helpdesk, 8-hour remote and 48-hour on-site response SLAs, and replacement of faulty sensors at no cost. Training covers 60 department staff in 3 workshops with hands-on sessions, user manuals in English and Punjabi, and refresher sessions every year."""

BETA_TECH = """### 1. Technical Approach and Methodology
Multi-parameter sensor nodes are placed at village water sources and transmit readings over NB-IoT to a cloud dashboard. Data is stored in a time-series database and shown on web dashboards with threshold alerts sent by SMS.

### 2. Team Qualifications and Experience
A team of 8 engineers and technicians will execute the project under an experienced project manager.

### 3. Sensor Accuracy and Hardware Specifications
Sensors measure pH, turbidity, TDS and chlorine with typical accuracy of +/-0.1 pH and +/-5% for the other parameters. Probes are IP67 rated and calibrated at installation.

### 4. Implementation Plan and Timeline
Installation will be completed within 8 months of the work order, in phases by district.

### 5. Support, Maintenance and Training Plan
Annual maintenance visits and a support phone line during office hours. One training session for department staff."""

GAMMA_TECH = (ALPHA_TECH.replace("15 minutes", "10 minutes").replace("5 minutes", "6 minutes")
              .replace("PMP-certified", "PMP certified").replace("three-layer", "3-layer"))

DELTA_TECH = """### 1. Technical Approach and Methodology
BlueRiver proposes LoRaWAN sensor nodes reporting to solar-powered gateways, with data streamed to a managed cloud platform. Rule-based thresholds and a statistical drift model trigger alerts to district officers by SMS and email. The dashboard offers village-level maps, trend charts and downloadable compliance reports.

### 2. Team Qualifications and Experience
The team of 10 comprises a project manager with 12 years of experience, 2 embedded engineers, 2 cloud developers, 1 data analyst and 4 field engineers who delivered the Haryana irrigation and Rajasthan groundwater telemetry projects.

### 3. Sensor Accuracy and Hardware Specifications
pH 0-14 (+/-0.1), turbidity 0-1000 NTU (+/-3%), TDS 0-5000 ppm (+/-3%), residual chlorine 0-5 mg/L (+/-0.1 mg/L). IP68 probes with factory calibration certificates; recalibration every 12 months.

### 4. Implementation Plan and Timeline
Delivery in 7 months: 1 month design, 4 months phased installation, 1 month testing, 1 month training and handover. Fortnightly progress reports to the department.

### 5. Support, Maintenance and Training Plan
Maintenance contract with half-yearly visits and email/phone support. One training workshop for department staff."""

ROWS = lambda s, g, p, i, a: [("IoT water-quality sensor nodes", 50, s), ("Solar gateways with 4G backhaul", 50, g),
                              ("Cloud platform and dashboard", 1, p), ("Installation and commissioning", 50, i),
                              ("3-year comprehensive AMC", 1, a)]

BIDS = {
    "SecureFlow Technologies Pvt Ltd": {"submitted_at": "2026-10-02 10:14", "text": build_bid(
        "SecureFlow Technologies Pvt Ltd", 2012, "FY2022-23 INR 9.1 crore, FY2023-24 INR 10.4 crore, FY2024-25 INR 11.2 crore",
        "(1) Smart water metering for Ludhiana Municipal Corporation, INR 3.2 crore, completed 2023; (2) River quality monitoring network for Punjab Pollution Control Board (PPCB), INR 2.6 crore, completed 2024.",
        "ISO 9001:2015 certificate valid till March 2028 is attached.", "EMD of INR 2,00,000 submitted via demand draft DD-458213.",
        ALPHA_TECH, ROWS(400000, 120000, 8000000, 50000, 9000000), 45500000)},
    "HydroNova Systems Pvt Ltd": {"submitted_at": "2026-10-02 15:40", "text": build_bid(
        "HydroNova Systems Pvt Ltd", 2018, "FY2022-23 INR 2.6 crore, FY2023-24 INR 3.1 crore, FY2024-25 INR 3.9 crore",
        "(1) Borewell level telemetry for Haryana Jal Board, INR 1.2 crore, completed 2023; (2) Lake monitoring for Chandigarh Administration, INR 1.5 crore, completed 2024.",
        "ISO 9001 renewal is in progress; the certificate is not enclosed with this bid.", "EMD of INR 2,00,000 submitted via demand draft DD-119027.",
        BETA_TECH, ROWS(380000, 110000, 7000000, 45000, 8000000), 41750000)},
    "AquaSense Infra Pvt Ltd": {"submitted_at": "2026-10-03 11:55", "text": build_bid(
        "AquaSense Infra Pvt Ltd", 2019, "FY2022-23 INR 6.2 crore, FY2023-24 INR 6.9 crore, FY2024-25 INR 7.3 crore",
        "(1) Pond water quality sensors for Gujarat Jal Sansthan, INR 1.4 crore, completed 2023; (2) Canal flow monitoring for Haryana Irrigation Department, INR 1.1 crore, completed 2024.",
        "ISO 9001:2015 certificate valid till June 2027 is attached.", "EMD of INR 2,00,000 submitted via demand draft DD-662310.",
        GAMMA_TECH, ROWS(200000, 60000, 4000000, 20000, 3000000), 21000000)},
    "BlueRiver Analytics Pvt Ltd": {"submitted_at": "2026-10-02 12:05", "text": build_bid(
        "BlueRiver Analytics Pvt Ltd", 2016, "FY2022-23 INR 7.5 crore, FY2023-24 INR 8.2 crore, FY2024-25 INR 9.0 crore",
        "(1) Smart irrigation monitoring for Haryana Agriculture Department, INR 1.8 crore, completed 2022; (2) Groundwater level telemetry for Rajasthan Water Resources Department, INR 1.3 crore, completed 2024.",
        "ISO 9001:2015 certificate valid till August 2027 is attached.", "EMD of INR 2,00,000 submitted via demand draft DD-771204.",
        DELTA_TECH, ROWS(420000, 125000, 8500000, 55000, 9500000), 45000000)},   # stated total is WRONG on purpose (true sum = 4,80,00,000)
}


def build_demo():
    """Return (tender_text, [ {name, filename, text, submitted_at}, ... ])."""
    bids = []
    for name, b in BIDS.items():
        fname = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") + "_Bid.md"
        bids.append({"name": name, "filename": fname, "text": b["text"], "submitted_at": b["submitted_at"]})
    return TENDER_TEXT.strip() + "\n", bids


def export(directory):
    """Write the demo tender and bids as files (so the upload path can be tested)."""
    import pathlib
    d = pathlib.Path(directory)
    d.mkdir(parents=True, exist_ok=True)
    tender, bids = build_demo()
    (d / "tender_notice.md").write_text(tender, encoding="utf-8")
    for b in bids:
        (d / b["filename"]).write_text(b["text"], encoding="utf-8")
    return [p.name for p in sorted(d.iterdir())]


if __name__ == "__main__":
    import sys
    print(export(sys.argv[1] if len(sys.argv) > 1 else "sample_data"))
