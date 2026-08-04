import React from "react";

export const Skeleton: React.FC<{ className?: string }> = ({ className = "" }) => {
  return (
    <div className={`bg-zinc-800/50 animate-pulse rounded-xl ${className}`} />
  );
};

export const CourseCardSkeleton: React.FC = () => {
  return (
    <div className="glass-card rounded-3xl overflow-hidden p-4 flex flex-col gap-4">
      <Skeleton className="w-full aspect-video rounded-2xl" />
      <div className="flex items-center justify-between">
        <Skeleton className="w-16 h-5 rounded-full" />
        <Skeleton className="w-20 h-5" />
      </div>
      <Skeleton className="w-3/4 h-6" />
      <Skeleton className="w-full h-12" />
      <div className="h-px bg-zinc-800/80 my-1" />
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Skeleton className="w-6 h-6 rounded-full" />
          <Skeleton className="w-24 h-4" />
        </div>
        <Skeleton className="w-16 h-5" />
      </div>
    </div>
  );
};

export const StatsSkeleton: React.FC = () => {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 w-full">
      {[1, 2, 3, 4].map((i) => (
        <div key={i} className="glass-card rounded-3xl p-6 flex flex-col gap-3">
          <div className="flex items-center justify-between">
            <Skeleton className="w-12 h-12 rounded-2xl" />
            <Skeleton className="w-16 h-4" />
          </div>
          <Skeleton className="w-28 h-4" />
          <Skeleton className="w-16 h-8" />
        </div>
      ))}
    </div>
  );
};

export const TableSkeleton: React.FC = () => {
  return (
    <div className="glass-card rounded-3xl p-6 flex flex-col gap-4 w-full">
      <div className="flex items-center justify-between">
        <Skeleton className="w-48 h-6" />
        <Skeleton className="w-24 h-8" />
      </div>
      <div className="flex flex-col gap-3 mt-4">
        {[1, 2, 3, 4, 5].map((i) => (
          <div key={i} className="flex items-center justify-between py-2 border-b border-zinc-850/60 last:border-0">
            <div className="flex items-center gap-3">
              <Skeleton className="w-10 h-10 rounded-full" />
              <div className="flex flex-col gap-1.5">
                <Skeleton className="w-36 h-4" />
                <Skeleton className="w-24 h-3.5" />
              </div>
            </div>
            <Skeleton className="w-20 h-5" />
            <Skeleton className="w-16 h-5" />
          </div>
        ))}
      </div>
    </div>
  );
};
export default Skeleton;
