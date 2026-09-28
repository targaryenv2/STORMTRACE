import React, { useEffect, useRef, useState } from 'react';
import { useTranslation } from 'react-i18next';
import Map from 'ol/Map';
import View from 'ol/View';
import TileLayer from 'ol/layer/Tile';
import ImageLayer from 'ol/layer/Image';
import VectorLayer from 'ol/layer/Vector';
import XYZ from 'ol/source/XYZ';
import ImageCanvasSource from 'ol/source/ImageCanvas';
import VectorSource from 'ol/source/Vector';
import GeoJSON from 'ol/format/GeoJSON';
import { fromLonLat, toLonLat } from 'ol/proj';
import { Style, Fill, Stroke, Text, Circle as CircleStyle } from 'ol/style';
import Overlay from 'ol/Overlay';
import { 
  Plus, 
  Minus, 
  Crosshair, 
  Globe, 
  Search, 
  ChevronDown, 
  AlertCircle,
  Activity,
  Play,
  Pause,
  RotateCcw,
  Radio,
  Zap
} from 'lucide-react';
import TooltipHelper from '../Common/TooltipHelper';

// Built-in Geocoding Database for Fast Zero-Lag Searching
const GEO_LOCATIONS = [
  // India & South Asia (Operational Core)
  { name: 'India', lon: 82.5, lat: 22.0, zoom: 5.2, isIndia: true },
  { name: 'Tamil Nadu, India', lon: 78.6569, lat: 11.1271, zoom: 7.5, isIndia: true },
  { name: 'Chennai, Tamil Nadu, India', lon: 80.2707, lat: 13.0827, zoom: 8.5, isIndia: true },
  { name: 'Madurai, Tamil Nadu, India', lon: 78.1198, lat: 9.9252, zoom: 8.5, isIndia: true },
  { name: 'Coimbatore, Tamil Nadu, India', lon: 76.9558, lat: 11.0168, zoom: 8.5, isIndia: true },
  { name: 'Vellore, Tamil Nadu, India', lon: 79.1325, lat: 12.9165, zoom: 8.5, isIndia: true },
  { name: 'Salem, Tamil Nadu, India', lon: 78.1460, lat: 11.6643, zoom: 8.5, isIndia: true },
  { name: 'Tiruchirappalli, Tamil Nadu, India', lon: 78.7047, lat: 10.7905, zoom: 8.5, isIndia: true },
  { name: 'Kolkata, West Bengal, India', lon: 88.3639, lat: 22.5726, zoom: 8.5, isIndia: true },
  { name: 'Ranchi, Jharkhand, India', lon: 85.3096, lat: 23.3441, zoom: 8.5, isIndia: true },
  { name: 'Bhubaneswar, Odisha, India', lon: 85.8245, lat: 20.2961, zoom: 8.5, isIndia: true },
  { name: 'Patna, Bihar, India', lon: 85.1376, lat: 25.5941, zoom: 8.5, isIndia: true },
  { name: 'Delhi, India', lon: 77.1025, lat: 28.7041, zoom: 8.5, isIndia: true },
  { name: 'Mumbai, Maharashtra, India', lon: 72.8777, lat: 19.0760, zoom: 8.5, isIndia: true },
  { name: 'Bengaluru, Karnataka, India', lon: 77.5946, lat: 12.9716, zoom: 8.5, isIndia: true },
  { name: 'Kochi / Kerala, India', lon: 76.2673, lat: 9.9312, zoom: 8.5, isIndia: true },
  { name: 'Hyderabad, Telangana, India', lon: 78.4867, lat: 17.3850, zoom: 8.5, isIndia: true },
  { name: 'Visakhapatnam, Andhra Pradesh, India', lon: 83.2185, lat: 17.6868, zoom: 8.5, isIndia: true },
  { name: 'Guwahati, Assam, India', lon: 91.7362, lat: 26.1445, zoom: 8.5, isIndia: true },
  { name: 'Jaipur, Rajasthan, India', lon: 75.7873, lat: 26.9124, zoom: 8.5, isIndia: true },
  { name: 'Lucknow, Uttar Pradesh, India', lon: 80.9462, lat: 26.8467, zoom: 8.5, isIndia: true },
  { name: 'Ahmedabad, Gujarat, India', lon: 72.5714, lat: 23.0225, zoom: 8.5, isIndia: true },
  { name: 'Dhaka, Bangladesh', lon: 90.4125, lat: 23.8103, zoom: 7.5, isIndia: true },
  { name: 'Kathmandu, Nepal', lon: 85.3240, lat: 27.7172, zoom: 7.5, isIndia: true },
  { name: 'Colombo, Sri Lanka', lon: 79.8612, lat: 6.9271, zoom: 7.5, isIndia: true }
];

const LEAD_TIME_OPTIONS = [
  { value: 15, label: 'Last 15 min' },
  { value: 30, label: 'Last 30 min' },
  { value: 45, label: 'Last 45 min' },
  { value: 60, label: 'Last 60 min' },
  { value: 90, label: 'Last 90 min' },
  { value: 120, label: 'Last 120 min' }
];

