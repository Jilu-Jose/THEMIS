"""Synthetic benchmark dataset: 4 additional tenders + 3-4 bids each for testing and evaluation.

Combined with demo_data.py (Tender 1: IoT Water Quality), this gives 5 realistic government tenders:
  - Tender 1: IoT Water Quality (Punjab PHED, 4 bids) — Winner: SecureFlow Technologies Pvt Ltd, DQ: HydroNova Systems Pvt Ltd
  - Tender 2: Road Construction (HP PWD, 3 bids) — Winner: RoadBuild Pro Pvt Ltd, DQ: ConstructEase India Pvt Ltd
  - Tender 3: IT Citizen Portal (NIC, 4 bids) — Winner: TechForge Solutions Pvt Ltd, DQ: DevNest Technologies Pvt Ltd
  - Tender 4: Medical Diagnostic Equipment (AIIMS, 3 bids) — Winner: MedSupply Pharma Pvt Ltd, DQ: HealthFirst Devices Pvt Ltd
  - Tender 5: Rooftop Solar Power (MNRE, 4 bids) — Winner: SolarEdge Power Pvt Ltd, DQ: GreenVolt Systems Pvt Ltd
"""
import re
from .demo_data import build_bid
from .documents import inr

# ==============================================================================
# TENDER 2: Road Construction & Maintenance (HP PWD)
# ==============================================================================
TENDER_TEXT_2 = """
# TENDER NOTICE
Tender No: PWD/ROAD/2026/042
Title: Construction and Maintenance of Rural Road Network (45 km) in Himachal Pradesh
Issued by: Public Works Department, Government of Himachal Pradesh

## 1. Scope of Work
Construction, widening, drainage works, and 5-year routine maintenance of a 45 km rural road network across Mandi and Kullu districts.

## 2. Mandatory Eligibility Criteria
E1. Registered civil contractor in India for at least 7 years. Evidence: contractor registration certificate.
E2. Average annual turnover of at least INR 20 crore over the last three financial years. Evidence: CA-certified turnover certificate.
E3. At least 3 similar road construction projects, each of value INR 10 crore or more, completed in the last 7 years. Evidence: completion certificates.
E4. Valid GST registration and PAN card. Evidence: copies of both.
E5. Valid ISO 9001 and ISO 14001 certifications. Evidence: copies of both certificates.
E6. Earnest Money Deposit (EMD) of INR 10,00,000. Evidence: demand draft or bank guarantee.
E7. Self-declaration that the contractor is not blacklisted by Central or State Government. Evidence: notarised affidavit.

## 3. Technical Evaluation Criteria (100 marks)
T1. Construction methodology and quality control plan - 30 marks
T2. Equipment deployment and machinery availability - 25 marks
T3. Team qualifications and site engineering staff - 20 marks
T4. Environmental and slope protection plan - 15 marks
T5. Execution timeline and milestone schedule - 10 marks
Minimum technical qualifying score: 65 out of 100.

## 4. Selection Method
Quality and Cost Based Selection (QCBS). Weightage: Technical 70, Financial 30.
Financial score = (lowest price / bidder price) x 100. Arithmetical errors are corrected by line-item recomputation.
"""

ROAD_TECH_A = """### 1. Construction Methodology and Quality Control Plan
RoadBuild Pro utilizes an mechanized paving workflow complying with MoRTH specifications (5th Revision). Base course will be prepared with 150mm Granular Sub-Base (GSB) followed by 100mm Wet Mix Macadam (WMM) and 40mm Bituminous Concrete (BC). An on-site NABL-accredited field testing laboratory will test aggregate gradation, moisture content, compaction density (minimum 98% Proctor), and bitumen penetration at specified frequencies.

### 2. Equipment Deployment and Machinery Availability
All machinery is company-owned and staged at our regional depot in Sundernagar: 2 electronic sensor pavers (Vogele 1800-3), 4 tandem vibratory rollers (Hamm HD 90), 2 pneumatic tyre rollers, 1 modern asphalt batch mix plant (120 TPH), 10 tipper trucks, and 2 motor graders (CAT 120K).

### 3. Team Qualifications and Site Engineering Staff
Project Director holds M.Tech (Transportation) with 22 years of hill road construction experience. The on-site team includes 2 Senior Highway Engineers (B.Tech, 12+ years experience), 1 Geotechnical Engineer (M.Tech, 10 years experience), 2 Material Testing Engineers, and 6 Site Supervisors certified in road construction.

### 4. Environmental and Slope Protection Plan
Specialized bio-engineering slope stabilization will be deployed on fragile cut slopes using vetiver grass and geonets. Hydro-seeding will be conducted along 35,000 sqm of embankment slopes. Muck disposal sites designated by HP State Forest Department will be securely bunded to avoid river siltation.

### 5. Execution Timeline and Milestone Schedule
Total project duration is 18 months, split into 4 phases: Phase 1 (Months 1-3) earthwork and culverts; Phase 2 (Months 4-9) sub-base and WMM; Phase 3 (Months 10-15) bituminous surfacing; Phase 4 (Months 16-18) road furniture, safety signage, and final commissioning."""

