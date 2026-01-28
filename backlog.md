# Recruiter Market Brief - Product Backlog

**Last Updated:** 2026-01-28  
**Current Phase:** Phase 1 MVP  
**Target Ship Date:** 4 weeks from kickoff

---

## Backlog Status Legend

- 🔴 **Not Started** - Not yet begun
- 🟡 **In Progress** - Currently being worked on
- 🟢 **Done** - Completed and verified
- ⏸️ **Blocked** - Waiting on dependencies
- 📋 **Backlog** - Future work (Phase 2+)

---

## Phase 1: MVP (Weeks 1-4)

### Epic 1: Foundation & Infrastructure Setup

#### Story 1.1: Project Setup & Repository
**Status:** 🟢 Done  
**Priority:** P0 (Critical)  
**Sprint:** Week 1, Days 1-2

**Description:**  
Set up the foundational infrastructure including GitHub repo, Supabase project, Python environment, and project structure.

**Acceptance Criteria:**
- [x] GitHub repository created and initialized
- [x] Supabase project created (or schema ready to apply)
- [x] Python 3.11+ environment configured
- [x] Project structure established (backend, frontend, database, config, scripts, tests)
- [x] Basic CI/CD workflows configured
- [x] Environment variable management (.env.example)

**Notes:**  
✅ Completed in initial setup

---

#### Story 1.2: Database Schema Implementation
**Status:** 🟢 Done  
**Priority:** P0 (Critical)  
**Sprint:** Week 1, Days 6-7

**Description:**  
Create the database schema in Supabase with tables for companies, job_postings, and metrics_cache.

**Acceptance Criteria:**
- [x] `companies` table created with required fields (id, name, ats_platform, sector, size)
- [x] `job_postings` table created with all required fields (source_job_id, company_id, title, function, level, dates, etc.)
- [x] `weekly_metrics` table created for pre-computed metrics
- [x] Proper indexes created on foreign keys and frequently queried columns
- [x] Unique constraints on (source_job_id, company_id) for job_postings
- [x] Migration files created and documented
- [ ] Schema applied to Supabase production instance

**Notes:**  
✅ Schema SQL files created, ready to apply to Supabase

---

### Epic 2: Data Scraping Pipeline

#### Story 2.1: Apify Scraper Integration - Ashby
**Status:** 🟡 In Progress  
**Priority:** P0 (Critical)  
**Sprint:** Week 1, Days 3-5

**Description:**  
Integrate Apify Ashby actor to scrape job postings from Ashby-powered company careers pages. Test with 5 companies initially.

**Acceptance Criteria:**
- [ ] Apify client configured with authentication
- [ ] Test Apify Ashby actor with 5 sample companies
- [ ] Extract raw JSON data (title, company, URL, date, etc.)
- [ ] Handle rate limiting (max 5 concurrent requests)
- [ ] Store raw JSON locally for testing
- [ ] Error handling for failed scrapes
- [ ] Logging for scrape operations

**Dependencies:**  
- Apify account and token
- List of 5 test companies using Ashby

---

#### Story 2.2: Apify Scraper Integration - Greenhouse
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 1, Days 3-5

**Description:**  
Integrate Apify Greenhouse actor to scrape job postings from Greenhouse-powered company careers pages.

**Acceptance Criteria:**
- [ ] Apify Greenhouse actor configured
- [ ] Test with 2-3 Greenhouse companies
- [ ] Extract raw JSON data matching Ashby format
- [ ] Handle rate limiting
- [ ] Error handling and logging

**Dependencies:**  
- Story 2.1 (Ashby) as reference implementation
- List of Greenhouse companies

---

#### Story 2.3: Apify Scraper Integration - Lever
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 1, Days 3-5

**Description:**  
Integrate Apify Lever actor to scrape job postings from Lever-powered company careers pages.

**Acceptance Criteria:**
- [ ] Apify Lever actor configured
- [ ] Test with 1-2 Lever companies
- [ ] Extract raw JSON data matching format
- [ ] Handle rate limiting
- [ ] Error handling and logging

**Dependencies:**  
- Story 2.1 (Ashby) as reference implementation
- List of Lever companies

