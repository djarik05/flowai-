import React, { useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { X } from 'lucide-react';

interface ModalProps {
  isOpen: boolean;
  onClose: () => void;
  title: string;
  description?: string;
  children: React.ReactNode;
  maxWidth?: string;
}

export const Modal: React.FC<ModalProps> = ({
  isOpen,
  onClose,
  title,
  description,
  children,
  maxWidth = 'max-w-lg',
}) => {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  return (
    <AnimatePresence>
      {isOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            onClick={onClose}
            className="fixed inset-0 bg-[#070B12]/80 backdrop-blur-md"
          />

          <motion.div
            initial={{ scale: 0.95, opacity: 0, y: 16 }}
            animate={{ scale: 1, opacity: 1, y: 0 }}
            exit={{ scale: 0.95, opacity: 0, y: 16 }}
            transition={{ type: 'spring', damping: 25, stiffness: 350 }}
            className={`relative w-full ${maxWidth} glass-strong rounded-2xl border border-[rgba(148,180,210,0.25)] shadow-[0_16px_48px_rgba(0,0,0,0.6)] p-6 z-10 overflow-hidden`}
          >
            {/* Ambient cyan corner accent */}
            <div className="absolute top-0 right-0 w-48 h-48 bg-radial-glow pointer-events-none opacity-40" />

            <div className="flex items-start justify-between mb-4">
              <div>
                <h3 className="text-lg font-semibold text-[#F1F5F9]">{title}</h3>
                {description && <p className="text-xs text-[#91A4B8] mt-1">{description}</p>}
              </div>

              <button
                onClick={onClose}
                className="text-[#91A4B8] hover:text-[#F1F5F9] p-1.5 rounded-lg hover:bg-[rgba(148,180,210,0.1)] transition-colors cursor-pointer"
              >
                <X className="w-5 h-5" />
              </button>
            </div>

            <div className="relative z-10">{children}</div>
          </motion.div>
        </div>
      )}
    </AnimatePresence>
  );
};
