# MEMORY.md - Long-Term Memory

> Your curated memories. Distill from daily notes. Remove when outdated.

---

## About [Human Name]

### Key Context
[Important background that affects how you help them]

### Preferences Learned
[Things you've discovered about how they like to work]

### Important Dates
[Birthdays, anniversaries, deadlines they care about]

---

## Lessons Learned

### [Date] - [Topic]
[What happened and what you learned]

---

## Trading Goals

### Current Targets (Updated 2026-02-19)
| Metric | Target | Current Status |
|--------|--------|-----------------|
| Win Rate | ≥70% | 80.8% ✅ |
| **Profit** | **>0** | -$56.22 ❌ |

### Strategy
- Focus on **profitability** over high win rate
- min_split: 65%
- max_bet: $3
- expiry: 3 min

### Simmer Config
- API: sk_live_XXXXX_REDACTED
- Balance: $10,000 virtual

### Key Decisions Made

- **2026-02-25**: Integrated efinance for real-time fund flow data (主力净流入)
  - Created fund_flow.py module
  - Added to scoring: +20 for >100M, +10 for >10M, -10 for negative
  - System now has policy analysis + fund flow = unique among open source systems

### Things to Remember

- System runs 9:25 daily, 30-min scan cycle
- Current positions: 5 stocks (all on 创业板)
- Fund flow shows all positions negative today
- For real trading: need 30万+ for 券商API (华鑫证券 lowest门槛)

---

## Relationships & People

### [Person Name]
[Who they are, relationship to human, relevant context]

---

*Review and update periodically. Daily notes are raw; this is curated.*
