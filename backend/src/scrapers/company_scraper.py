 """
 Company scraping entrypoints using Apify.

 This module is intentionally minimal for Phase 1 and will be
 expanded as we add more ATS-specific logic.
 """

 from __future__ import annotations

 from concurrent.futures import ThreadPoolExecutor
 from typing import Iterable, Sequence

 from apify_client import ApifyClient
 from tenacity import retry, stop_after_attempt, wait_exponential

 from backend.src.config.settings import Settings, get_settings
 from backend.src.logging_config import get_logger

 logger = get_logger()


 @retry(wait=wait_exponential(multiplier=1, min=1, max=10), stop=stop_after_attempt(3))
 def _run_apify_actor(client: ApifyClient, actor_id: str, run_input: dict) -> dict:
    """Run a single Apify actor with retries."""
    run = client.actor(actor_id).call(run_input=run_input)
    return run  # type: ignore[no-any-return]


 def scrape_company(company_id: str, settings: Settings | None = None) -> None:
    """
    Scrape a single company using Apify.

    Currently a stub that logs start/end and calls a placeholder actor.
    """

    cfg = settings or get_settings()
    client = ApifyClient(cfg.apify.token)

    logger.info("scrape_started", company_id=company_id)
    # TODO: replace \"example-actor\" with real actor and inputs.
    _run_apify_actor(
        client,
        actor_id="example-actor",
        run_input={"company_id": company_id},
    )
    logger.info("scrape_completed", company_id=company_id)


 def scrape_companies(
    company_ids: Sequence[str],
    max_workers: int = 5,
    settings: Settings | None = None,
) -> None:
    """
    Scrape multiple companies with limited parallelism.

    This follows the guideline of max 5 concurrent workers.
    """

    cfg = settings or get_settings()
    effective_workers = min(max_workers, 5, len(company_ids) or 1)

    def _task(cid: str) -> None:
        scrape_company(cid, cfg)

    with ThreadPoolExecutor(max_workers=effective_workers) as executor:
        list(executor.map(_task, company_ids))

