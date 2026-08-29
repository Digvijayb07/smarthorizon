# 📖 Module 6 — Regulations & Compliance

## Complete Research Document for Autonomous Financial Crime Investigation Agent

**Researcher:** Digvijay  
**Date:** 28 July 2026  
**Status:** Phase 1 Research — No Coding

---

## Table of Contents
1. [RBI (Reserve Bank of India)](#1-rbi-reserve-bank-of-india)
2. [NPCI (National Payments Corporation of India)](#2-npci-national-payments-corporation-of-india)
3. [AML (Anti-Money Laundering)](#3-aml-anti-money-laundering)
4. [KYC (Know Your Customer)](#4-kyc-know-your-customer)
5. [CDD (Customer Due Diligence)](#5-cdd-customer-due-diligence)
6. [EDD (Enhanced Due Diligence)](#6-edd-enhanced-due-diligence)
7. [PEP (Politically Exposed Persons)](#7-pep-politically-exposed-persons)
8. [FATF (Financial Action Task Force)](#8-fatf-financial-action-task-force)
9. [Suspicious Activity Report (SAR/STR)](#9-suspicious-activity-report-sarstr)
10. [Transaction Monitoring](#10-transaction-monitoring)
11. [Data Privacy — DPDP Act](#11-data-privacy--dpdp-act-2023)
12. [PCI DSS](#12-pci-dss)
13. [ISO 27001](#13-iso-27001)
14. [Critical Compliance Questions for Our System](#14-critical-compliance-questions-for-our-system)
15. [Compliance Architecture Recommendations](#15-compliance-architecture-recommendations-for-our-system)
16. [Summary Compliance Matrix](#16-summary-compliance-matrix)

---

## 1. RBI (Reserve Bank of India)

### What is it?
The Reserve Bank of India is India's central banking institution that controls monetary policy, regulates all banks and financial institutions, and oversees the payment and settlement systems in India. For fraud detection systems, RBI is the **ultimate regulatory authority** whose guidelines are non-negotiable.

### Why is it needed?
- RBI ensures financial stability and consumer protection across India's banking system
- It mandates how banks handle fraud, cyber security, customer grievances, and AI/ML usage
- Any system that touches banking data or makes decisions about financial transactions MUST comply with RBI regulations

### Key Regulatory Frameworks Relevant to Our System

#### a) RBI FREE-AI Framework (August 2025)
- **Full Name:** Framework for Responsible and Ethical Enablement of Artificial Intelligence
- Establishes foundational "Sutras" (principles) for ethical AI in finance
- **Key Principles:**
  - **Transparency** — AI decisions must be explainable
  - **Accountability** — Banks bear ultimate responsibility for AI decisions
  - **Fairness** — AI must not discriminate against any customer segment
  - **Security** — AI models must be robustly secured against adversarial attacks

#### b) Model Risk Management Framework (Draft — June 2026)
- **Critical for our system**: This is the most recent and directly relevant regulation
- **Key Mandates:**
  - Banks bear **ultimate accountability** for ALL AI-driven decisions — even if third-party models are used
  - Board of Directors must approve the Model Risk Management Framework (MRMF)
  - Covers the **entire lifecycle** of AI models: development → deployment → monitoring → decommissioning
  - **"Kill Switch" Mandate** — Every AI system must have an immediate override mechanism that allows human risk teams to suspend/deactivate the model instantly
  - Banks CANNOT blame AI for flawed decisions or customer harm

#### c) Master Directions on Fraud Risk Management (2024)
- Banks must maintain **robust internal fraud monitoring committees**
- Report fraud incidents to **LEAs (Law Enforcement Agencies)** and RBI within **21 days**
- Fraud of ₹1 lakh or more must be reported to LEAs
- Banks must constitute a **Special Committee of the Board for Monitoring and Follow-up of cases of Frauds (SCBMF)**
- **Fraud Monitoring Returns (FMR)** must be filed via the **XBRL system**
- Banks must implement **Early Warning Systems (EWS)** integrated with core banking systems

#### d) MuleHunter.AI
- RBI's **own** AI/ML-based solution for detecting mule accounts
- Currently being scaled across Indian banks
- This is important because it shows RBI is actively promoting AI for fraud detection — our system aligns with this regulatory direction

### Existing Solutions
- Banks currently rely on internal compliance teams + manual processes
- RBI provides guidelines; banks implement their own systems
- Most banks use combinations of rule-based systems + commercial solutions (FICO, SAS, etc.)

### Advantages of RBI's Approach
- Clear regulatory framework provides certainty for system design
- RBI is actively encouraging AI adoption (MuleHunter.AI proves this)
- Human-in-the-loop requirement reduces liability for AI errors

### Disadvantages / Challenges
- Regulations are evolving rapidly — what's compliant today may not be tomorrow
- Strict accountability model means banks are risk-averse about deploying autonomous AI
- Compliance costs are high — extensive documentation, audit trails, and governance structures needed

### Implications for OUR System
- ✅ We MUST implement a kill switch / override mechanism
- ✅ Every AI decision must be explainable (not just a risk score, but WHY)
- ✅ We MUST maintain complete audit trails for every action
- ✅ We MUST support human-in-the-loop for all material decisions
- ✅ Our system must generate FMR-compatible reports
- ✅ We must design for board-level governance integration

---

## 2. NPCI (National Payments Corporation of India)

### What is it?
NPCI is the umbrella organization for operating retail payment and settlement systems in India. It operates UPI, IMPS, RuPay, NACH, BBPS, and Bharat QR. For UPI fraud detection, NPCI guidelines are directly applicable.

### Why is it needed?
NPCI sets the operational rules for how payments flow through India's digital infrastructure. Any fraud detection system operating on UPI transactions must comply with NPCI Operating Circulars.

### Key Regulations & Guidelines

#### a) Mobile Application Security Framework (2025)
- Mandatory **Root Detection and Root Cloaking Detection** for all UPI apps
- PSPs and TPAPs must submit compliance audits from **CERT-IN empanelled auditors annually**
- All UPI applications must undergo rigorous security testing

#### b) UPI Information Security Compliance Framework
- Defines security standards for all UPI ecosystem participants
- TPAPs must ensure systems are audited for data protection and transaction integrity
- Covers device security, network security, and application security

#### c) Two-Factor Authentication (2FA) Mandate (April 2026)
- All domestic digital payments including UPI require **two authentication factors from different categories**
- At least one factor must be a **dynamic security measure**
- This affects how our system evaluates authentication strength during fraud assessment

#### d) Enhanced Fraud Monitoring Requirements
- Banks must deploy robust software for **real-time transaction monitoring**
- Use **network analytics** to identify suspicious patterns and mule networks
- **IDPIC (Indian Digital Payment Intelligence Corporation)** — Established October 2025 for real-time fraud detection across the digital payments ecosystem

#### e) Chargeback & Dispute Management
- **RGNB (Remitting Bank Raising Good Faith Negative Chargeback)** — Introduced July 2025
- Allows banks to raise genuine disputes even when standard chargeback rules decline
- Chargeback procedures must be followed per NPCI Operating Circulars

#### f) Merchant KYC Norms
- Mandatory full KYC verification (PAN/Aadhaar) even for small merchants
- No anonymous merchant onboarding allowed
- Critical for detecting merchant fraud

### Implications for OUR System
- ✅ Must integrate with NPCI's real-time monitoring infrastructure concepts
- ✅ Must understand UPI-specific fraud patterns (QR fraud, collect request fraud, etc.)
- ✅ Must handle chargeback workflows per NPCI OCs
- ✅ Must validate authentication strength as part of fraud scoring
- ✅ Must be compatible with IDPIC's intelligence sharing framework

---

## 3. AML (Anti-Money Laundering)

### What is it?
AML refers to the set of laws, regulations, and procedures designed to prevent criminals from disguising illegally obtained funds as legitimate income. In India, AML is primarily governed by the **Prevention of Money Laundering Act (PMLA), 2002**.

### Why is it needed?
- Money laundering enables crime — drug trafficking, terrorism, corruption, fraud
- Without AML controls, financial institutions become conduits for criminal money
- India processes billions of digital transactions daily — automated AML is essential
- International pressure (FATF) requires robust AML frameworks

### How does it work?

#### Legislative Framework
1. **PMLA, 2002** — Core legislation criminalizing money laundering
2. **PML Rules, 2005** — Prescribe procedures for record maintenance, identity verification, and FIU-IND reporting
3. **RBI Master Direction – KYC Direction, 2016** (updated periodically) — Operational manual for all Regulated Entities

#### Three Stages of Money Laundering
1. **Placement** — Introducing illicit money into the financial system
2. **Layering** — Complex series of financial transactions to disguise the origin
3. **Integration** — Merging the laundered money into the legitimate economy

### Key Compliance Requirements
| Requirement | Description | Relevance to Our System |
|---|---|---|
| **Customer Acceptance Policy (CAP)** | Define criteria for accepting customers, risk categorization | Risk scoring module |
| **Customer Identification Procedure (CIP)** | Verify identity using official valid documents | Identity verification agent |
| **CDD** | Ongoing due diligence ensuring transactions match risk profile | Continuous monitoring |
| **Record Keeping** | Maintain records for at least **10 years** | Audit trail / data retention |
| **STR Filing** | Mandatory filing with FIU-IND for suspicious transactions | Report generation module |
| **CTR Filing** | Cash transactions exceeding **₹10 lakhs** | Threshold monitoring |

### Enforcement Bodies
- **FIU-IND** — Central agency for receiving/processing financial intelligence
- **Enforcement Directorate (ED)** — Investigates and prosecutes PMLA offences
- Can attach and confiscate property involved in money laundering

### Penalties for Non-Compliance
- Significant regulatory penalties and legal action under PMLA
- Reputational damage — banks can be blacklisted
- Criminal prosecution for individuals involved

### Implications for OUR System
- ✅ Must implement all three levels: CDD, monitoring, and reporting
- ✅ Must detect patterns across placement, layering, and integration stages
- ✅ Must generate STR/CTR-compatible reports
- ✅ Must maintain 10-year record retention capability
- ✅ Must support "tipping off" prevention — no customer notification before STR filing

---

## 4. KYC (Know Your Customer)

### What is it?
KYC is the process of verifying the identity of customers before and during the business relationship. It is mandated by RBI under the Master Direction – KYC Direction, 2016.

### Why is it needed?
- Prevents identity fraud and synthetic identity attacks
- Enables risk-based approach to customer monitoring
- Required by law (PMLA) — non-compliance attracts penalties
- Foundation for effective AML and fraud detection

### How does it work?
#### KYC Process Flow
```
New Customer Application
    ↓
Identity Verification (Aadhaar, PAN, Passport, etc.)
    ↓
Address Verification (Utility bills, Bank statements)
    ↓
Risk Categorization (Low / Medium / High)
    ↓
Account Opening + Ongoing Monitoring
    ↓
Periodic KYC Renewal (Risk-based frequency)
```

#### Types of KYC
| Type | When Used | Documents |
|---|---|---|
| **Full KYC** | Regular account opening | Aadhaar + PAN + Photo + Address Proof |
| **e-KYC** | Aadhaar-based digital verification | OTP/Biometric + Aadhaar data |
| **Video KYC (V-KYC)** | Remote account opening | Video call + Document verification |
| **Simplified KYC** | Small accounts (₹50,000 limit) | Basic identity proof |

### Who uses it?
- Every bank, NBFC, and financial institution in India
- Payment service providers (PSPs) and TPAPs
- Insurance companies, mutual fund houses, securities intermediaries

### Existing Solutions
- **Aadhaar-based e-KYC** (UIDAI) — most widely used in India
- **DigiLocker** — for digital document verification
- **CKYC (Central KYC)** — centralized KYC registry by CERSAI

### Implications for OUR System
- ✅ Must assess KYC completeness as part of risk scoring
- ✅ Accounts with incomplete/expired KYC → higher risk score
- ✅ Must integrate with or reference CKYC data
- ✅ KYC status should be a key input to the investigation agent
- ✅ Must flag KYC anomalies (e.g., multiple accounts with same KYC documents)

---

## 5. CDD (Customer Due Diligence)

### What is it?
CDD is the **ongoing** process of monitoring customer accounts and transactions to ensure they are consistent with the bank's knowledge of the customer, their business, and their risk profile.

### Why is it needed?
- One-time KYC is insufficient — customer behavior changes over time
- CDD catches behavioral anomalies that static KYC cannot
- Required by RBI Master Direction and PMLA
- Essential for detecting account takeover, mule activity, and sudden behavioral shifts

### How does it work?

#### CDD Components
1. **Identifying the customer and verifying identity** (part of initial KYC)
2. **Identifying the beneficial owner** — who ultimately controls/benefits from the account
3. **Understanding the purpose and intended nature of the business relationship**
4. **Ongoing monitoring** — screening transactions against the customer's risk profile

#### Risk Categorization
| Risk Level | Customer Profile | CDD Level | Monitoring Frequency |
|---|---|---|---|
| **Low** | Salaried individual, stable transaction pattern | Standard | Periodic |
| **Medium** | Business owners, frequent travelers | Standard + | Monthly |
| **High** | PEPs, cash-intensive businesses, high-risk jurisdictions | Enhanced (EDD) | Continuous |

### Implications for OUR System
- ✅ Must maintain customer risk profiles and compare transactions against them
- ✅ Must detect deviations from established behavioral baselines
- ✅ Must support dynamic risk re-categorization based on new data
- ✅ Risk scoring must incorporate CDD risk level as a key factor
- ✅ Must trigger alerts when transaction patterns diverge from established profile

---

## 6. EDD (Enhanced Due Diligence)

### What is it?
EDD is a heightened level of due diligence applied to customers who present a **higher risk** of money laundering, terrorist financing, or other financial crimes. It goes beyond standard CDD with more intensive scrutiny.

### Why is it needed?
- High-risk customers require deeper scrutiny to prevent financial crime
- Mandated by RBI and FATF for specific customer categories
- Failure to apply EDD when required can result in severe regulatory penalties

### When is EDD Required?
- **Politically Exposed Persons (PEPs)** and their family members/close associates
- Customers from **high-risk countries/jurisdictions** (FATF grey/blacklist)
- **Cash-intensive businesses** (jewellers, real estate, casinos)
- **Complex ownership structures** (trusts, shell companies, layered entities)
- **Non-face-to-face customers** (online-only accounts)
- **Wire transfers** from/to sanctioned jurisdictions
- **Correspondent banking** relationships

### EDD Procedures
| Procedure | Description |
|---|---|
| **Source of Wealth (SOW)** | Document and verify how the customer accumulated their wealth |
| **Source of Funds (SOF)** | Verify the origin of specific funds being transacted |
| **Senior Management Approval** | Business relationship must be approved by senior management |
| **Enhanced Monitoring** | More frequent and intensive transaction monitoring |
| **Adverse Media Screening** | Check for negative news about the customer |
| **Sanctions Screening** | Check against OFAC, UN, EU sanctions lists |
| **Beneficial Ownership** | Identify ALL beneficial owners (>10% ownership threshold) |

### Implications for OUR System
- ✅ Must automatically detect when a customer triggers EDD requirements
- ✅ Must support different investigation depth levels based on risk tier
- ✅ Must integrate sanctions list checking (OFAC, UN Security Council, EU)
- ✅ Must flag PEP connections in the investigation graph
- ✅ Investigation reports must reflect EDD-level detail for high-risk subjects

---

## 7. PEP (Politically Exposed Persons)

### What is it?
PEPs are individuals who hold or have held prominent public functions. Due to their position of power and influence, they are considered **higher risk for corruption, bribery, and money laundering**.

### Who Qualifies as a PEP?
| Category | Examples |
|---|---|
| **Senior Politicians** | Ministers, Members of Parliament/Legislature |
| **Judicial Officials** | Supreme Court / High Court judges |
| **Military Officers** | Senior ranks in armed forces |
| **SOE Executives** | Leaders of state-owned enterprises |
| **Diplomats** | Ambassadors, consul generals |
| **Central Bank Officials** | Senior RBI officials |
| **Family Members** | Spouse, children, parents of PEPs |
| **Close Associates** | Business partners, advisors with known close ties |

### Why is it important for our system?
- PEP status changes the entire risk profile of an account
- Transactions involving PEPs require **mandatory EDD**
- PEP families and associates must also be monitored (guilt by association)
- Not all PEP activity is criminal — the challenge is distinguishing legitimate use from abuse

### Current Solutions
- **PEP databases**: Dow Jones, World-Check (Refinitiv/LSEG), LexisNexis
- Banks manually screen against these databases periodically
- Most banks update PEP lists quarterly — but PEP status can change daily

### Implications for OUR System
- ✅ Must integrate PEP database checking into the investigation pipeline
- ✅ Must detect PEP connections through graph analysis (family, associates)
- ✅ PEP-flagged accounts must automatically trigger EDD-level investigation
- ✅ Must distinguish between domestic and foreign PEPs (different risk levels)
- ✅ Investigation reports must clearly document PEP status and applied measures

---

## 8. FATF (Financial Action Task Force)

### What is it?
FATF is the global inter-governmental body that sets standards for combating money laundering, terrorist financing, and proliferation of weapons of mass destruction. FATF's **40 Recommendations** are the global benchmark for AML/CFT compliance.

### Why is it important?
- India's banking system is evaluated against FATF standards
- Countries on the FATF "grey list" face severe economic consequences
- India was placed in the **"regular follow-up" category** (best possible rating) in September 2024
- India was rated **Compliant or Largely Compliant in 37 out of 40 recommendations**
- 3 recommendations were "Partially Compliant" — none were "Non-Compliant"

### India's FATF Evaluation — Key Findings (2024 MER)

#### Strengths Recognized
- Sophisticated understanding of ML/TF risks
- **JAM Trinity (Jan Dhan, Aadhaar, Mobile)** — praised for making transactions traceable
- Effective beneficial ownership framework
- Strong domestic and international cooperation on financial intelligence

#### Areas for Improvement
- **Significant backlog** of money laundering court cases
- ML and TF trials need faster completion
- Need better focus on human trafficking, migrant smuggling, drug trafficking-related ML

### FATF Recommendations Most Relevant to Our System

| Recommendation | Description | Our System's Role |
|---|---|---|
| **R.1** | Risk-Based Approach | Core of our risk scoring engine |
| **R.10** | Customer Due Diligence | CDD verification in investigation |
| **R.11** | Record Keeping | 10-year audit trail |
| **R.12** | PEP Screening | PEP detection agent |
| **R.15** | New Technologies | Our multi-agent AI approach |
| **R.20** | Suspicious Transaction Reporting | STR generation module |
| **R.26** | Regulation of Financial Institutions | Compliance reporting features |

### Implications for OUR System
- ✅ Must implement a **Risk-Based Approach (RBA)** — this is FATF's fundamental principle
- ✅ Must demonstrate how our technology aligns with R.15 (New Technologies)
- ✅ Must generate reports compatible with FATF evaluation criteria
- ✅ Our system's use of AI must be justified through FATF's technology guidelines
- ✅ Can argue our system helps India maintain its "regular follow-up" status

---

## 9. Suspicious Activity Report (SAR/STR)

### What is it?
In India, the formal mechanism is called a **Suspicious Transaction Report (STR)**. It is a mandatory filing with **FIU-IND (Financial Intelligence Unit — India)** when a transaction is identified as suspicious.

### Why is it needed?
- Legal requirement under PMLA — failure to file is a criminal offense
- STRs are the primary intelligence tool for detecting financial crime at the national level
- FIU-IND analyzes STRs to identify patterns across the entire financial system

### When Must an STR Be Filed?
A transaction must be reported when it:
- **Deviates** from the customer's normal profile or risk categorization
- Involves **proceeds of any offense** listed under PMLA
- Has **no apparent lawful purpose** or is intended to bypass reporting requirements
- Involves **financing of terrorism**
- Shows **structuring** (breaking transactions to avoid thresholds)

### STR Filing Process
```
Suspicious Transaction Detected
    ↓
Alert Reviewed by Compliance Officer
    ↓
Principal Officer Determines Suspicion (within 7 working days)
    ↓
STR Prepared in XML Format (FIU-IND schema)
    ↓
Filed Electronically via FINnet 2.0 / FINGate 2.0 Portal
    ↓
FIU-IND Reviews and Analyzes
    ↓
Intelligence Shared with LEAs if Needed
```

### Key Requirements
| Requirement | Detail |
|---|---|
| **Filing Deadline** | Within **7 working days** of determination |
| **Filing Format** | Electronic XML format via FINGate 2.0 |
| **Filing Portal** | FINnet 2.0 / FINGate 2.0 |
| **Entity Registration** | Requires REID (Reporting Entity Identification Number) |
| **Confidentiality** | **"No Tipping Off"** — customer must NOT be informed |
| **Record Retention** | At least **5 years** from date of transaction |
| **Principal Officer** | Every bank must appoint one — responsible for monitoring and reporting |

### Other Reporting Obligations
| Report Type | Threshold | Frequency |
|---|---|---|
| **CTR (Cash Transaction Report)** | Cash transactions > ₹10 lakhs | Monthly by 15th of next month |
| **STR (Suspicious Transaction Report)** | Any suspicious transaction | Within 7 working days |
| **CCT (Counterfeit Currency Report)** | Any counterfeit notes | Monthly |
| **NTR (Non-Profit Org Transaction Report)** | NPO transactions of concern | As needed |

### Implications for OUR System
- ✅ **THIS IS OUR BIGGEST VALUE-ADD** — Automated STR generation
- ✅ Must generate STRs in FIU-IND compatible XML format
- ✅ Must implement "no tipping off" — no customer-facing alerts for STR cases
- ✅ Must maintain Principal Officer workflow integration
- ✅ Must support 7-working-day deadline tracking
- ✅ Investigation report must contain all data fields required by FIU-IND schema
- ✅ Must also support CTR generation for cash transactions
- ✅ 5-year minimum data retention for all reported transactions

---

## 10. Transaction Monitoring

### What is it?
Transaction monitoring is the **continuous, automated surveillance** of customer transactions across all channels (UPI, NEFT, RTGS, IMPS, cards, cash) to detect suspicious activity in real-time or near-real-time.

### Why is it needed?
- Required by RBI Master Directions and PMLA
- Without monitoring, fraud and money laundering go undetected until damage is done
- Volume of transactions (billions/day across India) makes manual monitoring impossible
- Regulatory expectation is for "scientific, data-driven" monitoring models

### How does it work?

#### Transaction Monitoring Architecture
```
Transaction Occurs
    ↓
Data Captured (amount, parties, time, device, location, channel)
    ↓
Real-Time Rule Engine (velocity, threshold, blacklist checks)
    ↓
ML/AI Anomaly Detection (behavioral deviation, pattern matching)
    ↓
Risk Score Generated
    ↓
Decision: Allow / Flag / Block / Escalate
    ↓
If Flagged → Alert Generated → Investigation Queue
    ↓
Analyst Review → SAR/STR Decision
```

#### Types of Monitoring
| Type | Description | Latency |
|---|---|---|
| **Real-Time** | Blocks transaction before completion | < 100ms |
| **Near-Real-Time** | Flags transaction within minutes | 1-30 minutes |
| **Batch/Retrospective** | Analyzes historical patterns | Daily/Weekly |
| **Network Analysis** | Maps connections between entities | Continuous |

### Current Industry Standards
- Banks must implement both rule-based and AI/ML-based monitoring
- Rules must be reviewed and updated at least annually
- False positive rates must be tracked and optimized
- Monitoring must cover ALL channels — not just UPI

### Implications for OUR System
- ✅ Must support multi-channel transaction monitoring
- ✅ Must provide real-time risk scoring (< 100ms)
- ✅ Must combine rules engine + ML-based anomaly detection
- ✅ Must prioritize alerts by severity (not just flag everything)
- ✅ Must track false positive rates and provide feedback loops
- ✅ Must support both real-time blocking and retrospective analysis

---

## 11. Data Privacy — DPDP Act, 2023

### What is it?
The **Digital Personal Data Protection Act, 2023** is India's comprehensive data protection legislation. It regulates how personal data is collected, processed, stored, and deleted — with direct implications for any AI system handling banking data.

### Why is it critical for our system?
Our system will process massive amounts of personal financial data. DPDP Act compliance is not optional — penalties reach up to **₹250 crore** per violation. Compliance deadline is **May 13, 2027**.

### Key Provisions Affecting Our System

#### a) Consent and Transparency
- Must obtain **informed, granular, and specific consent** for processing personal data
- Customers must be informed when their data is used for **algorithmic decision-making**
- Cannot process data beyond the stated purpose

#### b) Purpose Limitation & Data Minimization
- Data must be collected and processed only for **specified objectives**
- AI systems cannot over-collect data "just in case" for model training
- Data must remain **relevant** to the stated purpose

#### c) Significant Data Fiduciary (SDF) Classification
- Banks will almost certainly be classified as SDFs
- **Additional obligations for SDFs:**
  - Appoint a **Data Protection Officer (DPO)** based in India
  - Conduct periodic **Data Protection Impact Assessments (DPIAs)**
  - Undergo **independent data audits**

#### d) Algorithmic Fairness & Explainability
- Growing expectation for banks to provide **explainability** for automated outcomes
- Automated decisions (fraud flagging, account blocking) must be justifiable
- Customers have right to **contest automated decisions**

#### e) Human-in-the-Loop (HITL)
- High-stakes automated decisions must have **human oversight**
- Decisions must be reviewable and rectifiable by a human officer
- AI "hallucinations" and bias must be mitigated through human validation

#### f) Data Localization
- Financial and transaction data **must be stored on servers within India**
- Cloud AI services must comply with data residency requirements

#### g) Grievance Redressal
- Must provide effective mechanism for customer complaints
- If AI makes an error, clear path for contesting the decision
- Must provide human intervention option

### Implications for OUR System
- ✅ Must implement consent management for data processing
- ✅ Must enforce data minimization — collect only what's needed for fraud investigation
- ✅ Must store all data in India (no offshore processing of PII)
- ✅ Must provide explainable decisions — not just risk scores
- ✅ Must support customer grievance and decision contestation workflows
- ✅ Must implement DPO interface for oversight
- ✅ Must be designed with privacy-by-design principles embedded
- ✅ Must support DPIA documentation generation

---

## 12. PCI DSS

### What is it?
**Payment Card Industry Data Security Standard** — the global security standard for entities that process, store, or transmit cardholder data. Currently at version **4.0.1** (future-dated requirements became mandatory **March 31, 2025**).

### Why is it needed?
- RBI mandates PCI DSS compliance for financial institutions and payment system operators
- Protects cardholder data (card numbers, CVVs, PINs) from theft
- Non-compliance can result in massive fines and loss of card processing ability

### Key Requirements Relevant to Our System

| Requirement | Description | Relevance |
|---|---|---|
| **Req 3** | Protect stored account data | Encryption of any card data in our system |
| **Req 6.4.3** | Inventory of all scripts on payment pages | If our system interacts with payment pages |
| **Req 7** | Restrict access by business need-to-know | Role-based access control in our dashboard |
| **Req 8** | Multi-factor authentication | Admin/analyst authentication |
| **Req 10** | Log and monitor all access to system components | Complete audit logging |
| **Req 11** | Regularly test security systems | Vulnerability scanning |
| **Req 11.6.1** | Detect unauthorized changes to scripts | Integrity monitoring |
| **Req 12** | Maintain an information security policy | Documentation requirement |

### Critical Focus Areas (Common Failure Points)
- **Req 6.4.3 & 11.6.1** — Most difficult to pass; mandate inventory of ALL scripts on payment pages and detect unauthorized changes
- Direct response to **Magecart-style e-skimming attacks**
- **Expanded MFA requirements** — phishing-resistant authentication methods

### Implications for OUR System
- ✅ If we handle card data, we MUST be PCI DSS compliant
- ✅ Even if we DON'T handle card data directly, our analytics on card transactions must follow PCI DSS principles
- ✅ Must implement encryption at rest and in transit for any payment data
- ✅ Must enforce strict role-based access control (RBAC)
- ✅ Must maintain complete access logs
- ✅ Design recommendation: **Tokenize** card data before it enters our system — avoids PCI scope

---

## 13. ISO 27001

### What is it?
ISO 27001 is the international standard for **Information Security Management Systems (ISMS)**. It provides a systematic, risk-based framework for managing the security of information assets — covering people, processes, and technology.

### Why is it needed?
- Widely adopted by Indian banks — often treated as a **mandatory benchmark**
- Satisfies both regulatory audits and global contractual requirements
- Aligns with RBI's cybersecurity expectations
- Demonstrates that rigorous security controls are in place

### Key Areas Relevant to Our System

#### Information Security Controls
| Control Area | Description | Our System's Need |
|---|---|---|
| **Access Control** | Role-based, need-to-know access | Analyst, admin, auditor roles |
| **Cryptography** | Encryption of data at rest and in transit | TLS, AES-256 |
| **Physical Security** | Server room controls | Cloud provider responsibility |
| **Operations Security** | Change management, logging | CI/CD pipeline, audit logs |
| **Communications Security** | Network segmentation, firewall | API security, network isolation |
| **System Acquisition** | Secure development lifecycle | Secure coding practices |
| **Incident Management** | Breach response procedures | Incident response automation |
| **Business Continuity** | Disaster recovery, backup | High availability architecture |
| **Compliance** | Legal/regulatory adherence | This entire document |

#### Alignment with RBI Requirements
- RBI references ISO 27001 as an accepted standard for demonstrating adequate security
- Implementing ISO 27001 helps close regulatory gaps
- Provides framework for DPDP Act compliance

### Implications for OUR System
- ✅ Must design system architecture aligned with ISO 27001 controls
- ✅ Must implement comprehensive logging and monitoring
- ✅ Must have documented incident response procedures
- ✅ Must implement change management and version control for all AI models
- ✅ Must design for business continuity (99.9%+ uptime requirement for banking systems)
- ✅ Must support regular security audits and penetration testing

---

## 14. Critical Compliance Questions for Our System

These are the specific questions from the research plan, answered with regulatory precision:

### Can AI Block an Account?

**SHORT ANSWER: NO — not autonomously.**

**Detailed Analysis:**
- Banks do **NOT** have inherent power to freeze/block accounts based solely on AI suspicion
- Account freezing requires authorization from **LEAs** or a **court order** (Section 106, Bharatiya Nagarik Suraksha Sanhita)
- Courts have held that freezing an entire account is often **arbitrary and violates fundamental rights** unless proportionate to the alleged fraud
- Banks should freeze only the **specific amount** linked to the suspicious transaction, not the entire balance
- **RBI's position**: AI decisions must have human-in-the-loop oversight; AI models must have "kill switch" mechanisms

**What Our System CAN Do:**
```
AI Detects Suspicious Activity
    ↓
System Generates Risk Score + Explanation
    ↓
Alert Sent to Human Analyst
    ↓
Analyst Reviews Evidence Package
    ↓
Analyst Makes Decision (with system's recommendation)
    ↓
If Block Needed → Analyst Initiates via Banking System
    ↓
System Logs Everything for Audit Trail
```

**Design Principle: AI RECOMMENDS, Human DECIDES.**

### Is Human Approval Required?

**YES — for all material financial decisions.**

- RBI mandates strong human oversight for AI-driven decision-making
- AI models cannot operate in isolation for decisions with **material financial impacts**
- Banks must ensure decisions can be **reviewed and reversed** by human personnel
- Customers must have an option to **switch to a human operator** at any stage

### What Audit Logs Are Required?

**Comprehensive and immutable audit trails:**
- Every AI decision must be logged with: timestamp, input data, model version, confidence score, explanation
- Every human action must be logged: who, what, when, why
- All data access must be logged
- Logs must be tamper-proof and digitally signed
- Retention: **minimum 5 years** (STR-related), **10 years** (AML-related)
- Must be producible for regulatory inspection within **24 hours**

### What Are Data Retention Requirements?

| Data Type | Retention Period | Authority |
|---|---|---|
| KYC Records | 5 years after relationship ends | PMLA |
| Transaction Records | 10 years | RBI Master Direction |
| STR/CTR Records | 5 years from filing date | FIU-IND |
| Audit Logs | 10 years minimum | RBI |
| AI Model Decisions | 10 years (recommended) | RBI MRM Framework |
| Communication Records | 8 years | IT Act |

### What About Privacy?

- **DPDP Act** governs all personal data processing
- Financial data must be stored in India (data localization)
- Consent required for processing
- Data minimization principle — collect only what's necessary
- Right to erasure — but conflicts with AML retention requirements (AML overrides)
- Must implement anonymization/pseudonymization where possible
- Penalties up to ₹250 crore for violations

### Is Explainability Required?

**YES — mandatory for compliance.**

- RBI FREE-AI Framework requires transparency in AI decisions
- DPDP Act requires customers to be informed about automated decision-making
- Model Risk Management Framework requires explainable models
- FATF R.15 requires that new technologies be transparent and auditable
- Every fraud alert must explain **WHY** — not just a score

---

## 15. Compliance Architecture Recommendations for Our System

Based on this research, our system MUST implement these compliance layers:

### Layer 1: Data Governance
```
┌──────────────────────────────────────┐
│         Data Governance Layer        │
├──────────────────────────────────────┤
│ • Data localization (India only)     │
│ • Encryption at rest (AES-256)       │
│ • Encryption in transit (TLS 1.3)    │
│ • Data minimization enforcement      │
│ • Consent management                 │
│ • Anonymization/Pseudonymization     │
│ • Tokenization of sensitive data     │
└──────────────────────────────────────┘
```

### Layer 2: Investigation Compliance
```
┌──────────────────────────────────────┐
│     Investigation Compliance Layer   │
├──────────────────────────────────────┤
│ • KYC/CDD/EDD verification          │
│ • PEP screening                     │
│ • Sanctions list checking            │
│ • Risk-based approach (FATF R.1)     │
│ • Human-in-the-loop for decisions    │
│ • AI recommendation + human approval │
│ • "Kill switch" for AI models        │
└──────────────────────────────────────┘
```

### Layer 3: Reporting & Audit
```
┌──────────────────────────────────────┐
│       Reporting & Audit Layer        │
├──────────────────────────────────────┤
│ • STR generation (FIU-IND XML)       │
│ • CTR generation                     │
│ • FMR (Fraud Monitoring Return)      │
│ • Immutable audit trail              │
│ • Explainable AI logs (SHAP/LIME)    │
│ • Retention policy enforcement       │
│ • Regulatory report templates        │
└──────────────────────────────────────┘
```

### Layer 4: Security & Access
```
┌──────────────────────────────────────┐
│       Security & Access Layer        │
├──────────────────────────────────────┤
│ • Role-based access control (RBAC)   │
│ • Multi-factor authentication        │
│ • ISO 27001 aligned controls         │
│ • PCI DSS compliance (if card data)  │
│ • Incident response automation       │
│ • Vulnerability management           │
│ • Penetration testing support        │
└──────────────────────────────────────┘
```

---

## 16. Summary Compliance Matrix

| Regulation | Authority | Mandatory? | Key Requirement for Our System | Penalty for Non-Compliance |
|---|---|---|---|---|
| **RBI FREE-AI** | RBI | Yes | Explainable, ethical AI | Regulatory action |
| **RBI MRM Framework** | RBI | Yes (Draft) | Kill switch, board governance | License risk |
| **RBI Fraud Risk Mgmt** | RBI | Yes | EWS, FMR, 21-day reporting | Regulatory penalties |
| **NPCI Security** | NPCI | Yes (UPI) | Annual audits, 2FA, device security | UPI ecosystem exclusion |
| **PMLA/AML** | FIU-IND/ED | Yes | CDD, STR, 10yr records | Criminal prosecution |
| **KYC** | RBI | Yes | Identity verification, risk categorization | Account restrictions |
| **FATF Standards** | Global | Indirect | Risk-based approach, transparency | Grey-listing (country) |
| **STR** | FIU-IND | Yes | 7-day filing, XML format, no tipping off | Criminal prosecution |
| **DPDP Act** | MeitY | Yes | Consent, data minimization, DPO | ₹250 crore per violation |
| **PCI DSS** | PCI SSC | If cards | Encryption, access control, logging | Fines, processing rights |
| **ISO 27001** | ISO | Best practice | ISMS framework, security controls | Audit failures |

---

## Key Takeaway for Final Brainstorming

> **Our system's BIGGEST differentiator should be compliance-readiness.**
> 
> Most existing fraud detection tools detect fraud but do NOT generate compliance-ready reports, maintain regulatory audit trails, or support human-in-the-loop decision workflows. If we build a system that is **investigation + compliance + audit-ready from Day 1**, we solve a real pain point that banks currently handle manually.
> 
> **The design principle is clear: AI RECOMMENDS, Human DECIDES, System DOCUMENTS.**

---

*This document is part of the Smart Horizon Hackathon Research Bible — Phase 1.*
*Last updated: 28 July 2026*
