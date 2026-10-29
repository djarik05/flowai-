import React from 'react';
import { motion, HTMLMotionProps } from 'framer-motion';

interface CardProps extends HTMLMotionProps<'div'> {
  children: React.ReactNode;
  variant?: 'glass' | 'glass-light' | 'glass-strong' | 'glow';
  className?: string;
  hoverable?: boolean;
}

export const Card: React.FC<CardProps> = ({
  children,
  variant = 'glass',
  className = '',
  hoverable = false,
  ...props
}) => {
  const variantStyles = {
    glass: 'bg-[rgba(18,29,45,0.62)] border-[rgba(148,180,210,0.16)] backdrop-blur-md',
    'glass-light': 'bg-[rgba(18,29,45,0.35)] border-[rgba(148,180,210,0.1)] backdrop-blur-sm',
    'glass-strong': 'bg-[rgba(18,29,45,0.85)] border-[rgba(148,180,210,0.22)] backdrop-blur-xl',
    glow: 'bg-[rgba(18,29,45,0.7)] border-[rgba(72,221,245,0.28)] shadow-[0_0_24px_rgba(72,221,245,0.08)] backdrop-blur-md',
  };

  return (
    <motion.div
      whileHover={hoverable ? { y: -2, transition: { duration: 0.15 } } : undefined}
      className={`rounded-2xl border ${variantStyles[variant]} ${
        hoverable ? 'hover:border-[rgba(72,221,245,0.35)] hover:shadow-[0_4px_20px_rgba(0,0,0,0.25)] transition-colors' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </motion.div>
  );
};