export default function OpenLayersMap({
  activeLayer = 'thunderstorm',
  setActiveLayer,
  leadTimeMin = 30,
  setLeadTimeMin,
  showThunderstormProb = true,
  showCells = true,
  showTrajectories = true,
  showImpactZones = true,
  showUncertainty = false,
  selectedCellId = 'SC-2026-0917-03',
  onSelectCell = null,
  onRegionChange = null,
  mapTheme = 'light',
  fallbackMode = false,
  targetMapView = null,
  liveStorms = []
}) {
  const { t } = useTranslation();
  const mapRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const baseLayerRef = useRef(null);
  const rasterLayerRef = useRef(null);
  const cellsLayerRef = useRef(null);
  const trajectoriesLayerRef = useRef(null);
  const impactZonesLayerRef = useRef(null);
  const tooltipRef = useRef(null);

  const [tooltipContent, setTooltipContent] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [isWorldView, setIsWorldView] = useState(false);
  const [isIndiaRegion, setIsIndiaRegion] = useState(true);
  const [activeRegionLabel, setActiveRegionLabel] = useState('India');
  const [isTimelinePlaying, setIsTimelinePlaying] = useState(false);
  
  const liveCoresRef = useRef([]);

  // Automated Timeline Playback Loop (+15 to +120 min)
  useEffect(() => {
    let interval = null;
    if (isTimelinePlaying) {
      const horizons = [15, 30, 45, 60, 90, 120];
      interval = setInterval(() => {
        setLeadTimeMin((prev) => {
          const idx = horizons.indexOf(prev);
          const nextIdx = (idx + 1) % horizons.length;
          return horizons[nextIdx];
        });
      }, 1600);
    }
    return () => clearInterval(interval);
  }, [isTimelinePlaying, setLeadTimeMin]);

  // Sync prop to ref for canvas closure
  useEffect(() => {
    liveCoresRef.current = liveStorms;
    if (rasterLayerRef.current) {
      rasterLayerRef.current.getSource().changed();
    }
  }, [liveStorms]);
  // 1. Initialize OpenLayers Map Instance
  useEffect(() => {
    if (!mapRef.current || mapInstanceRef.current) return;

    // CARTO Basemap with secure API key (Voyager light theme by default)
    const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || 'cb1_3oas_2_0a7099b23629e50e2394ba21';
    const basemapStyle = mapTheme === 'dark' ? 'dark_all' : 'voyager';
    const cartoUrl = `https://basemaps.cartocdn.com/rastertiles/${basemapStyle}/{z}/{x}/{y}.png?key=${cartoApiKey}`;

    const baseLayer = new TileLayer({
      source: new XYZ({
        url: cartoUrl,
        attributions: '© OpenStreetMap contributors © CARTO',
        maxZoom: 19
      }),
      zIndex: 0
    });
    baseLayerRef.current = baseLayer;

    // 2. Physical Continuous Convective Raster Layer (Thunderstorm, Lightning, Radar, Satellite)
    const convectiveRasterSource = new ImageCanvasSource({
      canvasFunction: (extent, resolution, pixelRatio, size) => {
        const canvas = document.createElement('canvas');
        canvas.width = size[0];
        canvas.height = size[1];
        const ctx = canvas.getContext('2d');
        if (!ctx) return canvas;

        const [width, height] = size;

        // Lead-time advection shift (simulating physical movement eastward/southeastward)
        const advectionFactor = (leadTimeMin - 30) / 30;
        const dLon = advectionFactor * 0.35;
        const dLat = -advectionFactor * 0.18;
        const decayScale = Math.max(0.65, 1.0 - (leadTimeMin - 30) * 0.0035);

        // Fetch dynamic PyTorch cells instead of hardcoded demo coordinates
        const baseCores = liveCoresRef.current.length > 0 ? liveCoresRef.current.map(c => ({
          ...c,
          lon: c.lon + dLon,
          lat: c.lat + dLat,
          intensity: c.intensity * decayScale,
          lightning: c.lightning * decayScale
        })) : [];

        // Offscreen canvas for intensity gradient accumulation
        const offCanvas = document.createElement('canvas');
        offCanvas.width = width;
        offCanvas.height = height;
        const offCtx = offCanvas.getContext('2d');
        if (!offCtx) return canvas;

        baseCores.forEach(core => {
          const coord = fromLonLat([core.lon, core.lat]);
          const x = ((coord[0] - extent[0]) / resolution) * pixelRatio;
          const y = ((extent[3] - coord[1]) / resolution) * pixelRatio;
          const uncertaintyExpansion = showUncertainty ? 1.3 : 1.0;
          const r = ((core.radius / resolution) * 1000 * uncertaintyExpansion) * pixelRatio;

          if (x >= -r && x <= width + r && y >= -r && y <= height + r) {
            const radGrad = offCtx.createRadialGradient(x, y, 0, x, y, r);
            const val = activeLayer === 'lightning' ? core.lightning : core.intensity;
            radGrad.addColorStop(0, `rgba(0, 0, 0, ${val * 0.95})`);
            radGrad.addColorStop(0.35, `rgba(0, 0, 0, ${val * 0.70})`);
            radGrad.addColorStop(0.7, `rgba(0, 0, 0, ${val * 0.30})`);
            radGrad.addColorStop(1, 'rgba(0, 0, 0, 0)');

            offCtx.fillStyle = radGrad;
            offCtx.beginPath();
            offCtx.arc(x, y, r, 0, Math.PI * 2);
            offCtx.fill();
          }
        });

        // Color Mapping depending on activeLayer
        const imgData = offCtx.getImageData(0, 0, width, height);
        const data = imgData.data;

        const getLayerColor = (alpha) => {
          const norm = alpha / 255;
          if (norm < 0.08) return [0, 0, 0, 0];

          if (activeLayer === 'lightning') {
            // DISTINCT LIGHTNING COLORMAP: Violet -> Electric Magenta -> Amber -> High-Voltage White
            if (norm < 0.3) {
              const t = norm / 0.3;
              return [Math.round(88 + t * 40), Math.round(28 + t * 50), Math.round(135 + t * 80), Math.round(norm * 220)];
            } else if (norm < 0.6) {
              const t = (norm - 0.3) / 0.3;
              return [Math.round(140 + t * 90), Math.round(50 + t * 110), Math.round(220 - t * 40), Math.round(norm * 240)];
            } else if (norm < 0.85) {
              const t = (norm - 0.6) / 0.25;
              return [Math.round(230 + t * 20), Math.round(160 + t * 60), Math.round(30 + t * 40), 245];
            } else {
              const t = (norm - 0.85) / 0.15;
              return [255, Math.round(220 + t * 35), Math.round(70 + t * 185), 255];
            }
          } else if (activeLayer === 'radar') {
            // IMD DWR Reflectivity Scale (Blue -> Cyan -> Green -> Yellow -> Orange -> Red -> Pink)
            if (norm < 0.25) {
              return [59, 130, 246, Math.round(norm * 220)];
            } else if (norm < 0.45) {
              return [34, 197, 94, Math.round(norm * 230)];
            } else if (norm < 0.7) {
              return [234, 179, 8, Math.round(norm * 240)];
            } else if (norm < 0.88) {
              return [249, 115, 22, 245];
            } else {
              return [239, 68, 68, 255];
            }
          } else if (activeLayer === 'satellite') {
            // Thermal Infrared (TIR1) Cloud-Top Palette
            const v = Math.round(norm * 255);
            return [Math.round(v * 0.8 + 40), Math.round(v * 0.9 + 20), Math.min(255, v + 60), Math.round(norm * 230)];
          } else {
            // Thunderstorm Probability (Jet / Continuous Rainbow)
            let r = 0, g = 0, b = 0;
            if (norm < 0.25) {
              const t = norm / 0.25;
              r = Math.round(15 + t * (6 - 15));
              g = Math.round(58 + t * (182 - 58));
              b = Math.round(180 + t * (212 - 180));
            } else if (norm < 0.5) {
              const t = (norm - 0.25) / 0.25;
              r = Math.round(6 + t * (34 - 6));
              g = Math.round(182 + t * (197 - 182));
              b = Math.round(212 + t * (94 - 212));
            } else if (norm < 0.75) {
              const t = (norm - 0.5) / 0.25;
              r = Math.round(34 + t * (249 - 34));
              g = Math.round(197 + t * (115 - 197));
              b = Math.round(94 + t * (22 - 94));
            } else {
              const t = (norm - 0.75) / 0.25;
              r = Math.round(249 + t * (239 - 249));
              g = Math.round(115 + t * (68 - 115));
              b = Math.round(22 + t * (68 - 22));
            }
            return [r, g, b, Math.min(235, Math.round(norm * 245))];
          }
        };

        for (let i = 0; i < data.length; i += 4) {
          const a = data[i + 3];
          if (a > 12) {
            const [r, g, b, outAlpha] = getLayerColor(a);
            data[i] = r;
            data[i + 1] = g;
            data[i + 2] = b;
            data[i + 3] = outAlpha;
          } else {
            data[i + 3] = 0;
          }
        }

        ctx.putImageData(imgData, 0, 0);

        // Draw MC-Dropout Epistemic Uncertainty Confidence Bands
        if (showUncertainty) {
          ctx.save();
          baseCores.forEach(core => {
            const coord = fromLonLat([core.lon, core.lat]);
            const x = ((coord[0] - extent[0]) / resolution) * pixelRatio;
            const y = ((extent[3] - coord[1]) / resolution) * pixelRatio;
            const rOuter = ((core.radius / resolution) * 1000 * 1.35) * pixelRatio;
            const rInner = ((core.radius / resolution) * 1000 * 0.95) * pixelRatio;

            // Outer 90th percentile confidence contour (stippled indigo)
            ctx.strokeStyle = 'rgba(79, 70, 229, 0.85)';
            ctx.lineWidth = 2;
            ctx.setLineDash([6, 4]);
            ctx.beginPath();
            ctx.arc(x, y, rOuter, 0, Math.PI * 2);
            ctx.stroke();

            // Inner core boundary (subtle dashed rose)
            ctx.strokeStyle = 'rgba(225, 29, 72, 0.8)';
            ctx.lineWidth = 1.5;
            ctx.setLineDash([3, 4]);
            ctx.beginPath();
            ctx.arc(x, y, rInner, 0, Math.PI * 2);
            ctx.stroke();
          });
          ctx.restore();
        }

        return canvas;
      },
      projection: 'EPSG:3857',
      ratio: 1
    });

    const rasterLayer = new ImageLayer({
      source: convectiveRasterSource,
      opacity: 0.88,
      zIndex: 10
    });
    rasterLayerRef.current = rasterLayer;

    // 3. Impact Zones (Airports/Hospitals/Schools) Layer
    const impactZonesSource = new VectorSource();
    const impactZonesLayer = new VectorLayer({
      source: impactZonesSource,
      declutter: true,
      style: (feature) => {
        const props = feature.getProperties();
        const label = props.name || props.code || 'POI';
        const type = props.type || 'airport';
        
        let emoji = '✈';
        let bgColor = '#2563eb';
        let priorityZ = 3; // Airports get highest priority during decluttering
        
        if (type === 'hospital') { emoji = '🏥'; bgColor = '#dc2626'; priorityZ = 1; }
        else if (type === 'school') { emoji = '🏫'; bgColor = '#d97706'; priorityZ = 2; }
        else if (type === 'transport') { emoji = '🚆'; bgColor = '#16a34a'; priorityZ = 1; }

        return [
          new Style({
            image: new CircleStyle({
              radius: 9,
              fill: new Fill({ color: bgColor }),
              stroke: new Stroke({ color: '#ffffff', width: 2 })
            }),
            text: new Text({
              text: emoji,
              font: '10px sans-serif',
              fill: new Fill({ color: '#ffffff' }),
              offsetY: 0
            }),
            zIndex: priorityZ
          }),
          new Style({
            text: new Text({
              text: label,
              font: '600 10.5px Inter, sans-serif',
              fill: new Fill({ color: '#334155' }),
              stroke: new Stroke({ color: 'rgba(255, 255, 255, 0.95)', width: 3.5 }),
              offsetY: 15
            }),
            zIndex: priorityZ
          })
        ];
      },
      zIndex: 20
    });
    impactZonesLayerRef.current = impactZonesLayer;

    fetch('http://127.0.0.1:8000/api/pois')
      .then(r => r.json())
      .then(data => {
        if (data.status === 'success' && data.pois) {
          data.pois.forEach(zone => {
            const feat = new GeoJSON().readFeature({
              type: 'Feature',
              properties: zone,
              geometry: { type: 'Point', coordinates: fromLonLat([zone.lon, zone.lat]) }
            });
            impactZonesSource.addFeature(feat);
          });
        }
      })
      .catch(err => console.error("Could not load POIs from backend", err));


    // 4. Trajectories Vector Layer (Dashed direction vectors)
    const trajectoriesSource = new VectorSource();
    const trajectoriesLayer = new VectorLayer({
      source: trajectoriesSource,
      style: new Style({
        stroke: new Stroke({
          color: '#eab308',
          width: 2.5,
          lineDash: [6, 4]
        }),
        image: new CircleStyle({
          radius: 4,
          fill: new Fill({ color: '#eab308' }),
          stroke: new Stroke({ color: '#713f12', width: 1.5 })
        })
      }),
      zIndex: 25
    });
    trajectoriesLayerRef.current = trajectoriesLayer;

    // Trajectory features are populated dynamically below


    // 5. Storm Cell Polygons Layer
    const cellsSource = new VectorSource();
    const cellsLayer = new VectorLayer({
      source: cellsSource,
      style: (feature) => {
        const props = feature.getProperties();
        const isSelected = props.cell_id === selectedCellId && !props.is_zone;
        const color = props.customStroke || props.color || '#ef4444';
        const fillColor = props.customColor || (isSelected ? 'rgba(239, 68, 68, 0.25)' : 'rgba(255, 255, 255, 0.15)');

        return new Style({
          fill: new Fill({
            color: fillColor
          }),
          stroke: new Stroke({
            color: isSelected ? '#1e293b' : color,
            width: isSelected ? 3.0 : 2.0
          }),
          image: new CircleStyle({
            radius: 5,
            fill: new Fill({ color: color }),
            stroke: new Stroke({ color: '#ffffff', width: 1.5 })
          })
        });
      },
      zIndex: 30
    });
    cellsLayerRef.current = cellsLayer;

    const defaultCells = [
      {
        cell_id: 'SC-2026-0917-03',
        warning_level: 'RED',
        color: '#ef4444',
        max_dbz: 58,
        speed_kmh: 46,
        coords: [
          [86.4, 23.7], [87.0, 23.9], [87.5, 23.6], [87.7, 23.1], 
          [87.3, 22.7], [86.7, 22.9], [86.4, 23.7]
        ]
      },
      {
        cell_id: 'SC-2026-0917-01',
        warning_level: 'RED',
        color: '#ef4444',
        max_dbz: 61,
        speed_kmh: 52,
        coords: [
          [84.8, 23.6], [85.5, 23.7], [85.8, 23.2], [85.2, 23.0], 
          [84.8, 23.6]
        ]
      },
      {
        cell_id: 'SC-2026-0917-02',
        warning_level: 'ORANGE',
        color: '#f97316',
        max_dbz: 52,
        speed_kmh: 38,
        coords: [
          [85.1, 21.9], [85.7, 22.1], [86.1, 21.7], [85.9, 21.2], 
          [85.3, 21.1], [84.9, 21.5], [85.1, 21.9]
        ]
      },
      {
        cell_id: 'SC-2026-0917-05',
        warning_level: 'YELLOW',
        color: '#eab308',
        max_dbz: 46,
        speed_kmh: 32,
        coords: [
          [80.0, 13.2], [80.4, 13.3], [80.6, 13.0], [80.2, 12.9], [80.0, 13.2]
        ]
      },
      {
        cell_id: 'SC-2026-0917-07',
        warning_level: 'ORANGE',
        color: '#f97316',
        max_dbz: 53,
        speed_kmh: 40,
        coords: [
          [77.9, 11.1], [78.4, 11.2], [78.6, 10.8], [78.0, 10.7], [77.9, 11.1]
        ]
      },
      {
        cell_id: 'SC-2026-0917-08',
        warning_level: 'RED',
        color: '#ef4444',
        max_dbz: 59,
        speed_kmh: 48,
        coords: [
          [-46.9, -23.3], [-46.3, -23.4], [-46.2, -23.8], [-46.8, -23.7], [-46.9, -23.3]
        ]
      },
      {
        cell_id: 'SC-2026-0917-09',
        warning_level: 'RED',
        color: '#ef4444',
        max_dbz: 62,
        speed_kmh: 42,
        coords: [
          [-60.5, -2.8], [-59.7, -2.9], [-59.6, -3.4], [-60.4, -3.3], [-60.5, -2.8]
        ]
      },
      {
        cell_id: 'SC-2026-0917-10',
        warning_level: 'ORANGE',
        color: '#f97316',
        max_dbz: 54,
        speed_kmh: 38,
        coords: [
          [55.0, 25.4], [55.5, 25.4], [55.6, 25.0], [55.1, 25.0], [55.0, 25.4]
        ]
      },
      {
        cell_id: 'SC-2026-0917-11',
        warning_level: 'ORANGE',
        color: '#f97316',
        max_dbz: 55,
        speed_kmh: 35,
        coords: [
          [-81.7, 28.7], [-81.1, 28.8], [-81.0, 28.3], [-81.6, 28.3], [-81.7, 28.7]
        ]
      },
      {
        cell_id: 'SC-2026-0917-14',
        warning_level: 'ORANGE',
        color: '#f97316',
        max_dbz: 53,
        speed_kmh: 36,
        coords: [
          [106.6, -6.0], [107.1, -6.1], [107.0, -6.4], [106.5, -6.3], [106.6, -6.0]
        ]
      }
    ];
    // Cell features are populated dynamically below


    // Create Map
    const map = new Map({
      target: mapRef.current,
      layers: [baseLayer, rasterLayer, impactZonesLayer, trajectoriesLayer, cellsLayer],
      view: new View({
        center: fromLonLat([82.5, 22.0]), // India focus
        zoom: 5.2,
        minZoom: 2,
        maxZoom: 16
      }),
      controls: []
    });

    // Tooltip Overlay
    const overlay = new Overlay({
      element: tooltipRef.current,
      positioning: 'bottom-center',
      stopEvent: false,
      offset: [0, -12]
    });
    map.addOverlay(overlay);

    // Viewport change listener to detect Region / Country bounds
    map.on('moveend', () => {
      const view = map.getView();
      const centerCoords = toLonLat(view.getCenter());
      const lon = centerCoords[0];
      const lat = centerCoords[1];

      // Check if within India geographic bounding polygon
      const inIndia = lon >= 66.0 && lon <= 98.0 && lat >= 6.0 && lat <= 36.5;
      setIsIndiaRegion(inIndia);

      if (onRegionChange) {
        onRegionChange({
          lon,
          lat,
          isIndia: inIndia,
          regionName: inIndia ? 'India' : 'Global'
        });
      }
    });

    // Hover Interaction
    map.on('pointermove', (evt) => {
      const pixel = map.getEventPixel(evt.originalEvent);
      const hit = map.hasFeatureAtPixel(pixel);
      map.getTargetElement().style.cursor = hit ? 'pointer' : '';

      if (hit) {
        const feature = map.forEachFeatureAtPixel(pixel, (f) => f);
        if (feature) {
          const props = feature.getProperties();
          if (props.cell_id) {
            setTooltipContent({
              title: props.cell_id,
              subtitle: `Max: ${props.max_dbz} dBZ · Speed: ${props.speed_kmh} km/h`,
              type: 'cell'
            });
            overlay.setPosition(evt.coordinate);
            return;
          } else if (props.code) {
            setTooltipContent({
              title: props.name,
              subtitle: `Airport Code: ${props.code}`,
              type: 'airport'
            });
            overlay.setPosition(evt.coordinate);
            return;
          }
        }
      }
      setTooltipContent(null);
      overlay.setPosition(undefined);
    });

    // Click to select cell
    map.on('singleclick', (evt) => {
      const feature = map.forEachFeatureAtPixel(evt.pixel, (f) => f);
      if (feature) {
        const props = feature.getProperties();
        if (props.cell_id && onSelectCell) {
          onSelectCell(props.cell_id);
        }
      }
    });

    mapInstanceRef.current = map;

    return () => {
      map.setTarget(null);
      mapInstanceRef.current = null;
    };
  }, []);

  // Update vectors when live data arrives
  useEffect(() => {
    if (!trajectoriesLayerRef.current || !cellsLayerRef.current) return;
    
    const tSource = trajectoriesLayerRef.current.getSource();
    const cSource = cellsLayerRef.current.getSource();
    
    tSource.clear();
    cSource.clear();
    
    // Populate Trajectories
    liveStorms.forEach(c => {
      let coords;
      if (c.trajectory && Array.isArray(c.trajectory) && c.trajectory.length > 0) {
        coords = [fromLonLat([c.lon, c.lat]), ...c.trajectory.map(pt => fromLonLat([pt.lon, pt.lat]))];
      } else {
        const len = (c.speed_kmh || 40) / 100.0;
        coords = [
          fromLonLat([c.lon, c.lat]),
          fromLonLat([c.lon + len, c.lat - (len / 2)])
        ];
      }

      const feat = new GeoJSON().readFeature({
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: coords
        }
      });
      tSource.addFeature(feat);
    });
    
    // Populate transparent interaction cores for tooltip hover
    liveStorms.forEach((core, i) => {
      const generateCoreCircle = (lon, lat, r) => {
        const pts = [];
        for (let a = 0; a <= 360; a += 15) {
          const rad = (a * Math.PI) / 180;
          pts.push([lon + r * Math.cos(rad), lat + r * Math.sin(rad)]);
        }
        return [pts];
      };

      const cellProps = {
        cell_id: core.cell_id || `SC-LIVE-${i}`,
        warning_level: core.warning_level || 'ORANGE',
        max_dbz: core.max_dbz || 45,
        speed_kmh: core.speed_kmh || 30,
        color: 'transparent',
        customColor: 'transparent',
        customStroke: 'transparent'
      };

      const feat = new GeoJSON().readFeature({
        type: 'Feature',
        properties: cellProps,
        geometry: {
          type: 'Polygon',
          coordinates: generateCoreCircle(core.lon, core.lat, 0.4) // interaction radius
        }
      }, {
        dataProjection: 'EPSG:4326',
        featureProjection: 'EPSG:3857'
      });
      cSource.addFeature(feat);
    });
  }, [liveStorms]);

  // Update basemap tile URL if theme changes in Settings
  useEffect(() => {
    if (!baseLayerRef.current) return;
    const cartoApiKey = import.meta.env.VITE_CARTO_API_KEY || 'cb1_3oas_2_0a7099b23629e50e2394ba21';
    const basemapStyle = mapTheme === 'dark' ? 'dark_all' : 'voyager';
    const cartoUrl = `https://basemaps.cartocdn.com/rastertiles/${basemapStyle}/{z}/{x}/{y}.png?key=${cartoApiKey}`;
    baseLayerRef.current.getSource().setUrl(cartoUrl);
  }, [mapTheme]);

  // Handle external animated map view changes (from AI Assistant or search)
  useEffect(() => {
    if (!mapInstanceRef.current || !targetMapView) return;
    const view = mapInstanceRef.current.getView();
    view.animate({
      center: fromLonLat([targetMapView.lon, targetMapView.lat]),
      zoom: targetMapView.zoom || 8.0,
      duration: 400
    });
  }, [targetMapView]);

  // Update layer parameters on layer switch or lead time change
  useEffect(() => {
    if (rasterLayerRef.current) {
      rasterLayerRef.current.getSource().changed();
    }
  }, [activeLayer, leadTimeMin, showUncertainty]);

  // Update Layer Visibilities
  useEffect(() => {
    if (rasterLayerRef.current) rasterLayerRef.current.setVisible(showThunderstormProb);
    if (cellsLayerRef.current) cellsLayerRef.current.setVisible(showCells);
    if (trajectoriesLayerRef.current) trajectoriesLayerRef.current.setVisible(showTrajectories);
    if (impactZonesLayerRef.current) impactZonesLayerRef.current.setVisible(showImpactZones);
  }, [showThunderstormProb, showCells, showTrajectories, showImpactZones]);

  // Search input handler
  const handleSearchChange = (e) => {
    const q = e.target.value;
    setSearchQuery(q);
    if (q.trim().length > 1) {
      const matches = GEO_LOCATIONS.filter(loc => 
        loc.name.toLowerCase().includes(q.toLowerCase())
      );
      setSearchResults(matches);
      setIsSearchOpen(true);
    } else {
      setSearchResults([]);
      setIsSearchOpen(false);
    }
  };

  const handleSelectLocation = (loc) => {
    setSearchQuery(loc.name);
    setIsSearchOpen(false);
    setIsIndiaRegion(loc.isIndia);
    setActiveRegionLabel(loc.name);

    if (mapInstanceRef.current) {
      const view = mapInstanceRef.current.getView();
      view.animate({
        center: fromLonLat([loc.lon, loc.lat]),
        zoom: loc.zoom || 7.0,
        duration: 400
      });
    }

    if (onRegionChange) {
      onRegionChange({
        lon: loc.lon,
        lat: loc.lat,
        isIndia: loc.isIndia,
        regionName: loc.name
      });
    }
  };

  // World View Toggle
  const handleToggleWorldView = () => {
    if (!mapInstanceRef.current) return;
    const view = mapInstanceRef.current.getView();
    if (!isWorldView) {
      view.animate({
        center: fromLonLat([20.0, 20.0]),
        zoom: 2.2,
        duration: 450
      });
      setIsWorldView(true);
      setActiveRegionLabel('Global View');
    } else {
      view.animate({
        center: fromLonLat([82.5, 22.0]),
        zoom: 5.2,
        duration: 450
      });
      setIsWorldView(false);
      setIsIndiaRegion(true);
      setActiveRegionLabel('India');
    }
  };

  // Recenter on India Convective Corridor
  const handleRecenter = () => {
    if (!mapInstanceRef.current) return;
    const view = mapInstanceRef.current.getView();
    view.animate({
      center: fromLonLat([86.8, 22.8]),
      zoom: 6.5,
      duration: 350
    });
    setIsWorldView(false);
    setIsIndiaRegion(true);
    setActiveRegionLabel('India');
  };

  return (
    <div className="relative w-full h-full bg-[#e2e8f0] overflow-hidden select-none">
      {/* Map Canvas */}
      <div ref={mapRef} className="w-full h-full" />

      {/* 1. Top Toolbar: Layer Tabs + Lead Time + Geocoded Search + World View Toggle */}
      <div className="absolute top-3.5 left-4 right-4 z-20 flex flex-wrap items-center justify-between gap-2 pointer-events-none">
        {/* Left: 4 Layer Tab Pills */}
        <div className="flex items-center space-x-1.5 bg-white/95 p-1 rounded-2xl border border-slate-200/90 shadow-sm backdrop-blur-md pointer-events-auto">
          <button
            onClick={() => setActiveLayer('thunderstorm')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
              activeLayer === 'thunderstorm'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
            title="AI Convective Nowcast Probability"
          >
            Thunderstorm Nowcast
          </button>

          <button
            onClick={() => setActiveLayer('radar')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
              activeLayer === 'radar'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
            title="Multi-Radar DWR Composite Mosaic"
          >
            Multi-Radar Mosaic (9 DWR)
          </button>

          <button
            onClick={() => setActiveLayer('lightning')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
              activeLayer === 'lightning'
                ? 'bg-purple-600 text-white shadow-sm'
                : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
            title="Dedicated Lightning Strike Probability Footprint"
          >
            <span className="flex items-center space-x-1">
              <Zap className="w-3 h-3 text-amber-400 fill-amber-400" />
              <span>Lightning Footprint</span>
            </span>
          </button>

          <button
            onClick={() => setActiveLayer('satellite')}
            className={`px-3.5 py-1.5 rounded-xl text-xs font-semibold transition ${
              activeLayer === 'satellite'
                ? 'bg-blue-600 text-white shadow-sm'
                : 'text-slate-700 hover:text-slate-900 hover:bg-slate-100/80'
            }`}
            title="INSAT-3DS Asia Infrared / Water Vapor Channel"
          >
            INSAT-3DS Satellite
          </button>
        </div>

        {/* Right: Lead Time Select + Geocoded Search + Recenter + Zoom World/Regional */}
        <div className="flex items-center space-x-2 pointer-events-auto">
          {/* Lead-Time Dropdown */}
          <div className="relative">
            <select
              value={leadTimeMin}
              onChange={(e) => setLeadTimeMin(Number(e.target.value))}
              className="appearance-none bg-white/95 text-slate-800 text-xs font-semibold px-3.5 py-2 pr-8 rounded-2xl border border-slate-200/90 shadow-sm backdrop-blur-md outline-none cursor-pointer hover:border-slate-300 transition"
            >
              {LEAD_TIME_OPTIONS.map(opt => (
                <option key={opt.value} value={opt.value} className="bg-white text-slate-800">
                  {opt.value === 15 ? t('map.last15min') :
                   opt.value === 30 ? t('map.last30min') :
                   opt.value === 45 ? t('map.last45min') :
                   opt.value === 60 ? t('map.last60min') :
                   opt.value === 90 ? t('map.last90min') :
                   t('map.last120min')}
                </option>
              ))}
            </select>
            <ChevronDown className="w-3.5 h-3.5 text-slate-500 absolute right-2.5 top-1/2 -translate-y-1/2 pointer-events-none" />
          </div>

          {/* Search Box */}
          <div className="relative">
            <div className="flex items-center bg-white/95 border border-slate-200/90 rounded-2xl px-3.5 py-2 shadow-sm backdrop-blur-md w-56 md:w-64">
              <Search className="w-3.5 h-3.5 text-slate-400 mr-2 shrink-0" />
              <input
                type="text"
                placeholder={t('map.searchPlaceholder')}
                value={searchQuery}
                onChange={handleSearchChange}
                onFocus={() => searchQuery.length > 1 && setIsSearchOpen(true)}
                className="bg-transparent text-xs text-slate-800 placeholder-slate-400 outline-none w-full font-medium"
              />
            </div>

            {/* Geocode Search Results Dropdown */}
            {isSearchOpen && searchResults.length > 0 && (
              <div className="absolute top-full mt-1.5 left-0 w-full bg-white border border-slate-200 rounded-2xl shadow-xl py-1.5 text-xs z-50 max-h-52 overflow-y-auto">
                {searchResults.map((loc, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSelectLocation(loc)}
                    className="w-full text-left px-3.5 py-2 hover:bg-slate-50 flex items-center justify-between text-slate-800 transition"
                  >
                    <span className="truncate font-medium">{loc.name}</span>
                    <span className={`text-[10px] px-1.5 py-0.2 rounded font-mono font-semibold ${
                      loc.isIndia ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' : 'bg-slate-100 text-slate-500'
                    }`}>
                      {loc.isIndia ? t('map.fullRadar') : t('map.satellite')}
                    </span>
                  </button>
                ))}
              </div>
            )}
          </div>

          {/* Recenter Button */}
          <button
            onClick={handleRecenter}
            className="p-2 bg-white/95 border border-slate-200/90 rounded-2xl text-slate-600 hover:text-slate-900 hover:bg-slate-50 shadow-sm backdrop-blur-md transition"
            title={t('map.recenter')}
          >
            <Crosshair className="w-4 h-4" />
          </button>

          {/* Camera Zoom Toggle Button (World / Regional) */}
          <button
            onClick={handleToggleWorldView}
            className="flex items-center space-x-1.5 px-3.5 py-2 rounded-2xl text-xs font-semibold shadow-sm backdrop-blur-md bg-blue-600 text-white hover:bg-blue-700 transition"
            title="Toggle camera view"
          >
            <Globe className="w-3.5 h-3.5" />
            <span>{isWorldView ? t('map.zoomRegional') : t('map.zoomWorld')}</span>
          </button>
        </div>
      </div>

      {/* 2. Honest Region Coverage Notice (Visible when navigated outside India) */}
      {!isIndiaRegion && (
        <div className="absolute top-16 left-1/2 -translate-x-1/2 z-20 bg-amber-50/95 border border-amber-300 px-4 py-2.5 rounded-2xl shadow-lg backdrop-blur-md flex items-center space-x-2.5 text-xs text-amber-900 max-w-lg">
          <AlertCircle className="w-4 h-4 text-amber-600 shrink-0" />
          <div>
            <span className="font-bold text-amber-900">{t('map.limitedCoverage')} ({activeRegionLabel}):</span>{' '}
            <span className="text-amber-800 text-[11px]">
              {t('map.coverageExplanation')}
            </span>
          </div>
        </div>
      )}

      {/* 3. Degraded Fallback Mode Pill (if active) */}
      {fallbackMode && (
        <div className="absolute top-16 right-4 z-20 bg-rose-50 border border-rose-300 px-3 py-1.5 rounded-xl shadow-md text-[11px] text-rose-800 flex items-center space-x-2">
          <Activity className="w-3.5 h-3.5 text-rose-600 animate-pulse" />
          <span className="font-semibold">Mode: XGBoost Fallback (Radar Offline)</span>
        </div>
      )}

      {/* 4. Zoom Controls & Scale Bar (Bottom-Left) */}
      <div className="absolute bottom-6 left-6 z-20 flex flex-col space-y-2">
        <div className="bg-white border border-slate-200 rounded-2xl overflow-hidden shadow-sm backdrop-blur-md flex flex-col">
          <button
            onClick={() => {
              if (!mapInstanceRef.current) return;
              const v = mapInstanceRef.current.getView();
              v.animate({ zoom: (v.getZoom() || 5.2) + 0.6, duration: 200 });
            }}
            className="p-2.5 text-slate-700 hover:text-slate-900 hover:bg-slate-50 border-b border-slate-100 transition"
            title={t('map.zoomIn')}
          >
            <Plus className="w-4 h-4" />
          </button>
          <button
            onClick={() => {
              if (!mapInstanceRef.current) return;
              const v = mapInstanceRef.current.getView();
              v.animate({ zoom: (v.getZoom() || 5.2) - 0.6, duration: 200 });
            }}
            className="p-2.5 text-slate-700 hover:text-slate-900 hover:bg-slate-50 transition"
            title={t('map.zoomOut')}
          >
            <Minus className="w-4 h-4" />
          </button>
        </div>

        <button
          onClick={handleRecenter}
          className="p-2.5 bg-white border border-slate-200 rounded-2xl text-slate-700 hover:text-slate-900 hover:bg-slate-50 shadow-sm backdrop-blur-md transition"
          title={t('map.recenter')}
        >
          <Crosshair className="w-4 h-4" />
        </button>

        <div className="bg-white border border-slate-200 px-3 py-1 rounded-xl text-[11px] font-mono font-bold text-slate-700 shadow-sm w-fit">
          500 km
        </div>
      </div>

      {/* 5. Center Bottom: Forecast Timeline Playback Controller */}
      <div className="absolute bottom-6 left-1/2 -translate-x-1/2 z-20 bg-white/95 border border-slate-200 px-4 py-2 rounded-2xl shadow-xl backdrop-blur-md flex items-center space-x-3 text-xs select-none">
        <button
          onClick={() => setIsTimelinePlaying(!isTimelinePlaying)}
          className={`px-3 py-1.5 rounded-xl font-bold flex items-center space-x-1.5 transition ${
            isTimelinePlaying
              ? 'bg-amber-500 text-white shadow-sm'
              : 'bg-blue-600 text-white hover:bg-blue-700 shadow-sm'
          }`}
          title="Toggle automated nowcast timeline animation"
        >
          {isTimelinePlaying ? <Pause className="w-3.5 h-3.5" /> : <Play className="w-3.5 h-3.5" />}
          <span>{isTimelinePlaying ? 'Pause' : 'Play Timeline'}</span>
        </button>

        <div className="flex items-center space-x-1 bg-slate-100 p-1 rounded-xl">
          {[15, 30, 45, 60, 90, 120].map((h) => {
            const isActive = leadTimeMin === h;
            return (
              <button
                key={h}
                onClick={() => setLeadTimeMin(h)}
                className={`px-2.5 py-1 rounded-lg text-xs font-bold transition ${
                  isActive
                    ? 'bg-blue-600 text-white shadow-sm scale-105'
                    : 'text-slate-600 hover:text-slate-900'
                }`}
              >
                +{h}m
              </button>
            );
          })}
        </div>
      </div>

      {/* 6. Dynamic Legend Box (Bottom-Right) */}
      <div className="absolute bottom-6 right-6 z-20 bg-white/95 border border-slate-200 p-3.5 rounded-2xl shadow-lg backdrop-blur-md text-xs select-none min-w-[250px]">
        <div className="flex items-center justify-between font-bold text-slate-800 text-xs mb-1.5">
          <span>
            {activeLayer === 'lightning' ? t('map.legendLightning') :
             activeLayer === 'radar' ? t('map.legendRadar') :
             activeLayer === 'satellite' ? t('map.legendSatellite') :
             t('map.legendThunderstorm')}
          </span>
          <TooltipHelper
            title="Colormap Legend"
            text={
              activeLayer === 'lightning' ? 'Probability of cloud-to-ground lightning flashes within the grid cell.' :
              activeLayer === 'radar' ? 'Radar reflectivity in dBZ — higher dBZ values correlate to intense rainfall and hail.' :
              'Model-predicted convective probability from 0.0 (low) to 1.0 (extreme).'
            }
          />
        </div>

        {/* Dynamic Gradient Bar */}
        {activeLayer === 'lightning' ? (
          <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#4c1d95] via-[#a855f7] via-[#eab308] to-[#ffffff] border border-slate-200/60" />
        ) : activeLayer === 'radar' ? (
          <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#3b82f6] via-[#22c55e] via-[#eab308] via-[#f97316] to-[#ef4444] border border-slate-200/60" />
        ) : activeLayer === 'satellite' ? (
          <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#1e293b] via-[#475569] via-[#06b6d4] to-[#f8fafc] border border-slate-200/60" />
        ) : (
          <div className="h-3 w-full rounded-md bg-gradient-to-r from-[#1e40af] via-[#06b6d4] via-[#22c55e] via-[#eab308] via-[#f97316] to-[#ef4444] border border-slate-200/60" />
        )}

        {/* Tick Labels */}
        <div className="flex justify-between text-[10px] font-mono font-semibold text-slate-600 mt-1">
          {activeLayer === 'radar' ? (
            <><span>5</span><span>20</span><span>35</span><span>50</span><span>65</span><span>75+ dBZ</span></>
          ) : activeLayer === 'satellite' ? (
            <><span>+20°C</span><span>0°C</span><span>-20°C</span><span>-40°C</span><span>-60°C</span><span>-80°C</span></>
          ) : (
            <><span>0</span><span>0.2</span><span>0.4</span><span>0.6</span><span>0.8</span><span>1.0</span></>
          )}
        </div>

        {/* Epistemic Uncertainty Badge */}
        {showUncertainty && (
          <div className="mt-2.5 p-2 bg-indigo-50 border border-indigo-200/80 rounded-xl flex items-center justify-between text-[11px] text-indigo-900">
            <span className="font-semibold flex items-center space-x-1">
              <span className="w-2 h-2 rounded-full bg-indigo-600 animate-pulse inline-block mr-1" />
              {t('map.mcDropoutBand')}
            </span>
            <span className="font-mono font-bold text-indigo-700">{t('map.spread')}</span>
          </div>
        )}

        {/* Attribution line */}
        <div className="mt-2 pt-2 border-t border-slate-100 flex items-center justify-between text-[10px] text-slate-400">
          <span>{t('map.attribution')}</span>
        </div>
      </div>

      {/* Tooltip Overlay */}
      <div
        ref={tooltipRef}
        className={`pointer-events-none transition-opacity duration-150 ${
          tooltipContent ? 'opacity-100' : 'opacity-0 hidden'
        }`}
      >
        {tooltipContent && (
          <div className="bg-slate-900/95 border border-slate-700 px-3 py-1.5 rounded-xl shadow-2xl backdrop-blur-md text-xs text-slate-100">
            <div className="font-bold text-sky-400">{tooltipContent.title}</div>
            <div className="text-[11px] text-slate-300">{tooltipContent.subtitle}</div>
          </div>
        )}
      </div>
    </div>
  );
}
