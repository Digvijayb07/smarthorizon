# **Targeted Stakeholders:** 

1. **Fraud Investigation Teams / Analysts (primary, day-to-day user)** — they open the dashboard, work the case queue, read the agent's reasoning, click Allow/Verify/Block. This is who your live demo is built for. 

2. **Banks & Financial Institutions / Compliance Officers (buyer + oversight)** — they care about SLA compliance, audit-readiness, RBI reporting, and false-positive reduction. This is who your ROI slide is built for. 

|**Queston**|**What it means**|**How you can implement it**|
|---|---|---|
|**Who receives**<br>**the alert?**|When an AI model fags a suspicious<br>transacton, it doesn't directly notfy<br>the customer. It creates a case that<br>goes to a**Level-1 Fraud Analyst**who<br>investgates.|Create a dashboard where suspicious<br>transactons automatcally appear in<br>an investgator's queue. Assign<br>priority based on the AI risk score.|
|**Which**<br>**sofware?**|Large banks use platorms like**NICE**<br>**Actmize, Feedzai, or FICO Falcon**.<br>Many smaller banks stll rely on<br>simpler internal systems or even<br>spreadsheets.|Build your own lightweight case<br>management system that mimics<br>these enterprise tools instead of<br>trying to use them.|
|**Which**<br>**dashboard?**|Analysts see a queue of fraud cases<br>sorted by urgency.|Include flters like High Risk, Medium<br>Risk, Open Cases, Closed Cases,<br>Overdue Cases, and a search<br>functon.|
|**What**<br>**evidence?**|The analyst reviews all available<br>informaton before deciding whether<br>the transacton is fraudulent.|<br>Show details such as transacton<br>amount, customer profle, locaton,<br>device ID, previous transactons, and<br>risk score.|
|**What APIs?**|Banks gather data from many<br>systems: core banking, payment<br>networks (like UPI), credit bureaus,<br>watchlists, and device intelligence<br>services.|For a hackathon, simulate these APIs<br>with sample datasets or mock<br>endpoints rather than integratng<br>real banking systems.|



|**Queston**|**What it means**|**How you can implement it**|
|---|---|---|
|**What**<br>**databases?**|Banks store customer data,<br>transactons, fraud cases, watchlists,<br>and audit logs in separate databases.|<br>Use separate collectons/tables for<br>Users, Transactons, Cases, Alerts,<br>and Audit Logs.|
|**How much**<br>**tme?**|Inital review takes minutes or hours.<br>Complex investgatons can take<br>weeks or months due to legal and<br>regulatory requirements.|<br>Your demo can show the case<br>lifecycle: Open → Under Review →<br>Escalated → Closed.|
|**How is the**<br>**report**<br>**generated?**|Investgators manually write a<br>report, atach evidence, and the<br>sofware formats it into the<br>regulator's required template.|Add a "Generate Investgaton<br>Report" buton that compiles case<br>details into a PDF or structured<br>report automatcally.|
|**How is the**<br>**decision**<br>**approved?**|Banks use a**maker-checker**process:<br>one analyst investgates, another<br>person approves the fnal decision.|Implement role-based access where<br>an Analyst submits a<br>recommendaton and a Manager<br>approves or rejects it.|





<!-- Start of picture text -->
i’. 1. FRAUD ALERT<br>a| | or customer(EWS/rulescomplaint)engine Spe Sel SSe tessa yh,i<br>AaN 2. CASE AUTO-CREATED& RISK-PRIORITIZED ;<br>ee : (Case Management System) :<br>' e Risk Score Assigned ¢ SLA Timer Started ;<br>DATA SOURCES (= ,<br>(APIs / INTERNAL 3. ANALYST TRIAGE :<br>SYSTEMS) re (device, geo, KYC, transaction<br>inl history pulled manually) '<br>[] i]i] ¢ View Alert Details * Customer Profile ‘<br>x3 ¢ Transaction History ¢ Device & Geo Info :<br>Core Banking 5 '<br>System (CBS) | :<br>L_j=) 4. ENHANCED DUE DILIGENCE<br>NPCI / UPI ee x customer(linked accouco nt acted)s, network, :‘<br>Switch ; c :<br>¢ Linked Accounts/ Beneficiaries '<br>* Contact Customer / Obtain Clarification ;<br>CANa Ae <--> ¢¢ NetworkAdditional AnalysisDocument / KYC Check ;‘<br>Device Intelligence Feedback Loop<br>& Geo Location (Continuous<br>5. DECISION Improvement)<br>Oe a<br>(ea ‘<br>KYC/Customer | = ;<br>Master (Vv) () ;<br>fl CLOSE CASE(Genuine / No FRMESCALATECOMMITTEE TO CLASSIFYAS RFA Hy<br>Credit Bureau Suspicion) (High Risk / Complex (Reportable Fraud 4<br>APIs Cases) Activity) :<br>7 6. SAR/STR DRAFTED MANUALLY t<br>Sanctions/ PEP/ 4? ®& FILED WITH FIU-IND ;<br>Watchlist APIs a" : (natural-justice check for i<br>borrower response) H<br>© Draft SAR/STR  « Attach Evidence ;<br>¢ Borrower Response (if applicable) '<br>¢ File with FIU-IND within TAT :<br>7. AUDIT TRAIL LOGGED<br>+ RULE/THRESHOLD FEEDBACK LOOP :<br>* All Actions Logged (Who, When, What) le kdhay<br>¢ Audit Trail Immutable<br>¢ Rule/Threshold Performance Review<br>¢ Feedback to EWS/ Rules Engine<br><!-- End of picture text -->

|**Platorm**|**Explainable**<br>**AI**|**Case**<br>**Management**|**Indian**<br>**Payments**<br>**(UPI/IMPS)**|**GenAI**<br>**Reports**|**Afordable for**<br>**Mid-size Banks**|
|---|---|---|---|---|---|
|FICO Falcon|◐|||||
|Feedzai|||◐|||
|Featurespace|||◐|||
|SAS Fraud Mgmt|◐||◐|||
|Stripe Radar|◐|◐|||◐|
|Visa Risk Manager||◐||||
|Mastercard<br>Decision<br>Intelligence||◐||||
|NICE Actmize|||◐|||
|BioCatch||||||
|Sif|◐|◐|◐||◐|
|Alloy|||◐||◐|
|Sardine|||◐||◐|



# **Gap in Existing Solutions** 

Existing platforms detect fraud and manage cases but rarely provide: 

- Explainable AI-based verdicts 

- Automatic investigation summaries 

- RBI/FIU-IND compliant report drafting 

- Affordable deployment for Indian mid-size banks 

