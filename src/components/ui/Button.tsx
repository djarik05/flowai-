import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

export type ButtonVariant = 'primary' | 'secondary' | 'danger' | 'ghost' | 'outline';
export type ButtonSize = 'sm' | 'md' | 'lg';

interface ButtonProps extends Omit<HTMLMotionProps<'button'>, 'children'> {
  children?: React.ReactNode;
  variant?: ButtonVariant;
  size?: ButtonSize;
  icon?: React.ReactNode;
  iconPosition?: 'left' | 'right';
  isLoading?: boolean;
}

const variantClasses: Record<ButtonVariant, string> = {
  primary:
    'bg-gradient-to-r from-[#48DDF5] to-[#42F5A5] text-[#070B12] font-semibold shadow-[0_0_20px_rgba(72,221,245,0.25)] hover:shadow-[0_0_28px_rgba(72,221,245,0.4)] border border-transparent',
  secondary:
    'bg-[rgba(18,29,45,0.7)] text-[#F1F5F9] border border-[rgba(148,180,210,0.22)] hover:bg-[rgba(26,41,64,0.85)] hover:border-[rgba(72,221,245,0.4)]',
  danger:
    'bg-[rgba(255,100,124,0.18)] text-[#FF647C] border border-[rgba(255,100,124,0.35)] hover:bg-[rgba(255,100,124,0.28)] hover:shadow-[0_0_20px_rgba(255,100,124,0.25)]',
  ghost:
    'bg-transparent text-[#91A4B8] hover:text-[#F1F5F9] hover:bg-[rgba(148,180,210,0.08)] border border-transparent',
  outline:
    'bg-transparent text-[#48DDF5] border border-[rgba(72,221,245,0.35)] hover:bg-[rgba(72,221,245,0.1)]',
};

const sizeClasses: Record<ButtonSize, string> = {
  sm: 'px-2.5 py-1 text-xs rounded-lg gap-1.5',
  md: 'px-4 py-2 text-sm rounded-xl gap-2',
  lg: 'px-5 py-2.5 text-base rounded-xl gap-2.5',
};

export const Button: React.FC<ButtonProps> = ({
  children,
  variant = 'secondary',
  size = 'md',
  icon,
  iconPosition = 'left',
  isLoading = false,
  className = '',
  disabled,
  ...props
}) => {
  return (
    <motion.button
      whileHover={disabled ? undefined : { scale: 1.01 }}
      whileTap={disabled ? undefined : { scale: 0.98 }}
      transition={{ duration: 0.15 }}
      disabled={disabled || isLoading}
      className={`inline-flex items-center justify-center font-medium transition-all select-none cursor-pointer disabled:cursor-not-allowed disabled:opacity-50 disabled:shadow-none ${variantClasses[variant]} ${sizeClasses[size]} ${className}`}
      {...props}
    >
      {isLoading ? (
        <span className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin" />
      ) : (
        <>
          {icon && iconPosition === 'left' && <span className="shrink-0">{icon}</span>}
          {children && <span>{children}</span>}
          {icon && iconPosition === 'right' && <span className="shrink-0">{icon}</span>}
        </>
      )}
    </motion.button>
  );
};
