import { Link } from "react-router";
import { motion } from "framer-motion";
import type { Hotel } from "../../types/hotel";

export function HotelCard({ hotel }: { hotel: Hotel }) {
  return (
    <Link to={`/hotels/${hotel.id}`} aria-label={hotel.title}>
      <motion.div
        whileHover={{ y: -4, scale: 1.01 }}
        transition={{ duration: 0.2 }}
        className="group relative cursor-pointer overflow-hidden rounded-2xl"
      >
        {/* Full-bleed image */}
        <div className="relative aspect-[4/3] overflow-hidden bg-gradient-to-br from-gray-300 to-gray-400 dark:from-gray-700 dark:to-gray-600">
          {hotel.cover_image_url ? (
            <img
              src={hotel.cover_image_url}
              alt={hotel.title}
              className="absolute inset-0 h-full w-full object-cover"
            />
          ) : (
            /* Placeholder icon */
            <div className="absolute inset-0 flex items-center justify-center">
              <svg className="h-16 w-16 text-gray-400/60" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008V7.5z" />
              </svg>
            </div>
          )}

          {/* Gradient overlay */}
          <div className="absolute inset-0 bg-gradient-to-t from-black/75 via-black/20 to-transparent" />

          {/* Location badge — top left */}
          <div className="absolute left-3 top-3 z-10">
            <span className="inline-flex items-center gap-1 rounded-full bg-white/90 px-2.5 py-1 text-xs font-semibold text-gray-700 backdrop-blur-sm">
              <svg className="h-3 w-3" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 10.5a3 3 0 11-6 0 3 3 0 016 0z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M19.5 10.5c0 7.142-7.5 11.25-7.5 11.25S4.5 17.642 4.5 10.5a7.5 7.5 0 1115 0z" />
              </svg>
              {hotel.city}{hotel.address ? `, ${hotel.address}` : ""}
            </span>
          </div>

          {/* Content overlay — bottom */}
          <div className="absolute bottom-0 left-0 right-0 z-10 p-4">
            <div className="flex items-end justify-between gap-2">
              <div className="min-w-0 flex-1">
                <h3 className="truncate text-sm font-bold uppercase tracking-wide text-white">
                  {hotel.title}
                </h3>
                <p className="mt-0.5 truncate text-xs text-gray-300">
                  {hotel.city}{hotel.address ? `, ${hotel.address}` : ""}
                </p>
              </div>
            </div>
          </div>
        </div>
      </motion.div>
    </Link>
  );
}