---

#### Story 2.4: Full Scrape - All 73 Companies
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 2, Days 11-12

**Description:**  
Run the scraping pipeline on all 73 companies in the RMI-73 index. Debug failures and ensure >95% success rate.

**Acceptance Criteria:**
- [ ] Scrape all 67 Ashby companies
- [ ] Scrape all 4 Greenhouse companies
- [ ] Scrape all 2 Lever companies
- [ ] Success rate >95% (70+ companies)
- [ ] Failed companies logged with error details
- [ ] All successful scrapes stored in Supabase
- [ ] Manual review of failures and retry logic

**Dependencies:**  
- Stories 2.1, 2.2, 2.3 completed
- Database schema applied
- Complete companies.json with all 73 companies

---

### Epic 3: Data Normalization & Classification

#### Story 3.1: Title Classification - Function
**Status:** 🟡 In Progress  
**Priority:** P0 (Critical)  
**Sprint:** Week 2, Days 8-10

**Description:**  
Build a keyword-based classifier to assign job functions (operations, finance, gtm, product, people, engineering, marketing) to job titles.

**Acceptance Criteria:**
- [ ] Keyword dictionary for each function category
- [ ] Classification function implemented (classify_job_function)
- [ ] Test on 20+ sample job titles
- [ ] Accuracy >85% on manual spot checks
- [ ] Handle edge cases (ambiguous titles, multiple keywords)
- [ ] Unit tests with >80% coverage

**Dependencies:**  
- Sample job titles from scraped data
- Keyword taxonomy defined

**Notes:**  
✅ Basic implementation exists, needs expansion and testing

---

#### Story 3.2: Title Classification - Level
**Status:** 🟡 In Progress  
**Priority:** P0 (Critical)  
**Sprint:** Week 2, Days 8-10

**Description:**  
Build a pattern-based classifier to assign seniority levels (director, vp, svp, c-level) to job titles.

**Acceptance Criteria:**
- [ ] Level patterns defined (director, vp, svp, c-level)
- [ ] Classification function implemented (classify_job_level)
- [ ] Test on 20+ sample job titles
- [ ] Accuracy >85% on manual spot checks
- [ ] Handle variations (VP vs Vice President, Dir. vs Director)
- [ ] Unit tests with >80% coverage

**Dependencies:**  
- Sample job titles from scraped data

**Notes:**  
✅ Basic implementation exists, needs expansion and testing

---

#### Story 3.3: Data Deduplication Logic
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 2, Days 13-14

**Description:**  
Implement deduplication logic to handle the same job posting seen across multiple scrape days. Calculate first_seen_date and last_seen_date.

**Acceptance Criteria:**
- [ ] Dedupe logic based on (source_job_id, company_id) unique constraint
- [ ] Upsert pattern implemented (ON CONFLICT)
- [ ] first_seen_date set on first observation
- [ ] last_seen_date updated on subsequent observations
- [ ] Handle edge cases (same job, different URLs)
- [ ] <5% duplicate rate in final dataset
- [ ] Integration tests with sample data

**Dependencies:**  
- Database schema with unique constraint
- Multiple days of scrape data

---

#### Story 3.4: Data Storage Pipeline
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 2, Days 11-12

**Description:**  
Build the script that normalizes scraped data, applies classification, and stores results in Supabase job_postings table.

**Acceptance Criteria:**
- [ ] Normalize raw JSON from all 3 ATS platforms
- [ ] Apply function and level classification
- [ ] Batch upsert to Supabase (100 rows at a time)
- [ ] Handle connection pooling
- [ ] Error handling and retry logic
- [ ] Logging for each step
- [ ] Test with 5 companies' data end-to-end

**Dependencies:**  
- Stories 3.1, 3.2 (classification)
- Database schema applied
- Supabase client configured

---

### Epic 4: Metrics Computation

#### Story 4.1: Market Volume Index Calculator
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 3, Days 15-17

**Description:**  
Calculate Metric 1: Total Director/VP+ roles by function, with 2-week change comparison.