ROAD_TECH_B = """### 1. Construction Methodology and Quality Control Plan
Pavement Masters follows standard PWD specifications. Sub-grade compaction will be carried out using vibratory rollers followed by GSB and bituminous macadam layers. Quality tests will be performed at regional government engineering college laboratories.

### 2. Equipment Deployment and Machinery Availability
We will deploy 1 asphalt paver, 2 vibratory rollers, 1 static roller, and hire additional tippers and earthmoving equipment locally as required for the project.

### 3. Team Qualifications and Site Engineering Staff
Led by a Project Manager with 14 years of civil works experience, assisted by 1 Site Engineer (B.Tech, 6 years experience) and 3 supervisors.

### 4. Environmental and Slope Protection Plan
Standard retaining walls and crate wire walls (gabions) will be constructed along slope edges to prevent soil erosion. Waste soil will be dumped in designated low-lying areas.

### 5. Execution Timeline and Milestone Schedule
Project execution planned over 20 months with work progressing simultaneously across three road stretches."""

ROAD_TECH_C = """### 1. Construction Methodology and Quality Control Plan
ConstructEase India undertakes road laying using standard sub-base preparation and roller compaction. Periodic field density tests will be conducted.

### 2. Equipment Deployment and Machinery Availability
Basic road making machinery will be mobilized within 30 days of contract award.

### 3. Team Qualifications and Site Engineering Staff
A team of 4 civil diploma engineers under the supervision of a contractor partner.

### 4. Environmental and Slope Protection Plan
Retaining walls at critical landslide locations.

### 5. Execution Timeline and Milestone Schedule
Completion scheduled within 24 months."""

ROWS_ROAD = lambda earth, gsb, wmm, bit, amc: [
    ("Earthwork in hill cutting and embankment", 45000, earth),
    ("Granular Sub-Base (GSB) 150mm thick", 36000, gsb),
    ("Wet Mix Macadam (WMM) 100mm thick", 27000, wmm),
    ("Bituminous Surfacing & Macadam", 27000, bit),
    ("5-Year Comprehensive Road Maintenance", 1, amc),
]

BIDS_2 = {
    "RoadBuild Pro Pvt Ltd": {
        "submitted_at": "2026-10-04 11:20",
        "text": build_bid(
            "RoadBuild Pro Pvt Ltd", 2010,
            "FY2022-23 INR 26.4 crore, FY2023-24 INR 29.8 crore, FY2024-25 INR 32.1 crore",
            "(1) Bilaspur-Kullu Highway widening, INR 14.5 crore, completed 2022; (2) Shimla bypass rural link road, INR 11.8 crore, completed 2023; (3) Kangra valley district road (38 km), INR 16.2 crore, completed 2024.",
            "ISO 9001:2015 and ISO 14001:2015 certificates valid till October 2027 are enclosed.",
            "EMD of INR 10,00,000 submitted via Bank Guarantee BG-HP-88902 valid for 180 days.",
            ROAD_TECH_A,
            ROWS_ROAD(450, 1100, 1400, 2500, 20000000),
            187050000  # 45000*450 + 36000*1100 + 27000*1400 + 27000*2500 + 20000000 = 20250000 + 39600000 + 37800000 + 67500000 + 20000000 = 185150000
        )
    },
    "Pavement Masters Ltd": {
        "submitted_at": "2026-10-04 14:45",
        "text": build_bid(
            "Pavement Masters Ltd", 2015,
            "FY2022-23 INR 21.2 crore, FY2023-24 INR 22.8 crore, FY2024-25 INR 24.5 crore",
            "(1) Hamirpur bypass road, INR 10.5 crore, completed 2022; (2) Solan rural road package 2, INR 12.0 crore, completed 2023; (3) Chamba hill connectivity, INR 10.2 crore, completed 2024.",
            "ISO 9001:2015 and ISO 14001:2015 certificates valid till July 2027 are enclosed.",
            "EMD of INR 10,00,000 submitted via Demand Draft DD-554109 drawn on SBI.",
            ROAD_TECH_B,
            ROWS_ROAD(420, 1050, 1350, 2400, 18000000),
            175800000
        )
    },
    "ConstructEase India Pvt Ltd": {
        "submitted_at": "2026-10-04 16:10",
        "text": build_bid(
            "ConstructEase India Pvt Ltd", 2014,
            "FY2022-23 INR 10.5 crore, FY2023-24 INR 12.2 crore, FY2024-25 INR 13.8 crore",  # Turnover < 20 Cr threshold -> FAILS E2
            "(1) Una town road improvement, INR 5.5 crore, completed 2022; (2) Nurpur bridge approach road, INR 6.2 crore, completed 2023; (3) Paonta Sahib link, INR 7.1 crore, completed 2024.",
            "ISO 9001:2015 certificate valid till Nov 2026 enclosed; ISO 14001 certificate is not enclosed.",
            "EMD of INR 10,00,000 submitted via DD-901234.",
            ROAD_TECH_C,
            ROWS_ROAD(400, 1000, 1300, 2300, 15000000),
            166200000
        )
    }
}

