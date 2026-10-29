import React from 'react';

export interface SelectOption {
  value: string;
  label: string;
  description?: string;
}

interface SelectProps {
  value: string;
  onChange: (val: string) => void;
  options: SelectOption[];
  label?: string;
  description?: string;
  disabled?: boolean;
  className?: string;
}

export const Select: React.FC<SelectProps> = ({
  value,
  onChange,
  options,
  label,
  description,
  disabled = false,
  className = '',
}) => {
  return (
    <div className={`w-full flex flex-col gap-1.5 ${disabled ? 'opacity-50' : ''} ${className}`}>
      {label && <label className="text-xs font-medium text-[#F1F5F9]">{label}</label>}
      {description && <p className="text-[11px] text-[#91A4B8] mb-0.5">{description}</p>}

      <div className="relative">
        <select
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(e.target.value)}
          className="w-full appearance-none bg-[rgba(11,18,32,0.85)] border border-[rgba(148,180,210,0.2)] rounded-xl px-3.5 py-2 text-sm text-[#F1F5F9] focus:outline-none focus:border-[#48DDF5] focus:ring-1 focus:ring-[#48DDF5]/30 cursor-pointer disabled:cursor-not-allowed transition-all"
        >
          {options.map((opt) => (
            <option key={opt.value} value={opt.value} className="bg-[#0B1220] text-[#F1F5F9] py-1">
              {opt.label} {opt.description ? `(${opt.description})` : ''}
            </option>
          ))}
        </select>
        <div className="pointer-events-none absolute inset-y-0 right-0 flex items-center px-3 text-[#91A4B8]">
          <svg className="h-4 w-4 fill-current" viewBox="0 0 20 20">
            <path d="M5.293 7.293a1 1 0 011.414 0L10 10.586l3.293-3.293a1 1 0 111.414 1.414l-4 4a1 1 0 01-1.414 0l-4-4a1 1 0 010-1.414z" />
          </svg>
        </div>
      </div>
    </div>
  );
};
