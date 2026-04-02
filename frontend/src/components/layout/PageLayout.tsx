import type { ReactNode } from "react";
import { Header } from "./Header";

export function PageLayout({ children }: { children: ReactNode }) {
  return (
    <div className="min-h-screen bg-gray-50 text-gray-900 dark:bg-gray-900 dark:text-gray-100">
      <Header />
      <main className="mx-auto max-w-7xl px-4 py-8">{children}</main>
    </div>
  );
}