# ==============================================================================
# TENDER 3: IT Citizen Services Portal (NIC / MeitY)
# ==============================================================================
TENDER_TEXT_3 = """
# TENDER NOTICE
Tender No: NIC/GOV/2026/089
Title: Development and Deployment of Citizen Services Portal for 12 State Departments
Issued by: National Informatics Centre, Ministry of Electronics and IT

## 1. Scope of Work
Design, development, cloud deployment, security audit, and 3-year support of an integrated Citizen Services Portal with e-Sign, DigiLocker, and Aadhaar authentication.

## 2. Mandatory Eligibility Criteria
E1. Registered IT company in India for at least 5 years. Evidence: certificate of incorporation.
E2. Average annual turnover of at least INR 15 crore over the last three financial years. Evidence: CA certificate.
E3. At least 2 government IT software projects, each of value INR 5 crore or more, completed in the last 5 years. Evidence: work orders and client completion certificates.
E4. Valid GST registration and PAN card. Evidence: copies of both certificates.
E5. Valid CMMI Level 3 or higher certification. Evidence: CMMI appraisal certificate.
E6. Earnest Money Deposit (EMD) of INR 5,00,000. Evidence: bank guarantee or online transaction receipt.
E7. Self-declaration of not being blacklisted by any government entity. Evidence: signed declaration.

## 3. Technical Evaluation Criteria (100 marks)
T1. Solution architecture, microservices design, and scalability - 30 marks
T2. Security, data protection, and OWASP Top 10 compliance - 25 marks
T3. Team qualifications, certifications, and technical leadership - 20 marks
T4. Implementation roadmap, CI/CD pipeline, and testing strategy - 15 marks
T5. Post-deployment maintenance, SLA guarantees, and disaster recovery - 10 marks
Minimum technical qualifying score: 65 out of 100.

## 4. Selection Method
Quality and Cost Based Selection (QCBS). Weightage: Technical 70, Financial 30.
Financial score = (lowest price / bidder price) x 100.
"""

IT_TECH_A = """### 1. Solution Architecture and Microservices Design
TechForge proposes an event-driven microservices architecture built on containerized Spring Boot and Node.js services orchestrated via Kubernetes (K8s). Apache Kafka acts as the high-throughput message backbone processing up to 25,000 requests/sec. State is managed via distributed PostgreSQL with read-replicas and Redis caching. The front-end leverages Next.js 14 with server-side rendering for optimal performance across rural 2G/3G networks, complying with GIGW 3.0 accessibility standards.

### 2. Security, Data Protection, and OWASP Compliance
Zero Trust architecture with mTLS between internal microservices. Data at rest is encrypted using AES-256 with KMS key rotation; data in transit uses TLS 1.3. Integrated with Aadhaar e-KYC and DigiLocker via secure API gateways with IP whitelisting and HMAC token validation. Automated SAST/DAST security scans in GitHub Actions and CERT-In empanelled third-party audit planned prior to launch.

### 3. Team Qualifications and Technical Leadership
Team of 18 specialists led by an Enterprise Architect (TOGAF certified, 18 years experience). Key members include 1 Cloud Solution Architect (AWS/GCP Certified Professional), 1 DevSecOps Lead (CISSP), 4 Senior Full-Stack Developers, 2 Database Administrators, and 4 QA Automation Engineers.

### 4. Implementation Roadmap and CI/CD Pipeline
Deployment in 6 sprints over 9 months: Month 1-2 Discovery and high-level design; Months 3-5 Microservices development and integration; Month 6 Security audit & UAT; Month 7-8 Pilot rollout across 3 departments; Month 9 Statewide go-live. Fully automated GitLab CI/CD with canary deployments.

### 5. Maintenance, SLA Guarantees, and Disaster Recovery
3-year 24x7 Tier-3 support with 99.9% uptime SLA, 15-minute response for critical incidents, and RPO < 5 minutes / RTO < 30 minutes with multi-region disaster recovery in MeitY empanelled sovereign cloud."""

# Collusive duplicate of A
IT_TECH_B = IT_TECH_A.replace("TechForge", "SoftWave").replace("Spring Boot and Node.js", "Spring Boot and Node.js services").replace("25,000", "24,000").replace("18 specialists", "16 specialists")

IT_TECH_C = """### 1. Solution Architecture and Microservices Design
CodeMatrix proposes a modular cloud web portal using Python Django and React. Database will be PostgreSQL with Redis caching.

### 2. Security, Data Protection, and OWASP Compliance
Standard SSL encryption, role-based access control, and sanitization against SQL injection and XSS attacks.

### 3. Team Qualifications and Technical Leadership
Led by a Technical Lead with 10 years experience and 8 software developers.

### 4. Implementation Roadmap and CI/CD Pipeline
Development planned over 10 months in three milestones with weekly progress reports.

### 5. Maintenance, SLA Guarantees, and Disaster Recovery
Office-hours technical support with 99.5% uptime commitment."""

