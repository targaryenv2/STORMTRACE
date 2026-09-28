import React, { useEffect, useState } from 'react';
import { Play, Pause } from 'lucide-react';

const LEAD_TIMES = [15, 30, 45, 60, 90, 120];

export default function LeadTimeSlider({
  leadTimeMin = 30,
  setLeadTimeMin
}) {
  const [isPlaying, setIsPlaying] = useState(false);

  // Map leadTimeMin to step index (0 to 5)
  const currentStep = LEAD_TIMES.indexOf(leadTimeMin) !== -1 
    ? LEAD_TIMES.indexOf(leadTimeMin) 
    : 1;

  // Animation timer loop
  useEffect(() => {
    let interval = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setLeadTimeMin((prev) => {
          const idx = LEAD_TIMES.indexOf(prev);
          const nextIdx = (idx + 1) % LEAD_TIMES.length;
          return LEAD_TIMES[nextIdx];
        });
      }, 1500);
    }
    return () => clearInterval(interval);
  }, [isPlaying, setLeadTimeMin]);

  const handleSliderChange = (e) => {
    const stepIdx = parseInt(e.target.value, 10);
    setLeadTimeMin(LEAD_TIMES[stepIdx]);
  };

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-full px-4 py-2.5 shadow-2xl flex items-center space-x-4 select-none max-w-md mx-auto">
      {/* Play/Pause icon button */}
      <button
        onClick={() => setIsPlaying(!isPlaying)}
        className="p-1.5 rounded-full hover:bg-slate-800 text-slate-300 hover:text-slate-100 transition shrink-0"
        title={isPlaying ? 'Pause animation' : 'Play animation'}
        aria-label={isPlaying ? 'Pause animation' : 'Play animation'}
      >
        {isPlaying ? (
          <Pause className="w-4 h-4 fill-slate-300" />
        ) : (
          <Play className="w-4 h-4 fill-slate-300 ml-0.5" />
        )}
      </button>

      {/* Range Slider */}
      <div className="flex-1 flex flex-col justify-center">
        <input
          type="range"
          min="0"
          max="5"
          step="1"
          value={currentStep}
          onChange={handleSliderChange}
          className="w-full h-1.5 bg-slate-800 rounded-lg appearance-none cursor-pointer accent-sky-500 focus:outline-none"
        />
        <div className="flex justify-between text-[10px] text-slate-500 font-medium px-0.5 mt-1">
          <span>+15m</span>
          <span>+30m</span>
          <span>+45m</span>
          <span>+60m</span>
          <span>+90m</span>
          <span>+120m</span>
        </div>
      </div>

      {/* Single text readout */}
      <div className="text-xs font-medium text-slate-200 shrink-0 min-w-[100px] text-right">
        Forecast in <span className="text-sky-400 font-semibold">{leadTimeMin} min</span>
      </div>
    </div>
  );
}
