import React from 'react';
import { motion } from 'framer-motion';

export interface SwitchProps {
  checked: boolean;
  onChange: (checked: boolean) => void;
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
  title?: string;
}

export const Switch: React.FC<SwitchProps> = ({
  checked,
  onChange,
  label,
  description,
  disabled = false,
  className = '',
  title,
}) => {
  return (
    <label
      title={title}
      className={`inline-flex items-center justify-between gap-3 cursor-pointer select-none ${
        disabled ? 'opacity-50 cursor-not-allowed' : ''
      } ${className}`}
      onClick={(e) => {
        if (disabled) e.preventDefault();
      }}
    >
      {(label || description) && (
        <div className="flex flex-col text-left">
          {label && <span className="text-sm font-medium text-[#F1F5F9]">{label}</span>}
          {description && <span className="text-xs text-[#91A4B8]">{description}</span>}
        </div>
      )}

      <button
        type="button"
        role="switch"
        aria-checked={checked}
        disabled={disabled}
        onClick={() => !disabled && onChange(!checked)}
        className={`relative inline-flex h-6 w-11 shrink-0 cursor-pointer rounded-full border transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-[#48DDF5]/40 ${
          checked
            ? 'bg-[#48DDF5] border-[#48DDF5]/60 shadow-[0_0_12px_rgba(72,221,245,0.3)]'
            : 'bg-[#0B1220] border-[rgba(148,180,210,0.2)]'
        }`}
      >
        <motion.span
          layout
          transition={{ type: 'spring', stiffness: 500, damping: 30 }}
          className={`pointer-events-none inline-block h-4 w-4 rounded-full shadow-lg ring-0 transition-colors mt-0.5 ${
            checked ? 'translate-x-5 bg-[#070B12]' : 'translate-x-0.5 bg-[#91A4B8]'
          }`}
        />
      </button>
    </label>
  );
};