IT_TECH_D = """### 1. Solution Architecture and Microservices Design
DevNest offers a cloud-native platform using Java microservices and Angular front-end with API gateway routing.

### 2. Security, Data Protection, and OWASP Compliance
End-to-end HTTPS, token-based authentication, and vulnerability patching.

### 3. Team Qualifications and Technical Leadership
Development team of 10 engineers with average 5 years experience in web application development.

### 4. Implementation Roadmap and CI/CD Pipeline
Delivery in 8 months with bi-weekly sprint reviews.

### 5. Maintenance, SLA Guarantees, and Disaster Recovery
Business-hours ticket resolution and quarterly patch updates."""

ROWS_IT = lambda dev, intg, cloud, sec, amc: [
    ("Core Portal Software Architecture and Development", 1, dev),
    ("12 Departmental API Integrations & DigiLocker", 12, intg),
    ("Cloud Infrastructure Setup & Kubernetes Setup", 1, cloud),
    ("CERT-In Empanelled Security Audit & Compliance", 1, sec),
    ("3-Year Comprehensive Technical Support & Maintenance", 1, amc),
]

BIDS_3 = {
    "TechForge Solutions Pvt Ltd": {
        "submitted_at": "2026-10-05 10:15",
        "text": build_bid(
            "TechForge Solutions Pvt Ltd", 2014,
            "FY2022-23 INR 18.5 crore, FY2023-24 INR 21.0 crore, FY2024-25 INR 24.2 crore",
            "(1) Unified Transport Portal for Karnataka e-Governance, INR 7.8 crore, completed 2023; (2) Public Distribution System automation for MP Government, INR 6.4 crore, completed 2024; (3) Land Records GIS Portal for Odisha, INR 8.2 crore, completed 2025.",
            "CMMI Level 5 (DEV) appraisal certificate valid till August 2028 is enclosed.",
            "EMD of INR 5,00,000 submitted via RTGS UTR No. SBIN8266109923.",
            IT_TECH_A,
            ROWS_IT(45000000, 2500000, 12000000, 4000000, 28000000),
            119000000  # 45M + 30M + 12M + 4M + 28M = 119M
        )
    },
    "SoftWave India Ltd": {
        "submitted_at": "2026-10-05 11:30",
        "text": build_bid(
            "SoftWave India Ltd", 2017,
            "FY2022-23 INR 16.0 crore, FY2023-24 INR 17.5 crore, FY2024-25 INR 19.1 crore",
            "(1) Municipal Grievance Redressal System for Delhi MCD, INR 5.2 crore, completed 2023; (2) Hospital Management System for UP Health, INR 5.8 crore, completed 2024.",
            "CMMI Level 3 (DEV) certificate valid till June 2027 is enclosed.",
            "EMD of INR 5,00,000 submitted via Bank Guarantee BG-SW-11223.",
            IT_TECH_B,
            ROWS_IT(40000000, 2200000, 10000000, 3500000, 25000000),
            104900000
        )
    },
    "CodeMatrix Systems Pvt Ltd": {
        "submitted_at": "2026-10-05 14:00",
        "text": build_bid(
            "CodeMatrix Systems Pvt Ltd", 2015,
            "FY2022-23 INR 15.8 crore, FY2023-24 INR 17.2 crore, FY2024-25 INR 18.0 crore",
            "(1) Education scholarship portal for Rajasthan, INR 5.5 crore, completed 2023; (2) Mining royalty tracking for Jharkhand, INR 5.1 crore, completed 2024.",
            "CMMI Level 3 (DEV) certificate valid till May 2027 is enclosed.",
            "EMD of INR 5,00,000 submitted via DD-447812.",
            IT_TECH_C,
            ROWS_IT(42000000, 2400000, 11000000, 3800000, 26000000),
            95000000  # ARITHMETIC MISMATCH: 42M + 28.8M + 11M + 3.8M + 26M = 111.6M, but quoted 95M
        )
    },
    "DevNest Technologies Pvt Ltd": {
        "submitted_at": "2026-10-05 16:20",
        "text": build_bid(
            "DevNest Technologies Pvt Ltd", 2016,
            "FY2022-23 INR 17.0 crore, FY2023-24 INR 18.5 crore, FY2024-25 INR 20.1 crore",
            "(1) Police verification portal for Haryana, INR 5.3 crore, completed 2023; (2) Excise tracking for Punjab, INR 5.6 crore, completed 2024.",
            "CMMI Level 3 certificate valid till Dec 2026 enclosed.",
            "EMD of INR 5,00,000 submitted via DD-332190.",
            IT_TECH_D,
            ROWS_IT(44000000, 2300000, 10500000, 3600000, 27000000),
            112700000
        ).replace("GST registration and PAN copies are attached and valid.", "PAN copy enclosed; GST registration certificate is not attached as renewal application is pending with GST authorities.")  # FAILS E4
    }
}