**Acceptance Criteria:**
- [ ] Query job_postings for Director+ roles (director, vp, svp, c-level)
- [ ] Group by function (operations, finance, gtm, product, people)
- [ ] Calculate current count
- [ ] Calculate count from 2 weeks ago
- [ ] Compute change (+/-)
- [ ] Format output matching newsletter spec
- [ ] Unit tests with sample data
- [ ] Performance: completes in <30 seconds

**Dependencies:**  
- At least 2 weeks of historical data
- Classification working correctly

---

#### Story 4.2: Stale Search Index Calculator
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 3, Days 15-17

**Description:**  
Calculate Metric 2: Percentage of roles open >60 days by function, with 2-week change.

**Acceptance Criteria:**
- [ ] Query roles where (current_date - first_seen_date) > 60 days
- [ ] Group by function
- [ ] Calculate % stale = (stale_roles / total_roles) * 100
- [ ] Calculate % from 2 weeks ago
- [ ] Compute change (+/- percentage points)
- [ ] Format output matching newsletter spec
- [ ] Unit tests with sample data
- [ ] Handle edge cases (no roles, all stale, etc.)

**Dependencies:**  
- At least 60 days of historical data
- first_seen_date logic working

---

#### Story 4.3: High-Activity Employers Calculator
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 3, Days 15-17

**Description:**  
Calculate Metric 3: Companies with most new Director+ postings in last 2 weeks, ranked top 10.

**Acceptance Criteria:**
- [ ] Query new postings in last 14 days (first_seen_date within window)
- [ ] Filter to Director+ level only
- [ ] Count per company
- [ ] Rank top 10 companies
- [ ] Format output matching newsletter spec
- [ ] Handle ties (alphabetical)
- [ ] Unit tests with sample data

**Dependencies:**  
- At least 2 weeks of historical data
- Company dimension table populated

---

#### Story 4.4: Metrics Cache & Storage
**Status:** 🔴 Not Started  
**Priority:** P1 (High)  
**Sprint:** Week 3, Days 15-17

**Description:**  
Store computed metrics in weekly_metrics table for fast newsletter generation and historical tracking.

**Acceptance Criteria:**
- [ ] Store volume metrics by (week_start_date, company_id, function, level)
- [ ] Store stale % metrics by (week_start_date, function)
- [ ] Store top employers by (week_start_date)
- [ ] Unique constraint prevents duplicates
- [ ] Query function to retrieve latest metrics
- [ ] Integration tests

**Dependencies:**  
- Stories 4.1, 4.2, 4.3 (calculators)
- weekly_metrics table schema

---

### Epic 5: Automation & Scheduling

#### Story 5.1: Daily Scrape GitHub Action
**Status:** 🟢 Done  
**Priority:** P0 (Critical)  
**Sprint:** Week 3, Days 18-19

**Description:**  
Set up GitHub Actions workflow to run daily scrape automatically every 2 days (or daily).

**Acceptance Criteria:**
- [x] GitHub Actions workflow file created
- [x] Scheduled cron job (every 2 days or daily)
- [x] Manual trigger option (workflow_dispatch)
- [x] Environment variables from GitHub Secrets
- [x] Install dependencies
- [x] Run scrape script
- [x] Error handling and notifications
- [ ] Test successful run in production
- [ ] Slack/email alert on failure

**Notes:**  
✅ Workflow created, needs secrets configured and tested

---

#### Story 5.2: Weekly Metrics GitHub Action
**Status:** 🟢 Done  
**Priority:** P0 (Critical)  
**Sprint:** Week 3, Days 18-19

**Description:**  
Set up GitHub Actions workflow to compute weekly metrics every Sunday at midnight UTC.

**Acceptance Criteria:**
- [x] GitHub Actions workflow file created
- [x] Scheduled cron job (Sunday 00:00 UTC)
- [x] Manual trigger option
- [x] Environment variables from GitHub Secrets
- [x] Install dependencies
- [x] Run metrics computation script
- [x] Error handling
- [ ] Test successful run in production
- [ ] Completion time <5 minutes

**Notes:**  
✅ Workflow created, needs secrets configured and tested

---

#### Story 5.3: Error Monitoring & Alerts
**Status:** 🔴 Not Started  
**Priority:** P1 (High)  
**Sprint:** Week 3, Days 20-21

