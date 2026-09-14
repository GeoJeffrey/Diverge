export function LoadingState({ label = "Loading…" }: { label?: string }) {
  return (
    <div className="px-7 py-10" role="status" aria-live="polite">
      <div className="h-6 w-40 animate-pulse rounded bg-[#e0dbd4]" />
      <div className="mt-4 grid gap-4 md:grid-cols-2">
        <div className="h-32 animate-pulse rounded-xl bg-[#e0dbd4]" />
        <div className="h-32 animate-pulse rounded-xl bg-[#e0dbd4]" />
      </div>
      <p className="mt-4 text-sm text-[#7a5040]">{label}</p>
    </div>
  );
}

export function ErrorState({ message, onRetry }: { message: string; onRetry?: () => void }) {
  return (
    <div className="m-7 rounded-xl border border-[#e8cfc3] bg-[#faf3ef] p-6" role="alert">
      <p className="font-semibold text-ink">Couldn’t load this view</p>
      <p className="mt-1 text-sm text-[#5c4a3c]">{message}</p>
      {onRetry && (
        <button
          type="button"
          onClick={onRetry}
          className="mt-4 rounded-lg bg-ink px-4 py-2 text-sm font-semibold text-white"
        >
          Try again
        </button>
      )}
    </div>
  );
}

export function EmptyState({ title, body }: { title: string; body: string }) {
  return (
    <div className="rounded-xl border border-[#e7e1d8] bg-white p-6">
      <p className="font-semibold text-ink">{title}</p>
      <p className="mt-1 text-sm text-[#666]">{body}</p>
    </div>
  );
}
