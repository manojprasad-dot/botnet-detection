import React, { useState } from "react";
import { motion } from "framer-motion";

export default function FloatingInput({
  id,
  type = "text",
  label,
  value,
  onChange,
  required = false,
  icon: Icon,
  disabled = false,
  error = "",
  ...props
}) {
  const [focused, setFocused] = useState(false);

  const isFloating = focused || value.length > 0;

  return (
    <div className="w-full">
      <div className="relative w-full">
        {/* Glow backdrop on focus */}
        {focused && (
          <div className="absolute -inset-0.5 rounded-lg bg-gradient-to-r from-blue-600/20 to-cyan-500/20 blur-sm pointer-events-none transition-all duration-300" />
        )}

        <div
          className={`relative flex items-center w-full rounded-lg bg-gray-900/60 border transition-all duration-300 ${
            error
              ? "border-red-500"
              : focused
              ? "border-cyan-500 shadow-[0_0_10px_rgba(6,182,212,0.15)]"
              : "border-gray-800 hover:border-gray-700"
          }`}
        >
          {Icon && (
            <span
              className={`pl-3 flex items-center transition-colors duration-300 ${
                focused ? "text-cyan-400" : "text-slate-500"
              }`}
            >
              <Icon className="h-4.5 w-4.5" />
            </span>
          )}

          <input
            id={id}
            type={type}
            value={value}
            onChange={onChange}
            required={required}
            disabled={disabled}
            onFocus={() => setFocused(true)}
            onBlur={() => setFocused(false)}
            className={`w-full bg-transparent px-3 py-3.5 text-sm text-white placeholder-transparent outline-none disabled:opacity-50 ${
              Icon ? "pl-2" : "pl-3"
            }`}
            placeholder={label}
            {...props}
          />

          {/* Floating Label */}
          <label
            htmlFor={id}
            className={`absolute left-3 transition-all duration-300 pointer-events-none font-sans ${
              Icon ? "pl-7" : ""
            } ${
              isFloating
                ? `text-[10px] -translate-y-4 px-1.5 bg-[#030712] font-semibold ${
                    error ? "text-red-500" : "text-cyan-400 font-orbitron tracking-wider"
                  }`
                : "text-xs text-slate-500 translate-y-0"
            }`}
            style={{
              transformOrigin: "left top",
            }}
          >
            {label}
          </label>
        </div>
      </div>

      {error && (
        <motion.p
          initial={{ opacity: 0, y: -4 }}
          animate={{ opacity: 1, y: 0 }}
          className="text-[10px] text-red-500 mt-1 pl-1 font-sans"
        >
          {error}
        </motion.p>
      )}
    </div>
  );
}
