import React, { useState } from 'react';
import { HelpCircle } from 'lucide-react';

export default function TooltipHelper({ text, title = null }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <span className="relative inline-flex items-center ml-1 select-none">
      <button
        type="button"
        onClick={(e) => {
          e.stopPropagation();
          setIsOpen(!isOpen);
        }}
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
        className="text-slate-400 hover:text-sky-400 transition-colors focus:outline-none"
        aria-label="Information tooltip"
      >
        <HelpCircle className="w-3.5 h-3.5" />
      </button>

      {isOpen && (
        <span 
          className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1.5 w-56 p-2 bg-slate-900 border border-slate-700 text-slate-200 text-[11px] font-normal leading-tight rounded-lg shadow-2xl z-50 pointer-events-none animate-in fade-in zoom-in-95 duration-100"
          style={{ textTransform: 'none' }}
        >
          {title && <span className="block font-semibold text-sky-400 mb-0.5">{title}</span>}
          {text}
          <span className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-slate-900" />
        </span>
      )}
    </span>
  );
}