# ==============================================================================
# TENDER 4: Medical Equipment Supply (AIIMS)
# ==============================================================================
TENDER_TEXT_4 = """
# TENDER NOTICE
Tender No: AIIMS/MED/2026/156
Title: Supply, Installation and 5-Year Comprehensive Maintenance of Advanced Diagnostic Equipment
Issued by: All India Institute of Medical Sciences (AIIMS), New Delhi

## 1. Scope of Work
Supply, installation, testing, commissioning, and 5-year comprehensive on-site warranty/maintenance of 3.0T MRI, 128-Slice CT Scanner, and 4 Color Doppler Ultrasound machines for AIIMS partner hospitals.

## 2. Mandatory Eligibility Criteria
E1. Registered medical equipment manufacturer or authorized Indian subsidiary for at least 5 years. Evidence: certificate of incorporation.
E2. Average annual turnover of at least INR 30 crore over the last three financial years. Evidence: CA-certified balance sheet extracts.
E3. At least 2 similar contracts of advanced diagnostic imaging equipment supply, each of value INR 15 crore or more, executed in the last 5 years. Evidence: supply completion certificates.
E4. Valid GST registration and PAN card. Evidence: copies of both.
E5. Valid ISO 13485 (Medical Devices Quality Management) certification. Evidence: valid certificate with expiry date.
E6. Earnest Money Deposit (EMD) of INR 15,00,000. Evidence: bank guarantee.
E7. Self-declaration that the manufacturer/bidder has not been blacklisted or debarred. Evidence: notarised declaration.

## 3. Technical Evaluation Criteria (100 marks)
T1. Diagnostic imaging specifications, magnet homogeneity, and detector technology - 35 marks
T2. Clinical workflow, AI reconstruction packages, and post-processing workstation - 25 marks
T3. Technical service team qualifications and local spare parts warehouse - 20 marks
T4. Installation, siting, RF-shielding, and turnkey commissioning plan - 12 marks
T5. Clinical training program for radiologists, physicists, and radiographers - 8 marks
Minimum technical qualifying score: 70 out of 100.

## 4. Selection Method
Quality and Cost Based Selection (QCBS). Weightage: Technical 70, Financial 30.
Financial score = (lowest price / bidder price) x 100.
"""

MED_TECH_A = """### 1. Diagnostic Imaging Specifications and Magnet Homogeneity
3.0T Wide-Bore (70cm) Superconducting MRI with ultra-high homogeneity zero-boil-off magnet. Features 128 RF independent receiver channels, high-performance gradients (45 mT/m amplitude, 200 T/m/s slew rate). 128-Slice Dual-Energy CT Scanner equipped with Stellar detector array, 0.28 sec rotation speed, and sub-millimeter isotropic resolution (0.3mm). 4 High-end Color Doppler units with matrix array single-crystal transducers and shear-wave elastography.

### 2. Clinical Workflow, AI Reconstruction, and Workstation
Deep-learning based MR reconstruction algorithm (DL-Recon) reducing scan times by up to 50% while preserving SNR. CT iterative model reconstruction (IMR) delivering 80% radiation dose reduction. Advanced 3D post-processing server with 5 concurrent radiologist licenses including automated cardiac CTA, perfusion analysis, and virtual colonoscopy modules.

### 3. Service Team Qualifications and Local Spare Parts Warehouse
Dedicated team of 6 factory-trained Field Service Engineers (OEM certified on 3.0T MRI) based in Delhi-NCR. Central spare parts depot at Okhla stocking critical spares including cold-head, RF amplifiers, and replacement detector modules with guaranteed 4-hour on-site arrival SLA.

### 4. Turnkey Commissioning, Siting, and RF Shielding
Turnkey scope includes full RF cage installation (copper shielding > 100 dB attenuation up to 150 MHz), quench pipe routing, chilled water plant (redundant 2x30 TR chillers), and 160 kVA true online UPS with 30-minute full-load battery backup.

### 5. Clinical Training Program
Comprehensive on-site application training by clinical imaging specialists for 4 weeks post-handover, covering neuro, body, cardiac, and musculoskeletal imaging protocols, followed by 2 refresher training workshops per year for 5 years."""

MED_TECH_B = """### 1. Diagnostic Imaging Specifications and Magnet Homogeneity
3.0T MRI system with 60cm bore and standard gradient system (33 mT/m). 64-slice CT scanner with standard ceramic detector array. 4 standard digital ultrasound systems with abdominal and vascular probes.

### 2. Clinical Workflow, AI Reconstruction, and Workstation
Standard filtered back-projection and basic iterative reconstruction for CT. Standard PACS viewing workstation with 2 licenses.

### 3. Service Team Qualifications and Local Spare Parts Warehouse
Regional service engineers available during business hours with spare parts shipped from central warehouse in Mumbai within 48 hours.

### 4. Turnkey Commissioning, Siting, and RF Shielding
Standard RF room shielding and electrical connections provided according to room layout drawings.

### 5. Clinical Training Program
1 week initial application training for hospital technicians."""

