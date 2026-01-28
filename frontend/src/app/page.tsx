export default function Home() {
  return (
    <div className="flex min-h-screen items-center justify-center bg-zinc-50 font-sans dark:bg-black">
      <main className="flex min-h-screen w-full max-w-4xl flex-col gap-10 py-16 px-8 bg-white dark:bg-black">
        <header className="flex flex-col gap-2">
          <h1 className="text-3xl font-semibold tracking-tight text-black dark:text-zinc-50">
            Recruiter Market Brief
          </h1>
          <p className="text-zinc-700 dark:text-zinc-400">
            Phase 1 dashboard showing a snapshot of current hiring demand across
            tracked companies.
          </p>
        </header>

        <section className="grid gap-4 md:grid-cols-3">
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Total Open Roles
            </p>
            <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
              {/* Placeholder until wired to backend */}0
            </p>
            <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              Pulled from Supabase weekly metrics.
            </p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Top Function
            </p>
            <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
              Operations
            </p>
            <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              Based on latest classified postings.
            </p>
          </div>
          <div className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
            <p className="text-xs font-medium uppercase tracking-wide text-zinc-500">
              Last Updated
            </p>
            <p className="mt-2 text-2xl font-semibold text-zinc-900 dark:text-zinc-50">
              —
            </p>
            <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
              Will show the timestamp of the last successful scrape.
            </p>
          </div>
        </section>

        <section className="rounded-xl border border-zinc-200 bg-zinc-50 p-4 dark:border-zinc-800 dark:bg-zinc-900">
          <h2 className="text-sm font-semibold text-zinc-900 dark:text-zinc-50">
            Company Snapshot
          </h2>
          <p className="mt-1 text-xs text-zinc-600 dark:text-zinc-400">
            This table will be populated from the backend API once metrics are
            wired up.
          </p>
          <div className="mt-4 overflow-hidden rounded-lg border border-dashed border-zinc-300 p-8 text-center text-sm text-zinc-500 dark:border-zinc-700 dark:text-zinc-400">
            No data yet. Run the daily scrape and metrics jobs to see your first
            brief.
          </div>
        </section>
      </main>
    </div>
  );
}
