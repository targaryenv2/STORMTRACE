import { useState, useEffect } from 'react';

const FALLBACK_STORMS = [
  {
    cell_id: 'SC-LIVE-901',
    nearest_airport: 'Mumbai',
    lon: 72.8777,
    lat: 19.0760,
    radius: 400,
    intensity: 0.8,
    lightning: 0.8,
    warning_level: 'ORANGE',
    color: '#f97316',
    max_dbz: 52,
    speed_kmh: 38,
    direction_deg: 90,
    compass: 'E',
    severity_score: 78,
    polygon: [[72.87, 19.47], [73.27, 19.07], [72.87, 18.67], [72.47, 19.07]],
    trajectory: [
      { lon: 72.9777, lat: 19.0760, time_offset: 15 },
      { lon: 73.0777, lat: 19.0760, time_offset: 30 },
      { lon: 73.1777, lat: 19.0760, time_offset: 45 },
      { lon: 73.2777, lat: 19.0760, time_offset: 60 }
    ],
    impact_zone: [[72.87, 19.47], [73.57, 19.57], [73.57, 18.57], [72.87, 18.67]]
  },
  {
    cell_id: 'SC-LIVE-902',
    nearest_airport: 'Delhi',
    lon: 77.1025,
    lat: 28.7041,
    radius: 400,
    intensity: 0.9,
    lightning: 0.9,
    warning_level: 'RED',
    color: '#ef4444',
    max_dbz: 61,
    speed_kmh: 42,
    direction_deg: 90,
    compass: 'E',
    severity_score: 91,
    polygon: [[77.10, 29.10], [77.50, 28.70], [77.10, 28.30], [76.70, 28.70]],
    trajectory: [
      { lon: 77.2025, lat: 28.7041, time_offset: 15 },
      { lon: 77.3025, lat: 28.7041, time_offset: 30 },
      { lon: 77.4025, lat: 28.7041, time_offset: 45 },
      { lon: 77.5025, lat: 28.7041, time_offset: 60 }
    ],
    impact_zone: [[77.10, 29.10], [77.80, 29.20], [77.80, 28.20], [77.10, 28.30]]
  }
];

export function useLiveStorms(pollingIntervalMs = 15000) {
  const [liveStorms, setLiveStorms] = useState(FALLBACK_STORMS);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let isMounted = true;
    let isFetching = false;

    const fetchStorms = async () => {
      if (isFetching) return;
      isFetching = true;
      try {
        const res = await fetch('http://127.0.0.1:8000/api/multimodal/nowcast');
        if (!res.ok) throw new Error('Failed to fetch from backend');
        const data = await res.json();
        
        if (isMounted) {
          if (data.segmented_storm_cells) {
            let cells = data.segmented_storm_cells.map((c, i) => ({
              ...c,
              cell_id: c.cell_id || `SC-LIVE-${i}`,
              lon: c.centroid_lon,
              lat: c.centroid_lat,
              radius: Math.max(300, (c.pixel_count || 10) * 15), // Massive radius for zoomed out visibility
              intensity: Math.min(1.0, (c.max_dbz || 40) / 60.0),
              lightning: Math.min(1.0, (c.max_dbz || 40) / 65.0),
              warning_level: c.warning_level || 'ORANGE',
              color: c.warning_level === 'RED' ? '#ef4444' : (c.warning_level === 'ORANGE' ? '#f97316' : '#eab308'),
              max_dbz: c.max_dbz || 45,
              speed_kmh: c.speed_kmh || 45,
              direction_deg: c.direction_deg || 90,
              compass: c.compass || 'E',
              severity_score: Math.min(100, Math.round((c.max_dbz || 45) * 1.5))
            }));

            if (cells.length === 0) {
              cells = FALLBACK_STORMS;
            }
            setLiveStorms(cells);
          } else {
            setLiveStorms([]);
          }
          setLoading(false);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          console.error("Could not fetch real storm cells", err);
          setError(err);
          setLoading(false);
          setLiveStorms([]);
        }
      } finally {
        isFetching = false;
      }
    };

    fetchStorms();
    
    // Optional polling
    const interval = setInterval(fetchStorms, pollingIntervalMs);
    
    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [pollingIntervalMs]);

  return { liveStorms, loading, error };
}
