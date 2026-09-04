"use client";

type SkeletonLoaderProps = {
  count?: number;
  className?: string;
};

export function SkeletonLoader({ count = 3, className = "" }: SkeletonLoaderProps) {
  return (
    <>
      {Array.from({ length: count }).map((_, index) => (
        <div
          key={index}
          className={`overflow-hidden rounded-xl border border-slate-200 bg-white p-4 shadow-2xs dark:border-slate-700 dark:bg-slate-900 ${className}`}
        >
          <div className="animate-pulse space-y-4">
            <div className="h-24 rounded-lg bg-slate-100 dark:bg-slate-800" />
            <div className="h-3 w-2/3 rounded-full bg-slate-100 dark:bg-slate-800" />
            <div className="space-y-2">
              <div className="h-2 rounded-full bg-slate-100 dark:bg-slate-800" />
              <div className="h-2 w-5/6 rounded-full bg-slate-100 dark:bg-slate-800" />
            </div>
          </div>
        </div>
      ))}
    </>
  );
}
