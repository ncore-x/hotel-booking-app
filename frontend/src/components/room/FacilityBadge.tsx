import type { Facility } from "../../types/facility";

export function FacilityBadge({ facility }: { facility: Facility }) {
  return (
    <span className="inline-flex items-center rounded-full bg-blue-50 px-2.5 py-0.5 text-xs font-medium text-blue-700 dark:bg-blue-900/30 dark:text-blue-300">
      {facility.title}
    </span>
  );
}
