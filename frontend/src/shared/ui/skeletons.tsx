export function CatalogoSkeleton() {
  return (
    <div className="mt-4 grid grid-cols-2 gap-3 sm:gap-4 md:gap-8 lg:grid-cols-3 xl:grid-cols-4">
      {Array.from({ length: 8 }).map((_, i) => (
        <div
          key={i}
          className="animate-pulse overflow-hidden rounded-xl border border-slate-200 bg-white md:rounded-2xl"
        >
          <div className="aspect-square bg-slate-200 md:aspect-[4/5]" />
          <div className="space-y-2 p-3 md:p-4">
            <div className="h-3 w-[85%] rounded bg-slate-200 md:h-4" />
            <div className="h-3 w-[55%] rounded bg-slate-200 md:h-4" />
            <div className="h-8 w-full rounded bg-slate-200 md:h-9" />
          </div>
        </div>
      ))}
    </div>
  );
}

export function PedidoSkeleton() {
  return (
    <div className="mt-6 space-y-3 animate-pulse">
      <div className="h-5 w-48 rounded bg-slate-200" />
      <div className="h-4 w-full max-w-md rounded bg-slate-200" />
      <div className="h-40 w-full max-w-lg rounded border border-slate-200 bg-slate-100" />
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="animate-pulse flex flex-col md:overflow-hidden rounded-xl bg-white md:border md:border-slate-200 md:shadow-sm">
      <div className="hidden md:block aspect-square w-full bg-slate-200" />
      <div className="flex p-3 md:p-4 gap-3 md:block md:gap-0">
        <div className="md:hidden h-20 w-20 shrink-0 rounded-lg bg-slate-200" />
        <div className="flex-1 space-y-2 md:space-y-3 md:mt-0">
          <div className="h-4 w-[85%] rounded bg-slate-200" />
          <div className="h-3 w-[55%] rounded bg-slate-200" />
          <div className="hidden md:block mt-2 h-9 w-full rounded bg-slate-200" />
        </div>
      </div>
    </div>
  );
}

export function SkeletonTable() {
  return (
    <div className="animate-pulse space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <div className="h-6 w-full max-w-[200px] rounded bg-slate-200 mb-6" />
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} className="h-12 w-full rounded bg-slate-100" />
      ))}
    </div>
  );
}

export function SkeletonPedidoDetalle() {
  return (
    <div className="animate-pulse grid grid-cols-1 md:grid-cols-3 gap-6">
      <div className="md:col-span-2 space-y-4">
        <div className="h-24 w-full rounded-xl bg-slate-100" />
        <div className="h-64 w-full rounded-xl bg-slate-200" />
      </div>
      <div className="space-y-4">
        <div className="h-40 w-full rounded-xl bg-slate-100" />
        <div className="h-48 w-full rounded-xl bg-slate-100" />
      </div>
    </div>
  );
}
