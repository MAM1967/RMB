# PRD: Recruiter Market Brief - Phase 1 MVP
**Version:** 1.0  
**Target Ship Date:** 4 weeks from kickoff  
**Owner:** Michael McDermott

---

## Objective

Ship a bi-weekly newsletter that provides quantitative insights on executive hiring market conditions, starting with 73 companies using Ashby, Greenhouse, and Lever ATS platforms.

**Success Criteria:**
- First newsletter published with real data within 4 weeks
- 3 core metrics delivered per issue
- Data pipeline runs automatically
- Newsletter takes <2 hours to produce per issue

---

## Scope: What We're Building

### In Scope (Phase 1)
1. **Data Pipeline:** Scrape 73 companies (67 Ashby + 4 Greenhouse + 2 Lever)
2. **Core Metrics:** 3 quantitative insights per newsletter
3. **Newsletter Production:** Templated markdown → email via MailerLite/ConvertKit
4. **Cadence:** Bi-weekly (every 2 weeks)

### Out of Scope (Future Phases)
- Workday companies (120+ additional companies)
- Advanced scoring algorithms
- Automated chart generation
- Editorial dashboard/UI
- Custom ATS scraping
- Real-time alerts

---

## The RMI-73 Index

### Company Selection Criteria
**73 companies across major sectors using modern ATS platforms:**

**By Platform:**
- Ashby: 67 companies (92%)
- Greenhouse: 4 companies (5%)
- Lever: 2 companies (3%)

**By Size:**
- Large enterprises: 62 companies (85%)
- Growth companies: 11 companies (15%)

**By Sector (Top 5):**
- Tech & Fintech: 14 companies (19%)
- Manufacturing: 7 companies (10%)
- Healthcare & Pharma: 9 companies (12%)
- Banking & Finance: 7 companies (10%)
- Logistics & Transportation: 7 companies (10%)
- Other 21 sectors: 29 companies (39%)

**Notable Companies:**
- Enterprise: Amazon, GE, Intel, UPS, Delta, Bank of America, Johnson & Johnson
- Growth: OpenAI, Canva, Stripe, Coinbase, Brex, Rippling

### Why This Index Works
✓ Sector diversity (28 unique sectors)
✓ Mix of stable + hot companies
✓ All have public careers pages
✓ Consistent scraping (single platform per company)
✓ Low maintenance burden

---

## Core Metrics (The "Newsletter Facts Packet")

Each newsletter delivers exactly 3 metrics:

### Metric 1: Market Volume Index
**What:** Total Director/VP+ roles by function (Ops, Finance, GTM, Product, People)  
**Calculation:** Count of open roles with Director/VP/SVP/CXO titles  
**Frequency:** Current count + 2-week change  
**Display:** 
```
Total Director+ Roles: 1,247 (+34 vs 2 weeks ago)
  Operations:  387 (+12)
  GTM/Revenue: 298 (+8)
  Finance:     201 (+5)
  Product:     189 (+7)
  People/HR:   172 (+2)
```

### Metric 2: Stale Search Index
**What:** % of roles open >60 days by function  
**Calculation:** (roles_open_60d / total_roles) * 100  
**Frequency:** Current % + 2-week change  
**Display:**
```
Stale Searches (60+ days open):
  Operations:  23% (+2 pts)
  Finance:     31% (+1 pt)
  GTM/Revenue: 18% (-1 pt)
```

### Metric 3: High-Activity Employers
**What:** Companies with most new Director+ postings in last 2 weeks  
**Calculation:** Count new postings per company, rank top 10  
**Frequency:** Rolling 2-week window  
**Display:**
```
Most Active Hirers (last 2 weeks):
  1. Amazon (23 new Director+ roles)
  2. Coinbase (12 new roles)
  3. UPS (11 new roles)
```

---

## Technical Architecture

### Data Stack
- **Scraping:** Python + Apify actors (Ashby/Greenhouse/Lever)
- **Storage:** Supabase (Postgres)
- **Processing:** Python pandas
- **Scheduling:** GitHub Actions (cron every 2 days)
- **Newsletter:** MailerLite or ConvertKit

### Data Model

```sql
-- Core table
CREATE TABLE job_postings (
  id UUID PRIMARY KEY,
  company_id VARCHAR,
  company_name VARCHAR,
  ats_platform VARCHAR, -- 'ashby' | 'greenhouse' | 'lever'
  source_job_id VARCHAR,
  title_raw VARCHAR,
  title_canonical VARCHAR,
  url TEXT,
  first_seen_date DATE,
  last_seen_date DATE,
  function VARCHAR, -- 'operations' | 'finance' | 'gtm' | 'product' | 'people'
  level VARCHAR, -- 'director' | 'vp' | 'svp' | 'c-level'
  location_raw VARCHAR,
  is_remote BOOLEAN,
  created_at TIMESTAMP
);

-- Company dimension
CREATE TABLE companies (
  id VARCHAR PRIMARY KEY,
  name VARCHAR,
  domain VARCHAR,
  ats_platform VARCHAR,
  ats_url TEXT,
  sector VARCHAR,
  size VARCHAR, -- 'large' | 'growth'
  active BOOLEAN
);

-- Metrics cache (pre-computed)
CREATE TABLE metrics_cache (
  metric_date DATE,
  metric_type VARCHAR, -- 'volume' | 'stale' | 'active_employers'
  metric_data JSONB,
  created_at TIMESTAMP
);
```

