"use client";

import React, { useState, useEffect } from "react";
import { Sparkles, BookOpen, BarChart2, Clock } from "lucide-react";

export function SolarSystemOrbit() {
  // Staggered and continuous animation delays
  const [delays, setDelays] = useState({
    ring1: 0,
    ring2: 0,
    ring3: 0,
    ring4: 0,
  });

  useEffect(() => {
    // Wall-clock continuous progression stored in sessionStorage
    // Cost: zero performance impact (computes once on mount, 100% GPU CSS animation)
    let anchor = 0;
    try {
      const stored = sessionStorage.getItem("nexo_orbit_anchor");
      if (stored) {
        anchor = parseFloat(stored);
      } else {
        anchor = Date.now() / 1000;
        sessionStorage.setItem("nexo_orbit_anchor", anchor.toString());
      }
    } catch {
      anchor = Date.now() / 1000;
    }

    const elapsed = Math.max(0, Date.now() / 1000 - anchor);

    // Stagger initial phases so planets & badges start in different quadrants,
    // plus elapsed time to resume continuously when refreshing or navigating
    setDelays({
      ring1: (elapsed + 7.5) % 22,
      ring2: (elapsed + 16.0) % 34,
      ring3: (elapsed + 28.5) % 48,
      ring4: (elapsed + 44.0) % 64,
    });
  }, []);

  return (
    <div className="relative w-[360px] h-[360px] sm:w-[480px] sm:h-[480px] lg:w-[600px] lg:h-[600px] flex items-center justify-center select-none pointer-events-none">
      {/* Ambient glowing radial aura (#39BEAD at 20%) */}
      <div className="absolute w-80 h-80 rounded-full bg-[#39BEAD]/20 blur-3xl animate-pulse-glow" />
      <div className="absolute w-[460px] h-[460px] rounded-full bg-[#0A635F]/15 blur-3xl pointer-events-none" />

      {/* Orbit Ring 4 (Outermost - 540px) */}
      <div
        className="absolute w-[340px] h-[340px] sm:w-[460px] sm:h-[460px] lg:w-[540px] lg:h-[540px] rounded-full border border-[#65D7C9]/15 animate-orbit-outer"
        style={{ animationDelay: `-${delays.ring4}s` }}
      >
        {/* Badge: 8 min al día */}
        <div className="absolute -bottom-4 left-1/2 -translate-x-1/2">
          <div
            className="animate-counter-outer"
            style={{ animationDelay: `-${delays.ring4}s` }}
          >
            <div className="bg-[#0B2D34]/90 backdrop-blur-md border border-[#65D7C9]/45 text-teal-50 text-[10px] sm:text-[11px] font-semibold px-3.5 py-1.5 rounded-xl shadow-lg shadow-[#0B2D34]/80 flex items-center gap-1.5 whitespace-nowrap">
              <Clock className="w-3.5 h-3.5 text-[#69D7C9]" />
              <span>8 min al día</span>
            </div>
          </div>
        </div>

        {/* Small celestial dot */}
        <div className="absolute top-16 left-16">
          <div className="w-2 h-2 rounded-full bg-[#38bdf8] shadow-sm shadow-[#38bdf8]" />
        </div>
      </div>

      {/* Orbit Ring 3 (420px) */}
      <div
        className="absolute w-[260px] h-[260px] sm:w-[360px] sm:h-[360px] lg:w-[420px] lg:h-[420px] rounded-full border border-[#65D7C9]/20 animate-orbit-slow"
        style={{ animationDelay: `-${delays.ring3}s` }}
      >
        {/* Badge: Progreso */}
        <div className="absolute top-1/2 -right-8 sm:-right-10 -translate-y-1/2">
          <div
            className="animate-counter-slow"
            style={{ animationDelay: `-${delays.ring3}s` }}
          >
            <div className="bg-[#0B2D34]/90 backdrop-blur-md border border-[#65D7C9]/45 text-teal-50 text-[10px] sm:text-[11px] font-semibold px-3.5 py-1.5 rounded-xl shadow-lg shadow-[#0B2D34]/80 flex items-center gap-1.5 whitespace-nowrap">
              <BarChart2 className="w-3.5 h-3.5 text-[#69D7C9]" />
              <span>Progreso</span>
            </div>
          </div>
        </div>

        {/* Small amber celestial dot */}
        <div className="absolute top-1/2 -left-1.5 -translate-y-1/2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#fde047] shadow-sm shadow-[#fde047]" />
        </div>
      </div>

      {/* Orbit Ring 2 (300px) */}
      <div
        className="absolute w-[185px] h-[185px] sm:w-[260px] sm:h-[260px] lg:w-[300px] lg:h-[300px] rounded-full border border-[#65D7C9]/25 animate-orbit-medium"
        style={{ animationDelay: `-${delays.ring2}s` }}
      >
        {/* Badge: Microlecciones */}
        <div className="absolute -top-4 left-1/2 -translate-x-1/2">
          <div
            className="animate-counter-medium"
            style={{ animationDelay: `-${delays.ring2}s` }}
          >
            <div className="bg-[#0B2D34]/90 backdrop-blur-md border border-[#65D7C9]/45 text-teal-50 text-[10px] sm:text-[11px] font-semibold px-3.5 py-1.5 rounded-xl shadow-lg shadow-[#0B2D34]/80 flex items-center gap-1.5 whitespace-nowrap">
              <BookOpen className="w-3.5 h-3.5 text-[#69D7C9]" />
              <span>Microlecciones</span>
            </div>
          </div>
        </div>

        {/* Small purple celestial dot */}
        <div className="absolute -bottom-1 left-1/2 -translate-x-1/2">
          <div className="w-2.5 h-2.5 rounded-full bg-[#c084fc] shadow-sm shadow-[#c084fc]" />
        </div>
      </div>

      {/* Orbit Ring 1 (Innermost - 180px) */}
      <div
        className="absolute w-[120px] h-[120px] sm:w-[155px] sm:h-[155px] lg:w-[180px] lg:h-[180px] rounded-full border border-[#65D7C9]/30 animate-orbit-fast"
        style={{ animationDelay: `-${delays.ring1}s` }}
      >
        {/* Small turquoise luminous dot */}
        <div className="absolute -top-1.5 left-1/2 -translate-x-1/2">
          <div className="w-3 h-3 rounded-full bg-[#65D7C9] shadow-md shadow-[#65D7C9]" />
        </div>
      </div>

      {/* Central Sun / Nexo Glowing Core */}
      <div className="relative flex items-center justify-center">
        {/* Outer glowing radial halo */}
        <div className="absolute w-28 h-28 rounded-full bg-[#39BEAD]/30 blur-xl animate-pulse-glow" />

        {/* Intermediate aura */}
        <div className="w-20 h-20 sm:w-24 sm:h-24 rounded-full bg-[#123E45]/60 border border-[#65D7C9]/40 flex items-center justify-center">
          {/* Core Orb with gradient */}
          <div className="w-12 h-12 sm:w-16 sm:h-16 rounded-full bg-gradient-to-br from-[#69D7C9] via-[#39BEAD] to-[#0A635F] flex items-center justify-center shadow-xl shadow-[#39BEAD]/40 text-[#0B2D34]">
            <Sparkles className="w-6 h-6 sm:w-7 sm:h-7 text-[#0B2D34] animate-pulse" />
          </div>
        </div>
      </div>
    </div>
  );
}
