import React from 'react';

interface SliderProps {
  value: number;
  min: number;
  max: number;
  step?: number;
  onChange: (val: number) => void;
  label?: string;
  unit?: string;
  formatValue?: (val: number) => string;
  disabled?: boolean;
  className?: string;
  description?: string;
}

export const Slider: React.FC<SliderProps> = ({
  value,
  min,
  max,
  step = 0.01,
  onChange,
  label,
  unit = '',
  formatValue,
  disabled = false,
  className = '',
  description,
}) => {
  const percentage = Math.min(100, Math.max(0, ((value - min) / (max - min)) * 100));

  const displayValue = formatValue
    ? formatValue(value)
    : step < 0.1
    ? `${value.toFixed(2)}${unit}`
    : `${value}${unit}`;

  return (
    <div className={`w-full flex flex-col gap-1.5 ${disabled ? 'opacity-50' : ''} ${className}`}>
      <div className="flex items-center justify-between text-xs">
        {label && <span className="font-medium text-[#F1F5F9]">{label}</span>}
        <span className="font-mono text-[#48DDF5] bg-[rgba(72,221,245,0.08)] px-2 py-0.5 rounded border border-[rgba(72,221,245,0.2)]">
          {displayValue}
        </span>
      </div>

      {description && <p className="text-[11px] text-[#91A4B8] mb-0.5">{description}</p>}

      <div className="relative flex items-center h-5">
        <input
          type="range"
          min={min}
          max={max}
          step={step}
          value={value}
          disabled={disabled}
          onChange={(e) => onChange(Number(e.target.value))}
          className="absolute w-full h-1.5 bg-[#0B1220] rounded-lg appearance-none cursor-pointer focus:outline-none accent-[#48DDF5]"
          style={{
            background: `linear-gradient(to right, #48DDF5 0%, #42F5A5 ${percentage}%, #0B1220 ${percentage}%, #0B1220 100%)`,
          }}
        />
      </div>

      <div className="flex justify-between text-[10px] text-[#61758B] px-0.5">
        <span>{min}</span>
        <span>{max}</span>
      </div>
    </div>
  );
};
