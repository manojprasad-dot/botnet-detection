import React from "react";
import { Check } from "lucide-react";
import { motion } from "framer-motion";

export default function RememberDevice({ checked, onChange, disabled = false }) {
  return (
    <label className="flex items-center gap-2.5 cursor-pointer select-none group text-xs text-slate-400 hover:text-white transition-colors duration-200">
      <div className="relative">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => onChange(e.target.checked)}
          disabled={disabled}
          className="sr-only"
        />
        
        {/* Checkbox box */}
        <motion.div
          animate={{
            borderColor: checked ? "#06B6D4" : "rgba(148, 163, 184, 0.2)",
            backgroundColor: checked ? "rgba(6, 182, 212, 0.1)" : "rgba(17, 24, 37, 0.6)",
          }}
          transition={{ duration: 0.2 }}
          className={`h-4.5 w-4.5 rounded border flex items-center justify-center transition-all ${
            disabled ? "opacity-50 cursor-not-allowed" : "group-hover:border-cyan-500/50"
          }`}
        >
          {checked && (
            <motion.span
              initial={{ scale: 0.5, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              transition={{ type: "spring", stiffness: 500, damping: 30 }}
            >
              <Check className="h-3 w-3 text-cyan-400 stroke-[3]" />
            </motion.span>
          )}
        </motion.div>
      </div>

      <span className="font-orbitron font-medium tracking-wider text-[10px]">
        REMEMBER THIS DEVICE
      </span>
    </label>
  );
}