### Data Pipeline Flow

```
1. SCRAPE (Daily via GitHub Actions)
   ├─ Apify: Ashby actor → raw JSON
   ├─ Apify: Greenhouse actor → raw JSON  
   └─ Apify: Lever actor → raw JSON

2. NORMALIZE (Python script)
   ├─ Extract: title, company, date, URL
   ├─ Classify: function (keyword matching)
   ├─ Classify: level (title parsing)
   └─ Dedupe: same role seen multiple days

3. STORE (Supabase)
   └─ Upsert to job_postings table

4. COMPUTE METRICS (Every Sunday midnight)
   ├─ Calculate: volume by function
   ├─ Calculate: stale % by function
   ├─ Calculate: top active employers
   └─ Cache to metrics_cache table

5. GENERATE NEWSLETTER (Manual trigger)
   ├─ Pull from metrics_cache
   ├─ Populate markdown template
   └─ Send via MailerLite API
```

---

## Title Classification Logic

### Function Mapping (Keyword-Based)

```python
FUNCTION_KEYWORDS = {
    'operations': ['operations', 'supply chain', 'logistics', 
                   'program manager', 'process', 'ops'],
    'finance': ['finance', 'accounting', 'treasury', 'fp&a', 
                'controller', 'audit'],
    'gtm': ['sales', 'revenue', 'gtm', 'growth', 'business development',
            'account exec', 'partnerships', 'customer success'],
    'product': ['product', 'pm', 'product manager'],
    'people': ['people', 'hr', 'human resources', 'talent', 'recruiting'],
    'engineering': ['engineer', 'software', 'technical', 'infrastructure'],
    'marketing': ['marketing', 'brand', 'communications', 'content'],
}
```

### Level Classification

```python
LEVEL_PATTERNS = {
    'c-level': ['chief', 'ceo', 'cfo', 'coo', 'cto', 'cmo'],
    'svp': ['senior vice president', 'svp', 'sr vp'],
    'vp': ['vice president', 'vp', 'v.p.'],
    'director': ['director', 'dir.', 'head of'],
}
```

---

## Milestone Timeline (4 Weeks)

### Week 1: Foundation
**Days 1-2:** Setup
- Create Supabase project
- Create GitHub repo
- Setup Python environment

**Days 3-5:** Scraping
- Test Apify Ashby actor with 5 companies
- Implement data extraction script
- Store raw JSON locally

**Days 6-7:** Database
- Create schema in Supabase
- Build insert script
- Test with 5 companies' data

### Week 2: Data Pipeline
**Days 8-10:** Normalization
- Build title classifier (function + level)
- Test on 20 sample job titles
- Refine keyword dictionaries

**Days 11-12:** Full Scrape
- Run Apify on all 73 companies
- Debug failures
- Store in Supabase

**Days 13-14:** Deduplication
- Implement dedupe logic (same job, multiple days)
- Calculate first_seen_date and last_seen_date

### Week 3: Metrics + Automation
**Days 15-17:** Metrics Engine
- Build volume calculator
- Build stale % calculator
- Build top employers ranker
- Test against real data

**Days 18-19:** Scheduling
- Setup GitHub Actions workflow
- Test daily scrape
- Test weekly metrics computation

**Days 20-21:** QA + Monitoring
- Check data quality
- Add basic error alerts (email on failure)
- Validate 2 weeks of data collection

### Week 4: Newsletter
**Days 22-24:** Template
- Create markdown newsletter template
- Build facts packet → template script
- Test with real metrics

**Days 25-26:** Delivery
- Setup MailerLite account
- Integrate API
- Send test newsletter to self

**Day 27:** Launch
- Write editorial intro (200 words)
- Generate Issue #1
- Send to initial subscriber list

**Day 28:** Buffer

---

## Newsletter Format (Markdown Template)

