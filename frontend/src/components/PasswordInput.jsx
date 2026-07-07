import React, { useState } from "react";
import { Eye, EyeOff, Lock } from "lucide-react";
import FloatingInput from "./FloatingInput";

export default function PasswordInput({
  id,
  label,
  value,
  onChange,
  required = false,
  disabled = false,
  error = "",
  ...props
}) {
  const [showPassword, setShowPassword] = useState(false);

  return (
    <div className="relative w-full">
      <FloatingInput
        id={id}
        type={showPassword ? "text" : "password"}
        label={label}
        value={value}
        onChange={onChange}
        required={required}
        disabled={disabled}
        error={error}
        icon={Lock}
        {...props}
      />
      
      <button
        type="button"
        tabIndex={-1}
        onClick={() => setShowPassword(!showPassword)}
        disabled={disabled}
        className="absolute right-3.5 top-[18px] text-slate-500 hover:text-cyan-400 transition-colors duration-200 focus:outline-none"
      >
        {showPassword ? (
          <EyeOff className="h-4.5 w-4.5" />
        ) : (
          <Eye className="h-4.5 w-4.5" />
        )}
      </button>
    </div>
  );
}