MED_TECH_C = """### 1. Diagnostic Imaging Specifications and Magnet Homogeneity
Refurbished and certified 3.0T MRI scanner and multi-slice CT unit meeting standard hospital specifications.

### 2. Clinical Workflow, AI Reconstruction, and Workstation
Standard diagnostic viewing software installed on desktop computer.

### 3. Service Team Qualifications and Local Spare Parts Warehouse
On-call third-party maintenance engineers.

### 4. Turnkey Commissioning, Siting, and RF Shielding
Basic room preparation assistance.

### 5. Clinical Training Program
3 days operator familiarization."""

ROWS_MED = lambda mri, ct, us, turn, amc: [
    ("3.0T Superconducting MRI System Complete", 1, mri),
    ("128-Slice Dual-Energy CT Scanner", 1, ct),
    ("Color Doppler Ultrasound Units with Transducers", 4, us),
    ("Turnkey Civil, RF-Shielding & HVAC Siting Works", 1, turn),
    ("5-Year Comprehensive Maintenance Contract (CMC)", 1, amc),
]

BIDS_4 = {
    "MedSupply Pharma Pvt Ltd": {
        "submitted_at": "2026-10-06 10:45",
        "text": build_bid(
            "MedSupply Pharma Pvt Ltd", 2011,
            "FY2022-23 INR 38.5 crore, FY2023-24 INR 42.0 crore, FY2024-25 INR 46.5 crore",
            "(1) 3.0T MRI & Cath Lab installation at PGIMER Chandigarh, INR 22.0 crore, completed 2023; (2) Diagnostic equipment package for Safdarjung Hospital, INR 18.5 crore, completed 2024.",
            "ISO 13485:2016 certificate valid till November 2027 is enclosed.",
            "EMD of INR 15,00,000 submitted via Bank Guarantee BG-AIIMS-9081 valid for 180 days.",
            MED_TECH_A,
            ROWS_MED(120000000, 65000000, 4500000, 22000000, 55000000),
            280000000  # 120M + 65M + 18M + 22M + 55M = 280M
        )
    },
    "HealthFirst Devices Pvt Ltd": {
        "submitted_at": "2026-10-06 12:30",
        "text": build_bid(
            "HealthFirst Devices Pvt Ltd", 2013,
            "FY2022-23 INR 32.0 crore, FY2023-24 INR 35.4 crore, FY2024-25 INR 36.8 crore",
            "(1) CT Scanner installation for JIPMER Puducherry, INR 16.0 crore, completed 2023; (2) MRI unit for King George Medical University, INR 17.5 crore, completed 2024.",
            "ISO 13485 certificate expired on 31st December 2025; renewal audit is underway.",  # FAILS E5 (expired certificate)
            "EMD of INR 15,00,000 submitted via Bank Guarantee BG-HF-77441.",
            MED_TECH_B,
            ROWS_MED(110000000, 60000000, 4000000, 18000000, 50000000),
            254000000
        )
    },
    "CurePoint India Pvt Ltd": {
        "submitted_at": "2026-10-06 15:10",
        "text": build_bid(
            "CurePoint India Pvt Ltd", 2015,
            "FY2022-23 INR 31.0 crore, FY2023-24 INR 33.2 crore, FY2024-25 INR 34.0 crore",
            "(1) Medical imaging turnkey for RML Hospital, INR 15.5 crore, completed 2023; (2) Radiology upgrade for Patna Medical College, INR 16.2 crore, completed 2024.",
            "ISO 13485:2016 certificate valid till August 2027 is enclosed.",
            "EMD of INR 15,00,000 submitted via Demand Draft DD-882190.",
            MED_TECH_C,
            ROWS_MED(50000000, 28000000, 2000000, 8000000, 22000000),
            116000000  # Abnormally low price: 11.6 Cr vs ~28 Cr median (>55% below market)
        )
    }
}

# ==============================================================================
# TENDER 5: Rooftop Solar Power Plant (MNRE)
# ==============================================================================
TENDER_TEXT_5 = """
# TENDER NOTICE
Tender No: MNRE/SOLAR/2026/203
Title: Design, Supply, Installation and 5-Year O&M of 10 MW Grid-Connected Rooftop Solar PV Systems
Issued by: Ministry of New and Renewable Energy (MNRE), Government of India

## 1. Scope of Work
Turnkey design, supply, civil engineering, erection, testing, commissioning, grid synchronization, and 5 years comprehensive Operation & Maintenance (O&M) of 10 MW aggregate capacity grid-connected rooftop solar plants on government buildings.

## 2. Mandatory Eligibility Criteria
E1. Registered solar power developer or EPC company in India for at least 5 years. Evidence: certificate of incorporation.
E2. Average annual turnover of at least INR 25 crore over the last three financial years. Evidence: CA-certified turnover certificate.
E3. At least 2 grid-connected solar PV projects of 2 MW or more each, commissioned in the last 5 years. Evidence: commissioning certificates and joint inspection reports.
E4. Valid GST registration and PAN card. Evidence: copies of both.
E5. Valid ISO 9001 quality management certification. Evidence: valid certificate.
E6. Earnest Money Deposit (EMD) of INR 20,00,000. Evidence: bank guarantee or online deposit proof.
E7. Self-declaration that the bidder is not blacklisted by MNRE, SECI, or any State Nodal Agency. Evidence: signed declaration.

## 3. Technical Evaluation Criteria (100 marks)
T1. Solar module efficiency, cell technology (TopCon/Mono PERC), and degradation guarantees - 30 marks
T2. Inverter specifications, MPPT efficiency, and grid protection features - 25 marks
T3. Structural design, wind loading analysis (180 km/h), and mounting methodology - 25 marks
T4. Team engineering capabilities and MNRE-certified solar professionals - 12 marks
T5. Remote telemetry SCADA, solar irradiance monitoring, and O&M methodology - 8 marks
Minimum technical qualifying score: 65 out of 100.

## 4. Selection Method
Quality and Cost Based Selection (QCBS). Weightage: Technical 70, Financial 30.
Financial score = (lowest price / bidder price) x 100. Arithmetical errors are corrected by recomputing from unit prices.
"""

