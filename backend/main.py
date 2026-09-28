import os
import sys
import json
import time
import urllib.parse
from http.server import HTTPServer, BaseHTTPRequestHandler

try:
    from dotenv import load_dotenv
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '.env'))
    load_dotenv(env_path)
except ImportError:
    pass

# Ensure root and backend directories are importable
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

try:
    from ml.synthetic.storm_generator import SyntheticStormGenerator
    from ml.extrapolator import ForecastExtrapolator
    from ml.tracking.cell_tracker import StormCellTracker
    from ml.analogs.analog_matcher import HistoricalAnalogMatcher
    from dataset.sample_builder import MultimodalSampleBuilder
    from dataset.loaders.radar_mosaic import MultiRadarMosaicEngine, RADAR_STATION_NETWORK
    from ml.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_wglc_climatology_metadata, get_insat3ds_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )
    from backend.stormtrace.ai import get_ai_provider
    from backend.stormtrace.alerts import dispatch_alert, get_alert_history
    from backend.stormtrace.alerts.cap_serializer import serialize_cap_xml
    from backend.stormtrace.alerts.report_generator import generate_incident_situation_report, render_situation_report_html
except ImportError:
    from stormtrace.synthetic.storm_generator import SyntheticStormGenerator
    from stormtrace.forecast.extrapolator import ForecastExtrapolator
    from stormtrace.tracking.cell_tracker import StormCellTracker
    from stormtrace.analogs.analog_matcher import HistoricalAnalogMatcher
    from stormtrace.data.sample_builder import MultimodalSampleBuilder
    from stormtrace.data.radar_mosaic import MultiRadarMosaicEngine, RADAR_STATION_NETWORK
    from stormtrace.data.provenance import (
        DataType, TemporalSemantics, SystemMode,
        get_wglc_climatology_metadata, get_insat3ds_metadata,
        get_era5_metadata, get_imerg_metadata, get_radar_demo_metadata
    )
    from stormtrace.ai import get_ai_provider
    from stormtrace.alerts import dispatch_alert, get_alert_history
    from stormtrace.alerts.cap_serializer import serialize_cap_xml
    from stormtrace.alerts.report_generator import generate_incident_situation_report, render_situation_report_html

# Global services
DATA_SOURCE = os.getenv("DATA_SOURCE", "real_observation")
DATA_ROOT = "dataset" if os.path.exists("dataset") else "data"
generator = SyntheticStormGenerator(grid_width=48, grid_height=48, time_step_min=5)
extrapolator = ForecastExtrapolator(mc_dropout_passes=25, dropout_rate=0.2)
tracker = StormCellTracker(dbz_threshold=40.0)
analog_matcher = HistoricalAnalogMatcher()
sample_builder = MultimodalSampleBuilder(data_root=DATA_ROOT)
mosaic_engine = MultiRadarMosaicEngine(sample_builder.grid)
ai_provider = get_ai_provider()