**Description:**  
Set up basic error monitoring and alerting for pipeline failures.

**Acceptance Criteria:**
- [ ] Slack webhook integration in GitHub Actions
- [ ] Email alert on scraper failure
- [ ] Alert includes: failed companies, error messages, timestamp
- [ ] Test alert delivery
- [ ] Document alert setup

**Dependencies:**  
- Slack webhook URL or email service
- GitHub Secrets configured

---

### Epic 6: Newsletter Generation

#### Story 6.1: Newsletter Markdown Template
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 4, Days 22-24

**Description:**  
Create the markdown newsletter template matching the PRD format with placeholders for metrics.

**Acceptance Criteria:**
- [ ] Template file created (newsletter_template.md)
- [ ] Includes all sections: Market Snapshot, Stale Searches, High-Activity Employers, Methodology
- [ ] Placeholders for all 3 metrics
- [ ] Date formatting
- [ ] Issue number placeholder
- [ ] Unsubscribe link placeholder
- [ ] Professional formatting

**Dependencies:**  
- PRD newsletter format specification

---

#### Story 6.2: Newsletter Generation Script
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 4, Days 22-24

**Description:**  
Build script that pulls metrics from cache, populates template, and generates final markdown newsletter.

**Acceptance Criteria:**
- [ ] Load latest metrics from weekly_metrics table
- [ ] Format metrics according to template spec
- [ ] Populate template with real data
- [ ] Generate markdown file
- [ ] Handle missing data gracefully
- [ ] Test with real metrics data
- [ ] Output matches newsletter format exactly

**Dependencies:**  
- Story 6.1 (template)
- Stories 4.1, 4.2, 4.3 (metrics calculators)
- Story 4.4 (metrics cache)

---

#### Story 6.3: MailerLite/ConvertKit Integration
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 4, Days 25-26

**Description:**  
Integrate with MailerLite or ConvertKit API to send newsletter emails to subscribers.

**Acceptance Criteria:**
- [ ] MailerLite or ConvertKit account setup
- [ ] API client configured
- [ ] Convert markdown to HTML (or use markdown support)
- [ ] Send test newsletter to self
- [ ] Send to subscriber list
- [ ] Handle API errors
- [ ] Unsubscribe link working
- [ ] Test email rendering in Gmail, Outlook, Apple Mail

**Dependencies:**  
- Story 6.2 (generation script)
- Email service account

---

#### Story 6.4: First Newsletter Issue
**Status:** 🔴 Not Started  
**Priority:** P0 (Critical)  
**Sprint:** Week 4, Day 27

**Description:**  
Generate and send Issue #1 of the Recruiter Market Brief newsletter.

**Acceptance Criteria:**
- [ ] Write editorial intro (200 words)
- [ ] Generate Issue #1 with real data
- [ ] Review for accuracy (all numbers correct)
- [ ] Review for typos/errors (0 errors)
- [ ] Send to initial subscriber list
- [ ] Verify delivery
- [ ] Document production time (<2 hours)

**Dependencies:**  
- Story 6.3 (email integration)
- At least 2 weeks of data collection
- Initial subscriber list

---

### Epic 7: Quality Assurance & Monitoring

#### Story 7.1: Data Quality Validation
**Status:** 🔴 Not Started  
**Priority:** P1 (High)  
**Sprint:** Week 3, Days 20-21

**Description:**  
Implement data quality checks to ensure pipeline reliability.

**Acceptance Criteria:**
- [ ] Scraper success rate >95% (70+ of 73 companies)
- [ ] Duplicate rate <5%
- [ ] Title classification accuracy >85% (manual spot check 50 jobs)
- [ ] No future dates in first_seen_date
- [ ] No nulls in required fields
- [ ] Validation script with clear error reporting
- [ ] Run validation before each newsletter generation

**Dependencies:**  
- At least 2 weeks of data
- Classification logic complete

---

#### Story 7.2: Pipeline Health Monitoring
**Status:** 🔴 Not Started  
**Priority:** P1 (High)  
**Sprint:** Week 3, Days 20-21

**Description:**  
Monitor pipeline health and track key metrics.