SOLAR_TECH_A = """### 1. Solar Module Efficiency and Technology Selection
Tier-1 N-Type TOPCon bifacial glass-glass monocrystalline PV modules with 22.8% module efficiency and positive power tolerance (+5W). Modules feature 16-busbar half-cut cell technology with first-year degradation <= 1.0% and linear degradation <= 0.40%/year over 30-year performance warranty. Tested and certified under IEC 61215, IEC 61730, and BIS IS 14286.

### 2. Inverter Specifications and Grid Protection
Grid-tied string inverters with 98.8% Euro-efficiency, 9 MPPT trackers per 100kW unit, and built-in PID recovery. Integrated anti-islanding protection, DC surge arrester (Type II), arc fault circuit interrupter (AFCI), and automated power factor correction complying with CEA Technical Standards for Grid Connectivity.

### 3. Structural Design and Wind Load Resistance
Hot-dip galvanized steel mounting structures (minimum 80 microns galvanization) designed to withstand wind velocities up to 180 km/h in accordance with IS 875 (Part 3). Non-penetrating ballasted mounting on flat roofs with EPDM rubber pads to protect building waterproofing membranes.

### 4. Team Engineering Capabilities
Project executed under Chief Solar Engineer with Ph.D. in Photovoltaics and 16 years EPC experience. Team includes 4 MNRE Surya Mitra certified solar engineers, 2 Structural Engineers (M.Tech), and 10 certified technicians.

### 5. Remote Telemetry SCADA and 5-Year O&M
Cloud SCADA platform monitoring string-level voltage, current, and pyranometer solar irradiance in real-time. Automated robotic dry-cleaning system for high-soiling rooftops. Guaranteed 99% plant availability and Performance Ratio (PR) > 78%."""

SOLAR_TECH_B = """### 1. Solar Module Efficiency and Technology Selection
Mono PERC solar PV modules with 21.2% module efficiency and standard 25-year linear performance warranty (IEC certified).

### 2. Inverter Specifications and Grid Protection
Standard string inverters with 98.2% efficiency and standard anti-islanding protection.

### 3. Structural Design and Wind Load Resistance
Aluminum structure anchored to RCC roof slabs designed for 150 km/h wind speeds.

### 4. Team Engineering Capabilities
Team of 6 electrical engineers with experience in commercial solar installations.

### 5. Remote Telemetry SCADA and 5-Year O&M
Web portal for daily generation monitoring and scheduled quarterly cleaning visits."""

SOLAR_TECH_C = """### 1. Solar Module Efficiency and Technology Selection
Polycrystalline / standard mono solar modules with 20.0% efficiency and 25-year warranty.

### 2. Inverter Specifications and Grid Protection
Standard grid-tied central/string inverters.

### 3. Structural Design and Wind Load Resistance
Mild steel mounting structure with anti-rust coating.

### 4. Team Engineering Capabilities
Solar engineering team of 5 members.

### 5. Remote Telemetry SCADA and 5-Year O&M
Periodic maintenance and on-call troubleshooting."""

SOLAR_TECH_D = """### 1. Solar Module Efficiency and Technology Selection
Standard Tier-1 mono PERC modules with 21.0% efficiency.

### 2. Inverter Specifications and Grid Protection
European brand string inverters with standard safety certifications.

### 3. Structural Design and Wind Load Resistance
Pre-galvanized structures for flat roofs.

### 4. Team Engineering Capabilities
Technical team with 8 engineers.

### 5. Remote Telemetry SCADA and 5-Year O&M
Monthly manual cleaning and generation reporting."""

ROWS_SOLAR = lambda mod, inv, bos, inst, om: [
    ("N-Type TOPCon/Mono Solar PV Modules (10 MWp)", 10000, mod),
    ("Grid-Tied String Inverters with SCADA telemetry", 100, inv),
    ("Balance of Systems (BOS: Cables, LT Panels, Structures)", 1, bos),
    ("Installation, Testing & Grid Interconnection Works", 1, inst),
    ("5-Year Comprehensive Operation & Maintenance (O&M)", 1, om),
]

