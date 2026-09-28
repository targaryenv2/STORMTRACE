import React, { useState } from 'react';
import { getCellRiskTrend } from '../../services/nowcastService';

export default function CellRiskTrendChart({ cell }) {
  const [hoveredBar, setHoveredBar] = useState(null);

  const trendData = getCellRiskTrend(cell);
  const { isNew, history, forecast } = trendData;

  // Chart dimensions
  const svgWidth = 260;
  const svgHeight = 44;
  const maxScore = 100;
  const chartBottom = 34; // baseline y-coordinate for bars
  const maxBarHeight = 28; // maximum height in px for score = 100

  // Severity color mapping for forecast bars matching severity tier
  const getSeverityFill = (score) => {
    if (score >= 80) return '#ef4444'; // Red (High)
    if (score >= 60) return '#f97316'; // Orange (Moderate)
    if (score >= 40) return '#eab308'; // Yellow (Low)
    return '#22c55e'; // Green (Weak)
  };

  const pastBarFill = '#94a3b8'; // Neutral Slate-400 for past observed

  // Geometry calculation: partition width into past (left) and forecast (right)
  const dividerX = 96;
  const pastWidth = dividerX - 10;
  const forecastWidth = svgWidth - dividerX - 10;

  const numPast = history.length;
  const pastBarWidth = 12;
  const pastSpacing = numPast > 1 ? (pastWidth - (numPast * pastBarWidth)) / (numPast - 1) : 0;

  const numForecast = forecast.length; // 6 lead times
  const forecastBarWidth = 14;
  const forecastSpacing = (forecastWidth - (numForecast * forecastBarWidth)) / (numForecast - 1);

  return (
    <div className="w-full bg-slate-50/90 border border-slate-200/90 rounded-xl p-2.5 space-y-1.5 transition-all">
      {/* Header labels */}
      <div className="flex items-center justify-between text-[10px] font-bold text-slate-500 tracking-tight px-0.5">
        <div className="flex items-center space-x-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
          <span>Past Trend</span>
        </div>
        <div className="flex items-center space-x-1.5">
          <span className={`w-1.5 h-1.5 rounded-full ${
            cell?.severity_score >= 80 ? 'bg-rose-500' :
            cell?.severity_score >= 60 ? 'bg-amber-500' :
            'bg-yellow-400'
          }`}></span>
          <span>Forecast (+15m → +120m)</span>
        </div>
      </div>

      {/* SVG Multi-Bar Trend Chart */}
      <div className="relative w-full overflow-hidden">
        <svg
          viewBox={`0 0 ${svgWidth} ${svgHeight}`}
          className="w-full h-[52px] select-none"
        >
          {/* Subtle horizontal grid lines */}
          <line x1="4" y1={chartBottom - maxBarHeight} x2={svgWidth - 4} y2={chartBottom - maxBarHeight} stroke="#e2e8f0" strokeDasharray="2 2" strokeWidth="0.8" />
          <line x1="4" y1={chartBottom - (maxBarHeight / 2)} x2={svgWidth - 4} y2={chartBottom - (maxBarHeight / 2)} stroke="#f1f5f9" strokeDasharray="2 2" strokeWidth="0.8" />
          <line x1="4" y1={chartBottom} x2={svgWidth - 4} y2={chartBottom} stroke="#cbd5e1" strokeWidth="1" />

          {/* Past / Forecast Vertical Divider */}
          <line
            x1={dividerX}
            y1="4"
            x2={dividerX}
            y2={svgHeight - 2}
            stroke="#94a3b8"
            strokeDasharray="2 2"
            strokeWidth="1.2"
          />

          {/* Past Observed Bars or New Cell Message */}
          {isNew || numPast === 0 ? (
            <text
              x={dividerX / 2}
              y={chartBottom - (maxBarHeight / 2) + 3}
              textAnchor="middle"
              className="text-[9.5px] fill-slate-400 font-medium italic"
            >
              New cell — no history yet
            </text>
          ) : (
            history.map((item, idx) => {
              const barH = Math.max(4, (item.score / maxScore) * maxBarHeight);
              const x = 8 + (idx * (pastBarWidth + pastSpacing));
              const y = chartBottom - barH;
              const isHovered = hoveredBar?.id === `past-${idx}`;

              return (
                <g key={`past-${idx}`} className="cursor-pointer">
                  <rect
                    x={x}
                    y={y}
                    width={pastBarWidth}
                    height={barH}
                    rx="2"
                    fill={isHovered ? '#64748b' : pastBarFill}
                    className="transition-all duration-150"
                    onMouseEnter={() => setHoveredBar({ id: `past-${idx}`, label: `${item.label}: Score ${item.score} (${item.dbz} dBZ)` })}
                    onMouseLeave={() => setHoveredBar(null)}
                  />
                  {/* Small time label */}
                  <text
                    x={x + (pastBarWidth / 2)}
                    y={chartBottom + 8}
                    textAnchor="middle"
                    className="text-[8px] fill-slate-400 font-semibold"
                  >
                    {item.label}
                  </text>
                </g>
              );
            })
          )}

          {/* Forecast Horizon Bars */}
          {forecast.map((item, idx) => {
            const barH = Math.max(4, (item.score / maxScore) * maxBarHeight);
            const x = dividerX + 8 + (idx * (forecastBarWidth + forecastSpacing));
            const y = chartBottom - barH;
            const fill = getSeverityFill(item.score);
            const isHovered = hoveredBar?.id === `forecast-${idx}`;

            return (
              <g key={`forecast-${idx}`} className="cursor-pointer">
                <rect
                  x={x}
                  y={y}
                  width={forecastBarWidth}
                  height={barH}
                  rx="2"
                  fill={fill}
                  opacity={isHovered ? 1 : 0.88}
                  className="transition-all duration-150"
                  onMouseEnter={() => setHoveredBar({ id: `forecast-${idx}`, label: `${item.label}: Score ${item.score} (${item.dbz} dBZ)` })}
                  onMouseLeave={() => setHoveredBar(null)}
                />
                {/* Small lead time label */}
                <text
                  x={x + (forecastBarWidth / 2)}
                  y={chartBottom + 8}
                  textAnchor="middle"
                  className="text-[8px] fill-slate-500 font-bold"
                >
                  {item.time_min}m
                </text>
              </g>
            );
          })}
        </svg>

        {/* Hover Floating Tooltip */}
        {hoveredBar && (
          <div className="absolute top-0 right-1 bg-slate-900/90 text-white text-[9.5px] px-1.5 py-0.5 rounded shadow pointer-events-none font-mono font-medium">
            {hoveredBar.label}
          </div>
        )}
      </div>
    </div>
  );
}