**Acceptance Criteria:**
- [ ] Track scraper uptime (target >95%)
- [ ] Track data collection lag (target <24 hours)
- [ ] Track metrics computation time (target <5 minutes)
- [ ] Log all pipeline runs with timestamps
- [ ] Basic dashboard or log aggregation
- [ ] Alert on degradation

**Dependencies:**  
- GitHub Actions workflows running
- Logging infrastructure

---

## Phase 2: Future Enhancements (Backlog)

### Epic 8: Expanded Data Sources

#### Story 8.1: Workday Platform Support
**Status:** 📋 Backlog  
**Priority:** P2 (Medium)  
**Sprint:** Future

**Description:**  
Add support for scraping Workday-powered company careers pages, expanding index by 50-70 major enterprises.

**Acceptance Criteria:**
- [ ] Apify Workday actor identified or custom scraper built
- [ ] Test with 5 Workday companies
- [ ] Integrate into existing pipeline
- [ ] Update RMI index documentation
- [ ] Maintain >95% success rate

---

#### Story 8.2: Repost Detection
**Status:** 📋 Backlog  
**Priority:** P2 (Medium)  
**Sprint:** Future

**Description:**  
Detect when the same role is re-posted (different job ID but same title/company) to improve stale search accuracy.

**Acceptance Criteria:**
- [ ] Algorithm to detect reposts (title + company + level matching)
- [ ] Track repost history
- [ ] Update stale search calculation
- [ ] Test accuracy

---

#### Story 8.3: Layoff Data Integration
**Status:** 📋 Backlog  
**Priority:** P3 (Low)  
**Sprint:** Future

**Description:**  
Integrate layoffs.fyi or similar data source to correlate hiring activity with layoff announcements.

**Acceptance Criteria:**
- [ ] Identify layoff data source API
- [ ] Integrate layoff data into database
- [ ] Add layoff context to newsletter
- [ ] Test data quality

---

### Epic 9: Advanced Analytics

#### Story 9.1: Scope Inflation Scoring
**Status:** 📋 Backlog  
**Priority:** P2 (Medium)  
**Sprint:** Future

**Description:**  
Analyze job descriptions for keywords indicating "scope inflation" (e.g., "wear many hats", "do everything").

**Acceptance Criteria:**
- [ ] Keyword dictionary for scope inflation signals
- [ ] Scoring algorithm
- [ ] Add to newsletter as optional metric
- [ ] Validate accuracy

---

#### Story 9.2: Trend Charts Generation
**Status:** 📋 Backlog  
**Priority:** P2 (Medium)  
**Sprint:** Future

**Description:**  
Generate matplotlib charts showing trends over time (volume by function, stale % trends, etc.).

**Acceptance Criteria:**
- [ ] Matplotlib integration
- [ ] Generate volume trend chart
- [ ] Generate stale % trend chart
- [ ] Embed charts in newsletter
- [ ] Test rendering in email clients

---

### Epic 10: Editorial Tools

#### Story 10.1: Newsletter Assembly Dashboard
**Status:** 📋 Backlog  
**Priority:** P2 (Medium)  
**Sprint:** Future

**Description:**  
Build Streamlit or web dashboard for assembling newsletters with live preview and editing.

**Acceptance Criteria:**
- [ ] Streamlit app or web UI
- [ ] Load latest metrics
- [ ] Preview newsletter
- [ ] Edit editorial content
- [ ] Generate and send from UI
- [ ] Reduce production time to <1 hour

---

## Quality Gates Checklist

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

## Notes

- **Priority Levels:**
  - P0 (Critical): Must have for MVP launch
  - P1 (High): Important for quality/reliability
  - P2 (Medium): Nice to have, Phase 2 candidates
  - P3 (Low): Future consideration

- **Status Updates:**  
  Update this backlog as work progresses. Move stories from "Not Started" → "In Progress" → "Done" as they're completed.

- **Dependencies:**  
  Pay attention to story dependencies. Some stories cannot start until prerequisites are complete.

- **Timeline:**  
  Phase 1 MVP target: 4 weeks from kickoff. Adjust sprint assignments as needed based on velocity.
