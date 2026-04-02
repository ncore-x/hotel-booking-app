import { Link } from "react-router";
import { motion } from "framer-motion";
import type { Hotel } from "../../types/hotel";
import { Card } from "../ui/Card";

export function HotelCard({ hotel }: { hotel: Hotel }) {
  return (
    <Link to={`/hotels/${hotel.id}`}>
      <motion.div whileHover={{ y: -2 }} transition={{ duration: 0.2 }}>
        <Card className="cursor-pointer transition-shadow hover:shadow-md">
          <div className="mb-3 flex h-40 items-center justify-center rounded-lg bg-gradient-to-br from-blue-100 to-blue-200 dark:from-blue-900 dark:to-blue-800">
            <svg className="h-12 w-12 text-blue-400" fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={1.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 21h19.5m-18-18v18m10.5-18v18m6-13.5V21M6.75 6.75h.75m-.75 3h.75m-.75 3h.75m3-6h.75m-.75 3h.75m-.75 3h.75M6.75 21v-3.375c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125V21M3 3h12m-.75 4.5H21m-3.75 0h.008v.008h-.008V7.5z" />
            </svg>
          </div>
          <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
            {hotel.title}
          </h3>
          <p className="mt-1 text-sm text-gray-500 dark:text-gray-400">
            {hotel.location}
          </p>
        </Card>
      </motion.div>
    </Link>
  );
}