```markdown
# Recruiter Market Brief - Issue #[N]
*[Date] | RMI-73 Index*

---

## Market Snapshot

The RMI-73 tracks Director+ hiring activity across 73 leading employers 
spanning tech, finance, healthcare, manufacturing, and 25+ other sectors.

**This Week's Numbers:**
- Total Director+ roles: [X] ([+/- Y] vs 2 weeks ago)
- Operations roles: [X] ([+/- Y])
- Finance roles: [X] ([+/- Y])
- GTM/Revenue roles: [X] ([+/- Y])

---

## Stalled Searches

Roles open 60+ days signal challenging searches or scope issues:

- Operations: [X]% of roles stale ([+/- Y pts])
- Finance: [X]% of roles stale ([+/- Y pts])
- GTM: [X]% of roles stale ([+/- Y pts])

**What this means:** [1-2 sentence interpretation]

---

## High-Activity Employers

Companies posting the most new Director+ roles in the last 2 weeks:

1. [Company A] ([X] new roles)
2. [Company B] ([X] new roles)
3. [Company C] ([X] new roles)
[...top 10]

---

## Methodology

The RMI-73 Index tracks public job postings from 73 companies using 
Ashby, Greenhouse, and Lever ATS platforms. Companies span 28 sectors 
including tech, finance, healthcare, manufacturing, retail, and logistics.

Data collected: [Date range]

---

*Want to discuss these trends? Reply to this email.*
*Unsubscribe: [link]*
```

---

## Quality Gates (Must Pass Before Launch)

### Data Quality
- [ ] 70+ of 73 companies scraping successfully (95%+ coverage)
- [ ] <5% duplicate job postings
- [ ] Title classification accuracy >85% on 50 manual spot checks
- [ ] First_seen_date logic working (no future dates, no nulls)

### Pipeline Reliability
- [ ] GitHub Action runs successfully 3 days in a row
- [ ] Email alert sent on scraper failure
- [ ] Metrics computation completes in <5 minutes

### Newsletter Quality
- [ ] All 3 metrics display real data (no placeholders)
- [ ] Newsletter renders correctly in Gmail, Outlook, Apple Mail
- [ ] Links work
- [ ] Unsubscribe link works

---

## Known Limitations (v1)

**Accepted Tradeoffs:**
- No repost detection (can't tell if same role re-posted)
- No company layoff data integration (future)
- No scope inflation scoring (future)
- Function classification ~85% accurate (keyword-based)
- Only 73 companies (vs 300+ in full market)

**Why These Are OK for v1:**
- Volume trends still valid
- Stale % still meaningful
- 73 companies = credible cross-section
- Can improve accuracy in v2

---

## Success Metrics (First 3 Issues)

### Pipeline Health
- Scraper uptime: >95%
- Data collection lag: <24 hours
- Metrics computation: <5 minutes per run

### Content Quality
- Newsletter production time: <2 hours per issue
- Fact accuracy: 100% (no wrong numbers)
- Typos/errors: 0 per issue

### Subscriber Engagement (if tracking)
- Open rate: >30%
- Reply rate: >2%

---

## Risks & Mitigations

| Risk | Probability | Impact | Mitigation |
|------|-------------|--------|------------|
| Scraper breaks for 10+ companies | Medium | High | Test weekly, have manual backup process |
| Title classification too inaccurate | Low | Medium | Start with broad categories, refine later |
| GitHub Actions flaky | Low | Medium | Add retries, can run manually if needed |
| First dataset incomplete | Medium | Medium | Wait 2 full weeks before first issue |
| Can't hit 4-week timeline | Medium | Low | Cut scope: skip automation, run manually first |

---

## Phase 2 Preview (Not Building Yet)

Future enhancements to consider after 3 successful issues:

1. **Workday Detection:** Add 50-70 major enterprises
2. **Repost Tracking:** Detect when roles are re-posted
3. **Scope Scoring:** Keyword analysis for "scope inflation"
4. **Layoff Integration:** Add layoffs.fyi data
5. **Charts:** Matplotlib trend charts
6. **Editorial UI:** Streamlit dashboard for newsletter assembly

**Decision Point:** Evaluate after Issue #3 based on:
- Production effort per issue
- Subscriber growth
- Data quality issues encountered

---

## Appendix: 73 Companies by Sector

**Tech (7):** Amazon, Intel, ServiceNow, OpenAI, Canva, Lattice, Automation Anywhere

**Fintech (4):** PayPal, Stripe, Brex, Chime, Coinbase

**Banking (4):** Bank of America, Capital One, BMO, Schwab

**Healthcare (4):** HCA Healthcare, Mayo Clinic, Centene, Hims & Hers

**Pharma (3):** Johnson & Johnson, Eli Lilly, Biogen

**Manufacturing (6):** GE, 3M, Caterpillar, Parker Hannifin, Stanley Black & Decker, Corning

**Logistics (3):** UPS, Knight-Swift, Penske

**Construction (3):** D.R. Horton, PulteGroup, Toll Brothers

**HR Tech (3):** ADP, Paycom, Justworks

**Airlines (2):** American Airlines, Delta

**Hospitality (3):** Hyatt, IHG, MGM Resorts

**[Full list available in separate appendix]**

---

## Contact & Approvals

**Product Owner:** Michael McDermott  
**Technical Lead:** Michael McDermott  
**Launch Approval:** Self (founder-led)

**Questions or Concerns:** Ship fast, iterate based on real feedback.

---

**END OF PRD**