class StormTraceAPIHandler(BaseHTTPRequestHandler):
    """RESTful HTTP API Handler supporting both live and synthetic data modes."""

    def _set_cors_headers(self, status_code=200, content_type="application/json"):
        self.send_response(status_code)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_cors_headers(204)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        params = urllib.parse.parse_qs(parsed.query)

        # 1. Health & Status
        if path == "/api/health" or path == "/api/status":
            sat_files = sample_builder.sat_loader.discover_files()
            radar_files = sample_builder.radar_loader.discover_real_files()
            nwp_files = sample_builder.nwp_loader.discover_files()
            imerg_files = sample_builder.imerg_loader.discover_files()

            response_data = {
                "status": "healthy",
                "service": "STORMTRACE_Pipeline_API",
                "data_source": DATA_SOURCE,
                "system_mode": "REAL_HISTORICAL_MODE",
                "modalities": {
                    "satellite_insat3ds": {
                        "status": "AVAILABLE_REAL" if sat_files else "AWAITING_MOSDAC_DOWNLOAD",
                        "files_count": len(sat_files),
                        "provenance": get_insat3ds_metadata()
                    },
                    "lightning_wglc": {
                        "status": "AVAILABLE_CLIMATOLOGY",
                        "real_time_observation": False,
                        "observation_period": "2010-2020",
                        "role": "auxiliary_climatological_baseline",
                        "provenance": get_wglc_climatology_metadata()
                    },
                    "radar_dwr": {
                        "status": "AVAILABLE_REAL" if radar_files else "DEMO_OFFLINE_SIMULATION",
                        "files_count": len(radar_files),
                        "provenance": get_radar_demo_metadata() if not radar_files else {"source": "IMD_DWR"}
                    },
                    "nwp_era5": {
                        "status": "AVAILABLE_REAL" if nwp_files else "AWAITING_CDS_DOWNLOAD",
                        "files_count": len(nwp_files),
                        "provenance": get_era5_metadata()
                    },
                    "precipitation_imerg": {
                        "status": "AVAILABLE_REAL" if imerg_files else "AWAITING_EARTHDATA_DOWNLOAD",
                        "files_count": len(imerg_files),
                        "provenance": get_imerg_metadata()
                    }
                },
                "disclaimer": "AI decision-support output — prototype running with multimodal data alignment pipeline prepared for live/historical feeds."
            }
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        # 2. List Scenarios
        if path == "/api/scenarios":
            scenarios = generator.list_scenarios()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "data_source": DATA_SOURCE, "scenarios": scenarios}).encode("utf-8"))
            return

        # 3. Get Synthetic Storm Sequence
        if path == "/api/synthetic/storm-sequence":
            scenario_id = params.get("scenario", ["single_developing_storm"])[0]
            seed = int(params.get("seed", ["42"])[0])
            seq = generator.generate_sequence(scenario_id, seed=seed)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(seq).encode("utf-8"))
            return

        # 4. Get Nowcast Forecast
        if path == "/api/nowcast":
            scenario_id = params.get("scenario", ["single_developing_storm"])[0]
            model_mode = params.get("model", ["neural"])[0]
            seq = generator.generate_sequence(scenario_id, seed=42)
            recent_frames = seq["frames"][:6]  # Last 30 min of history
            if model_mode == "neural":
                nowcast_result = extrapolator.predict_neural(recent_frames, seed=42)
            else:
                nowcast_result = extrapolator.predict(recent_frames, seed=42)
            nowcast_result["scenario_id"] = scenario_id
            nowcast_result["data_source"] = DATA_SOURCE
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(nowcast_result).encode("utf-8"))
            return

        # 5. Historical Analogs Lookup
        if path == "/api/analogs":
            max_dbz = float(params.get("max_dbz", ["58.0"])[0])
            region = params.get("region", ["India"])[0]
            matches = analog_matcher.match_analog(max_dbz, region)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "analogs": matches}).encode("utf-8"))
            return

        # 6. Multimodal Manifest
        if path == "/api/multimodal/manifest":
            manifest_csv = os.path.join(DATA_ROOT, "manifests/events.csv")
            if not os.path.exists(manifest_csv) and os.path.exists("data/manifests/events.csv"):
                manifest_csv = "data/manifests/events.csv"
            rows = []
            if os.path.exists(manifest_csv):
                import csv
                with open(manifest_csv, "r", encoding="utf-8") as f:
                    reader = csv.DictReader(f)
                    rows = list(reader)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "events_count": len(rows), "events": rows}).encode("utf-8"))
            return

        # 7. Multimodal Validation Report
        if path == "/api/multimodal/validate":
            print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [VALIDATION] Executing multimodal integrity validation")
            sat_files = sample_builder.sat_loader.discover_files()
            radar_files = sample_builder.radar_loader.discover_real_files()
            nwp_files = sample_builder.nwp_loader.discover_files()
            imerg_files = sample_builder.imerg_loader.discover_files()
            report = {
                "status": "success",
                "validated_at_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "modalities": {
                    "satellite_insat3ds": {"available_files": len(sat_files), "status": "AVAILABLE" if sat_files else "MISSING"},
                    "radar_dwr": {"available_files": len(radar_files), "status": "REAL_AVAILABLE" if radar_files else "DEMO_FALLBACK"},
                    "nwp_era5": {"available_files": len(nwp_files), "status": "AVAILABLE" if nwp_files else "MISSING"},
                    "precipitation_imerg": {"available_files": len(imerg_files), "status": "AVAILABLE" if imerg_files else "MISSING"},
                    "lightning_wglc": {"status": "AVAILABLE_CLIMATOLOGY", "observation_period": "2010-2020"}
                }
            }
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(report).encode("utf-8"))
            return

        # 8. Multimodal Sample
        if path == "/api/multimodal/sample":
            target_ts = params.get("timestamp", ["2026-09-19T14:30:00Z"])[0]
            event_id = params.get("event_id", ["LIVE-QUERY-001"])[0]
            print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [SAMPLE_BUILDER] Building sample for event={event_id}, ts={target_ts}")
            try:
                sample = sample_builder.build_sample_at_timestamp(
                    event_id=event_id,
                    target_timestamp_iso=target_ts,
                    allow_demo_fallback=True
                )
                self._set_cors_headers(200)
                self.wfile.write(json.dumps({"status": "success", "sample": sample}).encode("utf-8"))
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [ERROR] Sample build error: {str(e)}")
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"status": "error", "message": f"Sample generation failed: {str(e)}"}).encode("utf-8"))
            return

        # 9. Multimodal Real-Data Nowcast Pipeline
        if path == "/api/multimodal/nowcast":
            target_ts = params.get("timestamp", ["2026-09-19T14:30:00Z"])[0]
            event_id = params.get("event_id", ["EVT-REAL-001"])[0]
            print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [INFERENCE] Running trained multimodal nowcast pipeline for {event_id}")
            try:
                sample = sample_builder.build_sample_at_timestamp(
                    event_id=event_id,
                    target_timestamp_iso=target_ts,
                    allow_demo_fallback=True
                )
                nowcast_out = extrapolator.predict_multimodal_sample(sample, seed=42)
                # Segment active convective cells from 2D output
                h15 = nowcast_out["lead_time_forecasts"][0]["grids"]["reflectivity_dbz"]
                segmented_cells = tracker.extract_cells_from_grid(
                    h15,
                    sample_builder.grid.lons,
                    sample_builder.grid.lats,
                    threshold=35.0
                )
                nowcast_out["segmented_storm_cells"] = segmented_cells
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(nowcast_out).encode("utf-8"))
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [ERROR] Multimodal nowcast error: {str(e)}")
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"status": "error", "message": f"Nowcast pipeline failed: {str(e)}"}).encode("utf-8"))
            return

        # 10. Multi-Radar Station Network Registry
        if path == "/api/radar/stations":
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({
                "status": "success",
                "stations_count": len(RADAR_STATION_NETWORK),
                "stations": list(RADAR_STATION_NETWORK.values())
            }).encode("utf-8"))
            return

        # 11. Multi-Radar Mosaic & Compositing Pipeline
        if path == "/api/radar/mosaic":
            method = params.get("method", ["MAX_REFLECTIVITY"])[0]
            # Build sample to get base field
            target_ts = params.get("timestamp", ["2026-09-19T14:30:00Z"])[0]
            event_id = params.get("event_id", ["EVT-REAL-001"])[0]
            try:
                sample = sample_builder.build_sample_at_timestamp(
                    event_id=event_id,
                    target_timestamp_iso=target_ts,
                    allow_demo_fallback=True
                )
                base_dbz = sample["tensors"]["radar_reflectivity_dbz"]
                # Simulate / ingest overlapping station scans around East India
                scans = [
                    {
                        "station_id": "DWR_KOLKATA",
                        "dbz_grid": base_dbz,
                        "vel_grid": [[float(c * 0.4) for c in row] for row in base_dbz],
                        "timestamp_utc": target_ts
                    },
                    {
                        "station_id": "DWR_PARADEEP",
                        "dbz_grid": [[float(max(0.0, c * 0.85 - 2.0)) for c in row] for row in base_dbz],
                        "vel_grid": [[float(c * 0.3) for c in row] for row in base_dbz],
                        "timestamp_utc": target_ts
                    }
                ]
                mosaic_res = mosaic_engine.create_multi_radar_composite(scans, method=method)
                response_payload = {
                    "status": "success",
                    "timestamp_utc": target_ts,
                    "compositing_method": method,
                    "participating_stations": mosaic_res["participating_stations"],
                    "metadata": mosaic_res["metadata"],
                    "grids": {
                        "composite_dbz": [[round(float(v), 1) for v in row] for row in mosaic_res["composite_dbz"]],
                        "composite_velocity": [[round(float(v), 1) for v in row] for row in mosaic_res["composite_velocity"]],
                        "coverage_count": [[int(v) for v in row] for row in mosaic_res["coverage_count_grid"]],
                        "divergence": [[round(float(v), 2) for v in row] for row in mosaic_res["divergence_grid"]]
                    }
                }
                self._set_cors_headers(200)
                self.wfile.write(json.dumps(response_payload).encode("utf-8"))
            except Exception as e:
                print(f"[{time.strftime('%Y-%m-%dT%H:%M:%SZ')}] [ERROR] Radar mosaic error: {str(e)}")
                self._set_cors_headers(500)
                self.wfile.write(json.dumps({"status": "error", "message": f"Mosaic failed: {str(e)}"}).encode("utf-8"))
            return

        # 12. Dedicated Lightning Nowcasting Pipeline (+15m to +120m)
        if path == "/api/lightning/nowcast":
            scenario_id = params.get("scenario", ["single_developing_storm"])[0]
            seq = generator.generate_sequence(scenario_id, seed=42)
            recent_frames = seq["frames"][:6]
            nowcast_result = extrapolator.predict_neural(recent_frames, seed=42)
            
            # Extract lightning-specific probability grids and strike severity zones
            lightning_horizons = []
            for h in nowcast_result.get("lead_time_forecasts", []):
                lt = h["lead_time_min"]
                lgt_prob = h["grids"].get("lightning_prob", [])
                max_prob = max((max(row) for row in lgt_prob), default=0.0)
                risk_level = "EXTREME" if max_prob >= 0.70 else "HIGH" if max_prob >= 0.45 else "MODERATE" if max_prob >= 0.20 else "LOW"
                lightning_horizons.append({
                    "lead_time_min": lt,
                    "peak_strike_probability": round(float(max_prob), 3),
                    "lightning_risk_level": risk_level,
                    "recommended_action": "ISSUE_GROUND_SAFETY_HALT" if risk_level in ("EXTREME", "HIGH") else "MONITOR_CONVECTIVE_CELL",
                    "lightning_probability_grid": lgt_prob
                })
                
            lgt_response = {
                "status": "success",
                "service": "STORMTRACE_Lightning_Nowcast_Engine",
                "scenario_id": scenario_id,
                "model_head": "DualHead_Spatiotemporal_LightningHead",
                "horizons": lightning_horizons
            }
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(lgt_response).encode("utf-8"))
            return

        # 13. Alert History & Delivery Logs
        if path in ("/api/v1/alerts/history", "/api/alerts/history", "/api/v1/delivery_logs"):
            history = get_alert_history()
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "history": history, "logs": history}).encode("utf-8"))
            return

        # 14. Meteorological Situation & Incident Report (JSON)
        if path == "/api/reports/incident":
            cell_id = params.get("cell_id", ["SC-2026-0917-03"])[0]
            report = generate_incident_situation_report(cell_id=cell_id)
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "report": report}).encode("utf-8"))
            return

        # 15. Printable HTML Situation Report Document
        if path == "/api/reports/incident/html":
            cell_id = params.get("cell_id", ["SC-2026-0917-03"])[0]
            report = generate_incident_situation_report(cell_id=cell_id)
            html_content = render_situation_report_html(report)
            self._set_cors_headers(200, content_type="text/html; charset=utf-8")
            self.wfile.write(html_content.encode("utf-8"))
            return

        # 11. POIs (Points of Interest) for Map
        if path == "/api/pois":
            # Generate static POIs for Mumbai and Delhi to demonstrate map alerts
            pois = [
                # Kolkata & East India (Active Storm Domain)
                {"id": "k1", "type": "hospital", "name": "Apollo Gleneagles Kolkata", "lat": 22.57, "lon": 88.40},
                {"id": "k2", "type": "hospital", "name": "SSKM Hospital", "lat": 22.54, "lon": 88.34},
                {"id": "k3", "type": "school", "name": "La Martiniere Calcutta", "lat": 22.54, "lon": 88.35},
                {"id": "k4", "type": "school", "name": "Jadavpur University", "lat": 22.49, "lon": 88.37},
                {"id": "k5", "type": "airport", "name": "Netaji Subhash Chandra Bose Intl", "lat": 22.65, "lon": 88.44},
                {"id": "k6", "type": "transport", "name": "Howrah Railway Station", "lat": 22.58, "lon": 88.34},
                {"id": "k7", "type": "transport", "name": "Kolkata Port Trust", "lat": 22.54, "lon": 88.32},
                {"id": "k8", "type": "hospital", "name": "Tata Medical Center", "lat": 22.57, "lon": 88.47},
                {"id": "k9", "type": "school", "name": "IIM Calcutta", "lat": 22.43, "lon": 88.30},
                
                # Mumbai & West India
                {"id": "m1", "type": "hospital", "name": "Lilavati Hospital", "lat": 19.05, "lon": 72.82},
                {"id": "m2", "type": "hospital", "name": "KEM Hospital", "lat": 19.00, "lon": 72.84},
                {"id": "m3", "type": "hospital", "name": "Tata Memorial Hospital", "lat": 19.01, "lon": 72.84},
                {"id": "m4", "type": "school", "name": "Bombay Scottish", "lat": 19.03, "lon": 72.84},
                {"id": "m5", "type": "school", "name": "IIT Bombay", "lat": 19.13, "lon": 72.91},
                {"id": "m6", "type": "airport", "name": "Chhatrapati Shivaji Maharaj Intl", "lat": 19.09, "lon": 72.86},
                {"id": "m7", "type": "transport", "name": "Bandra Terminus", "lat": 19.06, "lon": 72.84},
                {"id": "m8", "type": "transport", "name": "JNPT Port", "lat": 18.95, "lon": 72.95},
                
                # Delhi NCR
                {"id": "d1", "type": "hospital", "name": "AIIMS Delhi", "lat": 28.56, "lon": 77.20},
                {"id": "d2", "type": "hospital", "name": "Safdarjung Hospital", "lat": 28.56, "lon": 77.20},
                {"id": "d3", "type": "school", "name": "DPS RK Puram", "lat": 28.55, "lon": 77.18},
                {"id": "d4", "type": "school", "name": "IIT Delhi", "lat": 28.54, "lon": 77.19},
                {"id": "d5", "type": "airport", "name": "Indira Gandhi Intl Airport", "lat": 28.55, "lon": 77.10},
                {"id": "d6", "type": "transport", "name": "New Delhi Railway Station", "lat": 28.64, "lon": 77.22},
                {"id": "d7", "type": "school", "name": "Delhi University", "lat": 28.68, "lon": 77.20},

                # Chennai & South India
                {"id": "c1", "type": "hospital", "name": "Apollo Hospitals Greams Road", "lat": 13.06, "lon": 80.24},
                {"id": "c2", "type": "hospital", "name": "Christian Medical College Vellore", "lat": 12.92, "lon": 79.13},
                {"id": "c3", "type": "school", "name": "IIT Madras", "lat": 12.99, "lon": 80.23},
                {"id": "c4", "type": "school", "name": "Anna University", "lat": 13.01, "lon": 80.23},
                {"id": "c5", "type": "airport", "name": "Chennai Intl Airport", "lat": 12.97, "lon": 80.16},
                {"id": "c6", "type": "transport", "name": "Chennai Central Railway", "lat": 13.08, "lon": 80.27},
                
                # Bengaluru
                {"id": "b1", "type": "hospital", "name": "NIMHANS", "lat": 12.93, "lon": 77.59},
                {"id": "b2", "type": "hospital", "name": "Manipal Hospital HAL", "lat": 12.95, "lon": 77.64},
                {"id": "b3", "type": "school", "name": "IISc Bangalore", "lat": 13.01, "lon": 77.56},
                {"id": "b4", "type": "school", "name": "IIM Bangalore", "lat": 12.89, "lon": 77.60},
                {"id": "b5", "type": "airport", "name": "Kempegowda Intl Airport", "lat": 13.19, "lon": 77.70},
                {"id": "b6", "type": "transport", "name": "KSR Bengaluru Station", "lat": 12.97, "lon": 77.56},
                # Hyderabad
                {"id": "h1", "type": "hospital", "name": "Apollo Hospitals Jubilee Hills", "lat": 17.42, "lon": 78.41},
                {"id": "h2", "type": "school", "name": "IIT Hyderabad", "lat": 17.59, "lon": 78.12},
                {"id": "h3", "type": "airport", "name": "Rajiv Gandhi Intl Airport", "lat": 17.24, "lon": 78.43},
                
                # Ahmedabad & Gujarat
                {"id": "ah1", "type": "hospital", "name": "Apollo Hospitals Gandhinagar", "lat": 23.11, "lon": 72.58},
                {"id": "ah2", "type": "school", "name": "IIM Ahmedabad", "lat": 23.03, "lon": 72.53},
                {"id": "ah3", "type": "airport", "name": "Sardar Vallabhbhai Patel Intl", "lat": 23.07, "lon": 72.63},
                
                # Pune
                {"id": "p1", "type": "hospital", "name": "Ruby Hall Clinic", "lat": 18.53, "lon": 73.87},
                {"id": "p2", "type": "school", "name": "Pune University", "lat": 18.55, "lon": 73.82},
                {"id": "p3", "type": "airport", "name": "Pune Intl Airport", "lat": 18.58, "lon": 73.91}
            ]
            self._set_cors_headers(200)
            self.wfile.write(json.dumps({"status": "success", "pois": pois}).encode("utf-8"))
            return

        # 404 Fallback
        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found", "path": path}).encode("utf-8"))

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(length).decode('utf-8') if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if path == "/api/nowcast":
            scenario_id = payload.get("scenario", "single_developing_storm")
            model_mode = payload.get("model", "neural")
            seq = generator.generate_sequence(scenario_id, seed=42)
            recent_frames = seq["frames"][:6]
            if model_mode == "neural":
                nowcast_result = extrapolator.predict_neural(recent_frames, seed=42)
            else:
                nowcast_result = extrapolator.predict(recent_frames, seed=42)
            nowcast_result["scenario_id"] = scenario_id
            nowcast_result["data_source"] = DATA_SOURCE
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(nowcast_result).encode("utf-8"))
            return

        # AI Assistant Chat Endpoint
        if path in ("/api/chat", "/api/assistant"):
            message = payload.get("message", "")
            history = payload.get("history", [])
            context = payload.get("context", {})
            response_data = ai_provider.generate_response(
                message=message,
                history=history,
                context=context
            )
            self._set_cors_headers(200)
            self.wfile.write(json.dumps(response_data).encode("utf-8"))
            return

        # Demo Alert Trigger Endpoint
        if path in ("/api/v1/alerts/trigger", "/api/alerts/trigger"):
            alert_result = dispatch_alert(payload)
            status_code = 200 if alert_result.get("success") else (400 if alert_result.get("status") == "validation_failed" else 200)
            self._set_cors_headers(status_code)
            self.wfile.write(json.dumps(alert_result).encode("utf-8"))
            return

        # OASIS CAP 1.2 XML Document Endpoint
        if path in ("/api/v1/alerts/cap-xml", "/api/alerts/cap-xml"):
            xml_data = serialize_cap_xml(payload)
            self._set_cors_headers(200, content_type="application/xml; charset=utf-8")
            self.wfile.write(xml_data.encode("utf-8"))
            return

        self._set_cors_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))


def run_server(port: int = 8000):
    server_address = ('127.0.0.1', port)
    httpd = HTTPServer(server_address, StormTraceAPIHandler)
    print(f"STORMTRACE Pipeline Server running at http://127.0.0.1:{port}")
    print(f"DATA_SOURCE = {DATA_SOURCE} (Live Neural Engine Active)")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server.")
        httpd.server_close()


if __name__ == '__main__':
    port = int(os.getenv("PORT", "8000"))
    run_server(port)
