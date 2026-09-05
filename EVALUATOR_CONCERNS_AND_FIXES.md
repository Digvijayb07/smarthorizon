# Safe Flow — Evaluator Concerns & Fixes Summary

Consolidated from the final-evaluation prep discussion. Four concerns, each with the core issue and the concrete fix/talking point.

---

## 1. RBAC (Admin / Manager / Investigator) — "why does this exist?"

**The problem:** The demo showed three role views without explaining *why* three roles exist — it read as UI decoration rather than architecture.

**The fix — frame it as "three lines of defense" (a real banking control principle):**
- **Investigator (1st line):** detects and investigates, but cannot unilaterally freeze an account.
- **Manager (2nd line):** independently reviews the investigator's recommendation before high-impact action (maker-checker) — the person who found the case isn't the person who approves the consequence.
- **Admin (3rd line):** owns audit trail, user access, and system integrity — independent of case decisions entirely.

**Talking point:** *"No single role can both detect and act on a case unilaterally — that separation prevents both compliance errors and insider abuse, and mirrors how real banks structure fraud operations."*

---

## 2. The NetworkX Graph — "so what? How does this help investigation?"

**The problem:** Showing account connectivity isn't the same as helping someone decide what to do. "We traced money to 4 accounts and stopped" is a weak answer if that's all the graph does — it doesn't explain the hop limit or produce an actionable output.

**The fix — turn the graph into a freeze-priority tool, not just a visualization:**
For each downstream account in the trace, compute and surface:
- **% of the original flagged amount that reached it** (e.g., ₹40,000 of ₹1,00,000 sits in Account C).
- **Dwell time** — how long the money has sat untouched (short dwell = still recoverable; mule funds are typically dispersed within hours of arrival, so dwell time is a real, meaningful signal).
- **A ranked recommendation** — e.g., "Freeze Account C and D immediately — ₹75,000 recoverable. Account B's funds already moved — refer to law enforcement, freezing recovers nothing."

**Why this also answers "why stop at 4 accounts":** You're not capping hops arbitrarily — you trace until funds hit a terminal cash-out point or dwell time indicates the trail is stale, and that stopping point is itself a finding, not a limitation.

**Talking point:** *"We don't cap hops artificially — we trace until the money hits a terminal cash-out point or the trail goes cold, and we surface that stopping point as part of the investigation output, not as an omission."*

---

## 3. Passing account numbers / transaction IDs to the LLM — security & data-leak concern

**The problem:** Real customer identifiers (account numbers, transaction IDs) going to a third-party LLM API (Gemini) is a legitimate red flag, not a misreading by the evaluator — this is exactly the kind of data flow banking regulators scrutinize.

**The fix — a masking/pseudonymization layer between your data and the prompt:**
```python
def mask_for_llm(transaction, customer):
    masked = {
        "account_ref": f"ACC_{hash_to_short_id(transaction.sender_account_id)}",
        "counterparty_ref": f"ACC_{hash_to_short_id(transaction.receiver_account_id)}",
        "case_ref": f"CASE_{transaction.case_id}",
        "amount": transaction.amount,
        "channel": transaction.channel,
        "risk_factors": shap_top_factors,
    }
    return masked
    # Real account_id <-> ACC_xxx mapping lives only in your own DB —
    # never sent to Gemini. Re-hydrate to real identity only when
    # rendering the report for the analyst.
```
The LLM only ever sees pseudonymous references, transaction behavior, and risk factors — never real account numbers, names, or phone numbers.

**Talking point:** *"We identified that raw identifiers shouldn't leave our infrastructure to a third-party model — we pseudonymize before the LLM call and re-hydrate identities only inside our own system for the analyst's view. In production, this would go further — a data processing agreement with the LLM vendor, or a self-hosted model entirely, since customer financial data leaving the bank's infrastructure is exactly what RBI outsourcing and data-localization expectations scrutinize."*

---

## 4. Cross-bank tracing — "how would you even have access to another bank's transactions?"

**The problem:** Once money moves from Bank X to Bank Y, Bank X has no legitimate access to Bank Y's internal ledger. The prototype's multi-bank graph (SBI → Canara → Kotak → Axis → ICICI) implicitly assumes a shared ledger view across banks that would not exist in reality.

**What's real vs. simulated in that graph:**
- **Real:** the *first hop* across a bank boundary. Every interbank transfer (UPI/IMPS/NEFT/RTGS) carries the counterparty's account number and bank/IFSC code for routing — so your own ledger legitimately knows money went to a specific account at another bank.
- **Simulated for the demo:** anything showing continued tracing *through* that external bank and back out the other side (e.g., activity inside Axis after the money lands). That's outside any single bank's real visibility.

**The fix — relabel the trace boundary honestly:**
- Any node representing a different bank should be labeled **"Last Known Hop — External Bank"**, not treated as a fully investigated endpoint.
- Frame it as: *"transaction exited our bank's visibility here — this is the boundary of what our ledger can independently confirm."*

**The real cross-bank mechanism — cite this instead of pretending your graph does it:**
- **NPCI**, as the switch routing every UPI transaction between banks, already has fraud-monitoring visibility across both sides of an inter-bank transfer, and provides fraud-monitoring tooling to banks on that basis.
- **RBI's Central Payments Fraud Information Registry (CPFIR)**, operational since March 2020 (now migrated to the RBI's DAKSH platform), aggregates payment fraud reports across all regulated reporting entities — this is the actual place where Bank X's and Bank Y's independently-filed reports on the same fraud can be correlated.

**Talking point:** *"For the prototype we simulated multiple banks in one dataset because we don't have access to real multi-bank data — but the design reflects a real constraint: we only trace with confidence up to the first hop into another bank, because that's the boundary of what payment-rail metadata actually gives us. Beyond that, our STR filing is exactly what hands off to the regulator-level mechanism — NPCI and RBI's CPFIR — that's actually authorized to correlate across banks. We're not claiming to see into another bank's ledger; we're claiming to correctly identify where our visibility ends."*

---

## The common thread across all four

Every one of these lands better as **"we identified this constraint and here's how we handled it"** than as a defense that the constraint doesn't exist. That's the same posture that worked for the ML dataset-leakage issue earlier — naming the boundary and showing the mitigation is worth more to a technically literate judge than a demo that quietly hopes no one asks.
