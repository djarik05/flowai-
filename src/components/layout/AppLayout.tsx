import React from 'react';
import { Header } from './Header';
import { HideUIOverlay } from '../modals/HideUIOverlay';

interface AppLayoutProps {
  children: React.ReactNode;
}

export const AppLayout: React.FC<AppLayoutProps> = ({ children }) => {
  return (
    <div className="relative min-h-screen w-full bg-[#070B12] text-[#F1F5F9] flex flex-col overflow-x-hidden">
      {/* Subtle atmospheric ambient glow */}
      <div className="fixed top-0 left-1/3 w-[800px] h-[350px] bg-[radial-gradient(ellipse_at_top,rgba(72,221,245,0.06)_0%,transparent_70%)] pointer-events-none z-0" />
      <div className="fixed bottom-0 right-1/4 w-[600px] h-[400px] bg-[radial-gradient(ellipse_at_bottom,rgba(68,141,255,0.05)_0%,transparent_70%)] pointer-events-none z-0" />

      {/* Persistent Glass Header */}
      <Header />

      {/* Main Content Area */}
      <main className="relative z-10 flex-1 w-full max-w-7xl mx-auto p-4 sm:p-6 lg:p-8 flex flex-col">
        {children}
      </main>

      {/* Background Minimization Simulation Overlay */}
      <HideUIOverlay />
    </div>
  );
};
