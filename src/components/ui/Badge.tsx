import React from 'react';

export type BadgeVariant = 'cyan' | 'green' | 'blue' | 'purple' | 'warning' | 'error' | 'muted';

interface BadgeProps {
  children: React.ReactNode;
  variant?: BadgeVariant;
  className?: string;
  dot?: boolean;
}

const variantStyles: Record<BadgeVariant, { bg: string; text: string; border: string; dotColor: string }> = {
  cyan: {
    bg: 'bg-[rgba(72,221,245,0.12)]',
    text: 'text-[#48DDF5]',
    border: 'border-[rgba(72,221,245,0.25)]',
    dotColor: 'bg-[#48DDF5]',
  },
  green: {
    bg: 'bg-[rgba(66,245,165,0.12)]',
    text: 'text-[#42F5A5]',
    border: 'border-[rgba(66,245,165,0.25)]',
    dotColor: 'bg-[#42F5A5]',
  },
  blue: {
    bg: 'bg-[rgba(68,141,255,0.12)]',
    text: 'text-[#448DFF]',
    border: 'border-[rgba(68,141,255,0.25)]',
    dotColor: 'bg-[#448DFF]',
  },
  purple: {
    bg: 'bg-[rgba(155,124,255,0.12)]',
    text: 'text-[#9B7CFF]',
    border: 'border-[rgba(155,124,255,0.25)]',
    dotColor: 'bg-[#9B7CFF]',
  },
  warning: {
    bg: 'bg-[rgba(255,203,112,0.12)]',
    text: 'text-[#FFCB70]',
    border: 'border-[rgba(255,203,112,0.25)]',
    dotColor: 'bg-[#FFCB70]',
  },
  error: {
    bg: 'bg-[rgba(255,100,124,0.12)]',
    text: 'text-[#FF647C]',
    border: 'border-[rgba(255,100,124,0.25)]',
    dotColor: 'bg-[#FF647C]',
  },
  muted: {
    bg: 'bg-[rgba(97,117,139,0.15)]',
    text: 'text-[#91A4B8]',
    border: 'border-[rgba(148,180,210,0.15)]',
    dotColor: 'bg-[#61758B]',
  },
};

export const Badge: React.FC<BadgeProps> = ({
  children,
  variant = 'cyan',
  className = '',
  dot = false,
}) => {
  const styles = variantStyles[variant];

  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full text-xs font-medium border ${styles.bg} ${styles.text} ${styles.border} ${className}`}
    >
      {dot && <span className={`w-1.5 h-1.5 rounded-full animate-pulse ${styles.dotColor}`} />}
      {children}
    </span>
  );
};
