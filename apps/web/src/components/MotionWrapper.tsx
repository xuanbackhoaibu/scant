"use client";

import { motion, MotionConfig } from "framer-motion";
import { usePathname } from "next/navigation";
import { ReactNode } from "react";

export function MotionWrapper({ children }: { children: ReactNode }) {
  const pathname = usePathname();

  return (
    <MotionConfig reducedMotion="user">
      <motion.div
        key={pathname}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.18, ease: "easeOut" }}
        className="min-h-0"
      >
        {children}
      </motion.div>
    </MotionConfig>
  );
}
