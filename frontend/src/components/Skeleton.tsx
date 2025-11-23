export function Skeleton({ className = "" }: { className?: string }) {
  return (
    <div className={`animate-pulse bg-gray-200 rounded ${className}`} />
  );
}

export function MarketCardSkeleton() {
  return (
    <div className="bg-white rounded-lg shadow-md p-4">
      <div className="flex items-start justify-between gap-4">
        <div className="flex-1">
          <Skeleton className="h-5 w-3/4 mb-3" />
          <div className="flex items-center gap-4">
            <Skeleton className="h-4 w-16" />
            <Skeleton className="h-4 w-20" />
            <Skeleton className="h-4 w-24" />
          </div>
        </div>
        <div className="text-right">
          <Skeleton className="h-8 w-12 mb-1" />
          <Skeleton className="h-3 w-8" />
        </div>
      </div>
    </div>
  );
}

export function ResultSkeleton() {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="grid grid-cols-2 gap-6 mb-6">
          <Skeleton className="h-24 rounded-lg" />
          <Skeleton className="h-24 rounded-lg" />
        </div>
        <Skeleton className="h-10 w-32 mx-auto mb-6 rounded-full" />
        <div className="border-t pt-4 space-y-3">
          <Skeleton className="h-4 w-full" />
          <Skeleton className="h-4 w-full" />
        </div>
      </div>
    </div>
  );
}
