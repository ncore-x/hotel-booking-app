import { useState } from "react";
import {
  format,
  addMonths,
  subMonths,
  startOfMonth,
  endOfMonth,
  eachDayOfInterval,
  isSameDay,
  isBefore,
  isAfter,
  getDay,
  isToday,
} from "date-fns";
import { ru, enUS } from "date-fns/locale";
import { useLangStore } from "../../stores/langStore";
import { useT } from "../../i18n/useT";

interface DateRangePickerProps {
  dateFrom: string;
  dateTo: string;
  onChange: (from: string, to: string) => void;
  onClose: () => void;
}

function toISO(d: Date): string {
  return format(d, "yyyy-MM-dd");
}

function parseLocal(s: string): Date {
  return new Date(s + "T12:00:00");
}

function getMonthGrid(monthDate: Date): (Date | null)[] {
  const start = startOfMonth(monthDate);
  const end = endOfMonth(monthDate);
  const days = eachDayOfInterval({ start, end });
  // Monday-start: Sun=0 → pad 6, Mon=1 → pad 0
  const padding = (getDay(start) + 6) % 7;
  return [...Array(padding).fill(null), ...days];
}

const WEEKDAYS_EN = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"];
const WEEKDAYS_RU = ["Пн", "Вт", "Ср", "Чт", "Пт", "Сб", "Вс"];

export function DateRangePicker({ dateFrom, dateTo, onChange, onClose }: DateRangePickerProps) {
  const { lang } = useLangStore();
  const locale = lang === "ru" ? ru : enUS;
  const t = useT();

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const [viewMonth, setViewMonth] = useState<Date>(() => startOfMonth(parseLocal(dateFrom)));
  const [anchor, setAnchor] = useState<Date | null>(null);
  const [hoverDate, setHoverDate] = useState<Date | null>(null);

  const rightMonth = addMonths(viewMonth, 1);

  const committedFrom = parseLocal(dateFrom);
  const committedTo = parseLocal(dateTo);

  function handleDayClick(day: Date) {
    if (isBefore(day, today)) return;
    if (!anchor) {
      setAnchor(day);
    } else {
      if (!isBefore(day, anchor)) {
        onChange(toISO(anchor), toISO(day));
        setAnchor(null);
        onClose();
      } else {
        setAnchor(day);
      }
    }
  }

  function getDayState(day: Date) {
    const isPast = isBefore(day, today);
    const isStart = anchor ? isSameDay(day, anchor) : isSameDay(day, committedFrom);
    const isEnd = !anchor && isSameDay(day, committedTo);

    let isInRange = false;
    let isHovering = false;

    if (anchor) {
      if (hoverDate && !isBefore(hoverDate, anchor)) {
        isInRange = isAfter(day, anchor) && isBefore(day, hoverDate);
        isHovering = isSameDay(day, hoverDate);
      }
    } else {
      isInRange = isAfter(day, committedFrom) && isBefore(day, committedTo);
    }

    return { isPast, isStart, isEnd, isInRange, isHovering };
  }

  function renderMonth(monthDate: Date) {
    const grid = getMonthGrid(monthDate);
    const weekdays = lang === "ru" ? WEEKDAYS_RU : WEEKDAYS_EN;
    const monthLabel = format(monthDate, "LLLL yyyy", { locale });

    return (
      <div className="min-w-[260px] flex-1">
        <p className="mb-3 text-center text-sm font-semibold capitalize text-ink">{monthLabel}</p>
        <div className="grid grid-cols-7 gap-y-1 text-center">
          {weekdays.map((wd) => (
            <div key={wd} className="py-1 text-[11px] font-semibold uppercase text-subtle">
              {wd}
            </div>
          ))}
          {grid.map((day, idx) => {
            if (!day) return <div key={`pad-${idx}`} />;
            const { isPast, isStart, isEnd, isInRange, isHovering } = getDayState(day);
            const isHighlightEnd = isEnd || isHovering;
            const todayMark = isToday(day);

            let cellClass =
              "relative flex h-8 w-full cursor-pointer select-none items-center justify-center rounded-full text-sm transition-colors";

            if (isStart || isHighlightEnd) {
              cellClass += " bg-brand text-on-brand font-semibold";
            } else if (isInRange) {
              cellClass += " rounded-none bg-brand/10 text-ink";
            } else if (isPast) {
              cellClass += " cursor-not-allowed text-subtle";
            } else {
              cellClass += " text-ink hover:bg-secondary";
            }

            // Round left/right edges of range
            let rangeEdgeClass = "";
            if (isInRange) {
              const dayOfWeek = (getDay(day) + 6) % 7; // 0=Mon
              if (dayOfWeek === 0) rangeEdgeClass = " rounded-l-full";
              else if (dayOfWeek === 6) rangeEdgeClass = " rounded-r-full";
            }

            return (
              <div
                key={toISO(day)}
                className={cellClass + rangeEdgeClass}
                onClick={() => handleDayClick(day)}
                onMouseEnter={() => setHoverDate(day)}
                onMouseLeave={() => setHoverDate(null)}
              >
                {String(day.getDate())}
                {todayMark && !isStart && !isHighlightEnd && (
                  <span className="absolute bottom-1 left-1/2 h-1 w-1 -translate-x-1/2 rounded-full bg-brand" />
                )}
              </div>
            );
          })}
        </div>
      </div>
    );
  }

  return (
    <div className="rounded-2xl border border-divider bg-card p-4 shadow-xl">
      {/* Month navigation */}
      <div className="mb-4 flex items-center justify-between">
        <button
          type="button"
          onClick={() => setViewMonth((m) => subMonths(m, 1))}
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-secondary hover:text-ink"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 19.5L8.25 12l7.5-7.5" />
          </svg>
        </button>

        <div className="flex flex-1 gap-4">
          {renderMonth(viewMonth)}
          <div className="hidden w-px bg-divider sm:block" />
          <div className="hidden sm:block">{renderMonth(rightMonth)}</div>
        </div>

        <button
          type="button"
          onClick={() => setViewMonth((m) => addMonths(m, 1))}
          className="flex h-8 w-8 items-center justify-center rounded-full text-muted transition-colors hover:bg-secondary hover:text-ink"
        >
          <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
            <path strokeLinecap="round" strokeLinejoin="round" d="M8.25 4.5l7.5 7.5-7.5 7.5" />
          </svg>
        </button>
      </div>

      {anchor && (
        <p className="mt-1 text-center text-xs text-muted">
          {lang === "ru" ? "Выберите дату выезда" : "Select check-out date"}
        </p>
      )}

      <div className="mt-3 flex justify-end">
        <button
          type="button"
          onClick={onClose}
          className="rounded-xl bg-brand px-5 py-2 text-sm font-semibold text-on-brand transition-colors hover:bg-brand-hv"
        >
          {t.search.done}
        </button>
      </div>
    </div>
  );
}
