# initial goals
────────────────────────────────────────────────────────────────────────────
Bitvavo PnL Dashboard – WHY & WHAT
────────────────────────────────────────────────────────────────────────────
Context
-------
I’ve been dabbling with a grab‑bag of crypto – BTC, ETH, XRP, DOGE, you name it.
Trades, deposits, withdrawals, random buy‑the‑dip moments at 2 AM – the works.
Result: a jungle of Bitvavo transactions nobody (including me) can eyeball
anymore.


Objective (a.k.a. the whole point)
----------------------------------
**Give me, on command, a single crystal‑clear picture of how each coin and the
portfolio as a whole is performing – both realised and unrealised – without
Excel acrobatics or manual copy‑pasting.**

Why it matters
--------------
1. **Tax reporting:** Dutch fiscus wants FIFO numbers, not vibes.
2. **Risk control:** Know when I’m over‑exposed before I feel it in my gut.
3. **Decision speed:** “Should I dump or double‑down right now?” answered in
   under 5 seconds.

Core requirements
-----------------
1. **Data source** – Official Bitvavo API only.  
   - Pull full trade history per asset (paginated).  
   - Pull current balances.  
   - Pull live EUR price per asset.

2. **PnL engine** – Deterministic, test‑covered FIFO algorithm.
   - Handles partial lot sales.  
   - Splits realised vs. unrealised PnL.  
   - Works for any asset Bitvavo lists.

3. **Output** – Two flavours, same data:
   a. **CLI**: `python portfolio.py` → pretty table + grand‑total row.  
   b. **Streamlit**: `/dashboard` → interactive filter by asset + charts.

4. **UX speed** – <3 s from ENTER to results on a typical home Wi‑Fi.

5. **Ops** – Run local with just `python -m venv venv && pip install -r requirements.txt`.

Stretch goals (nice, not mandatory today)
-----------------------------------------
- CSV export.  
- Dark‑mode toggle in Streamlit.  
- Dockerfile for zero‑setup deployment on a NAS/Portainer.

Non‑goals
---------
- No margin, staking, or earn products – spot trades only for now.  
- No multi‑exchange aggregation (Bitvavo first, everything else later).  
- No AI‑driven trading decisions; pure reporting.

Ground rules for any contributor
--------------------------------
- Keep it **first‑principles & grounded**: read API docs, fail loud on missing
  env vars, write unit tests for maths.  
- Single‑file vertical slice per feature: don’t architect a cathedral.  
- Type hints everywhere; no inline comments unless the logic is non‑obvious.  
- One PR = one logical change.  🚦

Success criteria
----------------
I can:
1. Clone repo, set two env vars, run script, and instantly answer  
   “How much am I up or down on ADA since 2021?”  
2. Hand the output PDF/CSV to my accountant without follow‑up questions.  
3. Sleep better because the numbers are *known*, not *guessed*.

That’s it – build accordingly, keep it lean, and call me out if scope‑creep
sneaks in.
────────────────────────────────────────────────────────────────────────────
