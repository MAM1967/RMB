#!/usr/bin/env python3
"""
Generate a Recruiter Market Brief from current Supabase data.

This script:
  - Connects to Supabase using .env (SUPABASE_URL, SUPABASE_KEY)
  - Pulls all job_postings
  - Filters to senior roles in target functions
  - Computes:
      * Volume by function × level
      * Stale vs fresh (by age in days)
      * Top hiring companies
      * Simple scope / complexity scores from titles
  - Prints a markdown brief to stdout
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone, date
from pathlib import Path
from typing import Any, Iterable

from dotenv import load_dotenv
from supabase import create_client


TARGET_FUNCTIONS = {"gtm", "product", "operations", "finance"}
TARGET_LEVELS = {"manager", "director", "vp", "svp", "c-level"}
STALE_DAYS = 45


@dataclass
class Job:
    company_id: str
    title: str
    function: str | None
    level: str | None
    first_seen: datetime
    # Derived feature scores (computed later)
    strategy_score: int = 0
    execution_score: int = 0
    cross_functional_score: int = 0
    leadership_score: int = 0
    people_mgmt_flag: bool = False


def parse_iso8601(dt: str | None) -> datetime | None:
    if not dt:
        return None
    try:
        # Supabase returns ISO 8601 with timezone; datetime.fromisoformat handles this.
        return datetime.fromisoformat(dt.replace("Z", "+00:00"))
    except Exception:
        return None


def load_jobs() -> list[Job]:
    base_dir = Path(__file__).parent.parent
    load_dotenv(base_dir / ".env", override=True)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_KEY in .env")

    supabase = create_client(url, key)

    result = supabase.table("job_postings").select(
        "company_id,title,function,level,first_seen"
    ).execute()

    jobs: list[Job] = []
    for row in result.data:
        first_seen_dt = parse_iso8601(row.get("first_seen"))
        if not first_seen_dt:
            continue
        jobs.append(
            Job(
                company_id=row.get("company_id", ""),
                title=row.get("title", ""),
                function=row.get("function"),
                level=row.get("level"),
                first_seen=first_seen_dt,
            ),
        )
    return jobs


def filter_target_jobs(jobs: Iterable[Job]) -> list[Job]:
    return [
        j
        for j in jobs
        if j.function in TARGET_FUNCTIONS and j.level in TARGET_LEVELS
    ]


def _clean_title(title: str) -> str:
    if not title:
        return ""
    return "".join(ch if ch.isalnum() or ch.isspace() else " " for ch in title).lower()


def enrich_scope_features(jobs: Iterable[Job]) -> None:
    """
    Very lightweight feature extraction from titles only.
    This is a placeholder for a richer description-based engine.
    """
    # Keyword sets – can be tuned over time.
    strategy_terms = {
        "strategy",
        "strategic",
        "roadmap",
        "portfolio",
        "transformation",
        "vision",
    }
    execution_terms = {
        "execute",
        "execution",
        "deliver",
        "delivery",
        "own",
        "owning",
        "pipeline",
        "quota",
        "okrs",
    }
    cross_func_terms = {
        "cross functional",
        "cross-functional",
        "partner",
        "partnership",
        "collaborate",
        "collaboration",
    }
    leadership_terms = {
        "lead",
        "leader",
        "leadership",
        "head of",
        "director",
        "vp",
        "svp",
        "chief",
    }
    people_mgmt_terms = {
        "manage team",
        "managing team",
        "people manager",
        "people leadership",
        "build a team",
        "grow a team",
    }

    for j in jobs:
        t = _clean_title(j.title)
        if not t:
            continue

        # Simple scoring: count distinct term hits.
        def score(terms: set[str]) -> int:
            return sum(1 for term in terms if term in t)

        j.strategy_score = score(strategy_terms)
        j.execution_score = score(execution_terms)
        j.cross_functional_score = score(cross_func_terms)
        j.leadership_score = score(leadership_terms)
        j.people_mgmt_flag = any(term in t for term in people_mgmt_terms)


def compute_volume(jobs: Iterable[Job]) -> dict[tuple[str, str], int]:
    counter: Counter[tuple[str, str]] = Counter()
    for j in jobs:
        if j.function and j.level:
            counter[(j.function, j.level)] += 1
    return dict(counter)


def compute_staleness(jobs: Iterable[Job]) -> dict[str, dict[str, int]]:
    now = datetime.now(timezone.utc)
    stats: dict[str, dict[str, int]] = defaultdict(lambda: {"stale": 0, "fresh": 0})

    for j in jobs:
        if not j.function:
            continue
        age_days = (now - j.first_seen).days
        bucket = "stale" if age_days >= STALE_DAYS else "fresh"
        stats[j.function][bucket] += 1

    return stats


def load_company_names() -> dict[str, str]:
    base_dir = Path(__file__).parent.parent
    load_dotenv(base_dir / ".env", override=True)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return {}

    supabase = create_client(url, key)
    result = supabase.table("companies").select("id,name").execute()
    return {row["id"]: row.get("name", row["id"]) for row in result.data}


def compute_top_companies(jobs: Iterable[Job], company_names: dict[str, str]) -> dict[str, list[tuple[str, int]]]:
    # per-function company counts
    per_func: dict[str, Counter[str]] = defaultdict(Counter)
    for j in jobs:
        if not j.function:
            continue
        per_func[j.function][j.company_id] += 1

    top: dict[str, list[tuple[str, int]]] = {}
    for func, counter in per_func.items():
        ranked: list[tuple[str, int]] = []
        for company_id, count in counter.most_common(10):
            name = company_names.get(company_id, company_id)
            ranked.append((name, count))
        top[func] = ranked
    return top


@dataclass
class LayoffEvent:
    company_norm: str
    company_name: str
    event_date: date
    employees_affected: int | None
    geography: str | None
    function_tags: list[str]


def load_recent_layoffs(days: int = 60) -> list[LayoffEvent]:
    """
    Load layoff events from the last `days` days, if the table exists / has data.
    This is best-effort; if the table is empty or missing, we simply return [].
    """
    base_dir = Path(__file__).parent.parent
    load_dotenv(base_dir / ".env", override=True)

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    if not url or not key:
        return []

    supabase = create_client(url, key)

    try:
        result = supabase.table("layoff_events").select(
            "company_norm,company_raw,event_date,employees_affected,geography,function_tags"
        ).execute()
    except Exception:
        # Table not present or other error; treat as no layoffs yet.
        return []

    cutoff = datetime.now(timezone.utc).date().toordinal() - days
    events: list[LayoffEvent] = []
    for row in result.data:
        try:
            ev_date = datetime.strptime(row["event_date"], "%Y-%m-%d").date()
        except Exception:
            continue

        if ev_date.toordinal() < cutoff:
            continue

        tags = row.get("function_tags") or []
        if isinstance(tags, str):
            # In case it comes back as a stringified list.
            tags = [t.strip().lower() for t in tags.split(",") if t.strip()]

        events.append(
            LayoffEvent(
                company_norm=row.get("company_norm", ""),
                company_name=row.get("company_raw", row.get("company_norm", "")),
                event_date=ev_date,
                employees_affected=row.get("employees_affected"),
                geography=row.get("geography"),
                function_tags=tags,
            )
        )

    return events


def render_brief(
    jobs: list[Job],
    volume: dict[tuple[str, str], int],
    staleness: dict[str, dict[str, int]],
    top_companies: dict[str, list[tuple[str, int]]],
    layoffs: list[LayoffEvent] | None = None,
) -> str:
    total_roles = len(jobs)
    functions_present = sorted({j.function for j in jobs if j.function})

    lines: list[str] = []
    lines.append("## Recruiter Market Brief – Snapshot\n")

    # TL;DR
    lines.append("### TL;DR")
    lines.append(
        f"- **Scope**: {total_roles} senior roles across {len(functions_present)} functions "
        f"({', '.join(functions_present)})"
    )
    # Simple stale ratio overall
    total_stale = sum(f["stale"] for f in staleness.values())
    stale_pct = (total_stale / total_roles * 100) if total_roles else 0.0
    lines.append(f"- **Staleness**: ~**{stale_pct:.0f}%** of senior roles are older than {STALE_DAYS} days")
    lines.append("")

    # Volume by function × level
    lines.append("### Volume by Function × Level")
    lines.append("")
    lines.append("| Function | Level | Roles |")
    lines.append("|----------|-------|-------|")
    for func in sorted(TARGET_FUNCTIONS):
        for level in ["c-level", "svp", "vp", "director", "manager"]:
            count = volume.get((func, level), 0)
            if count == 0:
                continue
            lines.append(f"| {func} | {level} | {count} |")
    lines.append("")

    # Staleness by function
    lines.append("### Staleness by Function")
    lines.append("")
    lines.append(f"Roles are considered **stale** if first seen ≥ {STALE_DAYS} days ago.")
    lines.append("")
    lines.append("| Function | Fresh | Stale | Stale % |")
    lines.append("|----------|-------|-------|---------|")
    for func in sorted(TARGET_FUNCTIONS):
        stats = staleness.get(func, {"fresh": 0, "stale": 0})
        fresh = stats["fresh"]
        stale = stats["stale"]
        total = fresh + stale
        pct = (stale / total * 100) if total else 0.0
        lines.append(f"| {func} | {fresh} | {stale} | {pct:.0f}% |")
    lines.append("")

    # Top hiring companies per function
    lines.append("### Where Hiring Is Hottest")
    lines.append("")
    for func in sorted(TARGET_FUNCTIONS):
        companies = top_companies.get(func, [])
        if not companies:
            continue
        lines.append(f"#### {func.capitalize()}")
        for name, count in companies[:10]:
            lines.append(f"- **{name}** – {count} senior {func} roles")
        lines.append("")

    # Section: Why searches stall (complex / high-scope roles)
    lines.append("### Why Searches Stall")
    lines.append("")

    # Section: Market Reset / New Talent Supply (layoffs)
    layoffs = layoffs or []
    lines.append("### Market Reset / New Talent Supply")
    lines.append("")
    if not layoffs:
        lines.append(
            "_No recent layoff events ingested yet. Add layoff_events via "
            "`scripts/ingest_layoffs.py` to populate this section._"
        )
    else:
        # Aggregate by company, sum employees_affected
        by_company: dict[str, dict[str, Any]] = {}
        for ev in layoffs:
            key = ev.company_norm
            bucket = by_company.setdefault(
                key,
                {
                    "name": ev.company_name,
                    "employees": 0,
                    "events": 0,
                    "latest": ev.event_date,
                    "functions": set(),
                },
            )
            bucket["events"] += 1
            if ev.employees_affected:
                bucket["employees"] += ev.employees_affected
            if ev.event_date > bucket["latest"]:
                bucket["latest"] = ev.event_date
            for tag in ev.function_tags:
                bucket["functions"].add(tag)

        # Rank by employees affected desc
        ranked = sorted(
            by_company.values(),
            key=lambda b: b["employees"],
            reverse=True,
        )[:10]

        lines.append(
            "Recent layoff events that may have released senior talent "
            "in relevant functions (coarse, aggregated view):"
        )
        lines.append("")
        lines.append("| Company | Approx. affected | Events | Functions (coarse) | Latest event |")
        lines.append("|---------|------------------|--------|---------------------|--------------|")
        for b in ranked:
            funcs = ", ".join(sorted(b["functions"])) or "-"
            latest = b["latest"].isoformat()
            lines.append(
                f"| {b['name']} | {b['employees'] or '-'} | {b['events']} | {funcs} | {latest} |"
            )
    lines.append("")
    lines.append(
        "Below are high-scope senior roles based on title language "
        "(strategy, execution, cross-functional work, leadership). "
        "These often correlate with slower, more fragile searches."
    )
    lines.append("")

    # Compute a crude "scope inflation" index from the in-memory features.
    def scope_score(j: Job) -> int:
        return (
            j.strategy_score
            + j.execution_score
            + j.cross_functional_score
            + j.leadership_score
            + (1 if j.people_mgmt_flag else 0)
        )

    scored = [(j, scope_score(j)) for j in jobs if scope_score(j) > 0]
    # Sort by score desc, then by title
    scored.sort(key=lambda pair: (-pair[1], pair[0].title))

    if not scored:
        lines.append("_No complex senior roles detected yet – dataset is still small._")
    else:
        lines.append("| Title | Function | Level | Scope index |")
        lines.append("|-------|----------|-------|-------------|")
        for j, s in scored[:15]:
            func = j.function or "-"
            level = j.level or "-"
            lines.append(f"| {j.title} | {func} | {level} | {s} |")
    lines.append("")

    return "\n".join(lines)


def main() -> None:
    jobs_all = load_jobs()
    target_jobs = filter_target_jobs(jobs_all)

    # Enrich with simple scope features from titles.
    enrich_scope_features(target_jobs)

    volume = compute_volume(target_jobs)
    staleness = compute_staleness(target_jobs)
    company_names = load_company_names()
    top_companies = compute_top_companies(target_jobs, company_names)

    layoffs = load_recent_layoffs(days=60)

    brief_md = render_brief(target_jobs, volume, staleness, top_companies, layoffs)
    print(brief_md)

    # Also persist the brief and a simple "facts packet" for downstream use.
    base_dir = Path(__file__).parent.parent
    briefs_dir = base_dir / "briefs"
    facts_dir = base_dir / "facts"
    briefs_dir.mkdir(exist_ok=True)
    facts_dir.mkdir(exist_ok=True)

    today = datetime.now(timezone.utc).date()
    date_str = today.strftime("%Y%m%d")

    # Save brief markdown file.
    brief_path = briefs_dir / f"brief_{date_str}.md"
    try:
        brief_path.write_text(brief_md, encoding="utf-8")
    except OSError:
        # Non-fatal; continue even if we can't write the brief to disk.
        pass

    # Build a lightweight facts packet.
    functions_present = sorted({j.function for j in target_jobs if j.function})
    total_roles = len(target_jobs)
    total_stale = sum(f["stale"] for f in staleness.values())
    stale_pct = (total_stale / total_roles * 100) if total_roles else 0.0

    volume_serializable = {
        f"{func}|{level}": count for (func, level), count in volume.items()
    }

    facts: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total_roles": total_roles,
        "functions": functions_present,
        "stale_pct": stale_pct,
        "volume_by_function_level": volume_serializable,
        "staleness_by_function": staleness,
        "top_companies": top_companies,
        "layoff_events_count": len(layoffs),
        "layoff_companies_count": len({ev.company_norm for ev in layoffs}),
    }

    facts_path = facts_dir / f"facts_{date_str}.json"
    try:
        facts_path.write_text(json.dumps(facts, indent=2, default=str), encoding="utf-8")
    except OSError:
        # Non-fatal; continue even if we can't write the facts packet.
        pass


if __name__ == "__main__":
    main()

