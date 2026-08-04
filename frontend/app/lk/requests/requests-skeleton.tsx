export function RequestsSkeleton() {
  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center justify-between gap-4 mb-6">
        <div className="space-y-2">
          <div className="h-6 w-40 bg-[var(--fill-2)] rounded animate-pulse" />
          <div className="h-4 w-56 bg-[var(--fill-2)] rounded animate-pulse" />
        </div>
        <div className="h-10 w-32 bg-[var(--fill-2)] rounded animate-pulse" />
      </div>
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
        {Array.from({ length: 4 }).map((_, i) => (
          <div key={i} className="surface-card px-4 py-3.5 space-y-2">
            <div className="h-3 w-16 bg-[var(--fill-2)] rounded animate-pulse" />
            <div className="h-8 w-8 bg-[var(--fill-2)] rounded animate-pulse" />
          </div>
        ))}
      </div>
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="surface-card h-64 bg-[var(--fill-2)] rounded animate-pulse" />
        <div className="surface-card h-64 bg-[var(--fill-2)] rounded animate-pulse" />
      </div>
      <div className="space-y-3">
        {Array.from({ length: 3 }).map((_, i) => (
          <div key={i} className="surface-card p-5 space-y-2">
            <div className="h-4 w-32 bg-[var(--fill-2)] rounded animate-pulse" />
            <div className="h-3 w-full bg-[var(--fill-2)] rounded animate-pulse" />
          </div>
        ))}
      </div>
    </div>
  );
}