BIDS_5 = {
    "SolarEdge Power Pvt Ltd": {
        "submitted_at": "2026-10-07 09:30",
        "text": build_bid(
            "SolarEdge Power Pvt Ltd", 2013,
            "FY2022-23 INR 31.0 crore, FY2023-24 INR 35.5 crore, FY2024-25 INR 39.0 crore",
            "(1) 4.5 MW Rooftop Solar for Indian Railways, INR 18.2 crore, completed 2023; (2) 3.2 MW Solar PV for IIT Delhi, INR 13.5 crore, completed 2024; (3) 5.0 MW Solar for DMRC, INR 21.0 crore, completed 2025.",
            "ISO 9001:2015 certificate valid till September 2028 is enclosed.",
            "EMD of INR 20,00,000 submitted via Bank Guarantee BG-SOLAR-3390 valid for 180 days.",
            SOLAR_TECH_A,
            ROWS_SOLAR(24000, 110000, 75000000, 35000000, 60000000),
            421000000  # 10000*24000 (240M) + 100*110000 (11M) + 75M + 35M + 60M = 421M
        )
    },
    "SunRay Infra Pvt Ltd": {
        "submitted_at": "2026-10-07 11:45",
        "text": build_bid(
            "SunRay Infra Pvt Ltd", 2015,
            "FY2022-23 INR 27.5 crore, FY2023-24 INR 29.0 crore, FY2024-25 INR 31.5 crore",
            "(1) Solar project supplies for Gujarat Discom, INR 12.0 crore, completed 2023; (2) Solar power park works in Rajasthan, INR 14.5 crore, completed 2024.",  # Note: references "works/supplies", commissioning certs unclear
            "ISO 9001:2015 certificate valid till July 2027 is enclosed.",
            "EMD of INR 20,00,000 submitted via Demand Draft DD-661209.",
            SOLAR_TECH_B,
            ROWS_SOLAR(22000, 100000, 70000000, 32000000, 55000000),
            387000000  # 220M + 10M + 70M + 32M + 55M = 387M
        )
    },
    "PhotonWorks India Pvt Ltd": {
        "submitted_at": "2026-10-07 14:15",
        "text": build_bid(
            "PhotonWorks India Pvt Ltd", 2014,
            "FY2022-23 INR 26.0 crore, FY2023-24 INR 28.5 crore, FY2024-25 INR 30.0 crore",
            "(1) 2.5 MW Solar plant for BHEL, INR 11.0 crore, completed 2023; (2) 2.8 MW Solar for Cochin Port, INR 12.2 crore, completed 2024.",
            "ISO 9001:2015 certificate valid till May 2027 is enclosed.",
            "EMD of INR 20,00,000 submitted via BG-PW-8812.",
            SOLAR_TECH_C,
            ROWS_SOLAR(23000, 105000, 72000000, 34000000, 58000000),
            360000000  # ARITHMETIC DISCREPANCY: True sum = 230M + 10.5M + 72M + 34M + 58M = 404.5M, but quoted 360M
        )
    },
    "GreenVolt Systems Pvt Ltd": {
        "submitted_at": "2026-10-07 16:50",
        "text": build_bid(
            "GreenVolt Systems Pvt Ltd", 2016,
            "FY2022-23 INR 28.0 crore, FY2023-24 INR 30.5 crore, FY2024-25 INR 32.0 crore",
            "(1) 2.2 MW Solar installation for Maharashtra PWD, INR 10.5 crore, completed 2023; (2) 3.0 MW Solar for NTPC, INR 13.8 crore, completed 2024.",
            "ISO 9001:2015 certificate valid till October 2027 is enclosed.",
            "EMD of INR 20,00,000 submitted via DD-991245.",
            SOLAR_TECH_D,
            ROWS_SOLAR(25000, 115000, 76000000, 36000000, 62000000),
            435500000
        ).replace("Self-declaration: the company has not been blacklisted or debarred by any government agency.", "Self-declaration: formal non-blacklisting affidavit is currently under notarization and will be submitted separately on request.")  # FAILS E7
    }
}


def _make_bids_list(bids_dict):
    out = []
    for name, b in bids_dict.items():
        fname = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_") + "_Bid.md"
        out.append({"name": name, "filename": fname, "text": b["text"], "submitted_at": b["submitted_at"]})
    return out


def build_benchmark_data():
    """Return list of (tender_text, bids_list, known_winner, known_disqualified) for tenders 2-5."""
    return [
        (TENDER_TEXT_2.strip() + "\n", _make_bids_list(BIDS_2), "RoadBuild Pro Pvt Ltd", ["ConstructEase India Pvt Ltd"]),
        (TENDER_TEXT_3.strip() + "\n", _make_bids_list(BIDS_3), "TechForge Solutions Pvt Ltd", ["DevNest Technologies Pvt Ltd"]),
        (TENDER_TEXT_4.strip() + "\n", _make_bids_list(BIDS_4), "MedSupply Pharma Pvt Ltd", ["HealthFirst Devices Pvt Ltd"]),
        (TENDER_TEXT_5.strip() + "\n", _make_bids_list(BIDS_5), "SolarEdge Power Pvt Ltd", ["GreenVolt Systems Pvt Ltd"]),
    ]
