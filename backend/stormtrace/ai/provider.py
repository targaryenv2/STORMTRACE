"""STORMTRACE AI Assistant Provider Interface and Factory."""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import os

from .scope_guard import classify_project_scope, SCOPE_REFUSAL_MESSAGE


class AIProvider(ABC):
    """Abstract base class for AI Assistant providers."""

    @abstractmethod
    def generate_response(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate response given a user message, optional conversation history and context."""
        pass


class LocalFallbackProvider(AIProvider):
    """Deterministic fallback provider when external LLM is offline or unconfigured."""

    def __init__(self, disclaimer: str = "This is AI decision-support, not an official IMD warning."):
        self.disclaimer = disclaimer

    def generate_response(
        self,
        message: str,
        history: Optional[List[Dict[str, Any]]] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        # 1. Strict Scope Check
        category, is_project_related = classify_project_scope(message)
        if not is_project_related:
            return {
                "status": "success",
                "reply": SCOPE_REFUSAL_MESSAGE,
                "provider": "scope_guard",
                "model": "scope_guard_v1",
                "actions": [],
                "card": None
            }

        query = message.strip().lower()
        actions = []
        card = None
        
        # Grounded keyword matching for reliable offline fallback
        if any(w in query for w in ["accuracy", "production model", "model accuracy", "final model", "metrics", "how accurate", "skill score"]):
            text = (
                "Final operational model training and real-world evaluation on the East India target domain (83.5°E–89.8°E, 20.0°N–26.3°N) "
                "have not yet been completed, as they are pending verified 2020+ regional radar and satellite feeds. The architecture, "
                "loss formulations, and evaluation harness (CSI/POD/FAR/Brier) are verified, but no unmeasured production accuracy metrics are claimed.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["what is stormtrace", "explain stormtrace", "about stormtrace", "overview"]):
            text = (
                "STORMTRACE is an intelligent spatiotemporal thunderstorm nowcasting platform designed for high-resolution "
                "convective intelligence and multi-horizon radar/satellite nowcasting (0–120 minutes) across India.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["why convlstm", "convlstm", "architecture", "ai model", "model architecture", "algorithm", "forecastnet"]):
            text = (
                "STORMTRACE employs a genuine PyTorch spatiotemporal forecasting architecture (SpatiotemporalForecastNet / ConvLSTM) "
                "with MC-Dropout epistemic uncertainty estimation across 6 discrete forecast horizons (+15, +30, +45, +60, +90, +120 min). "
                "The model architecture and training harness are verified; final operational East India model training is pending verified 2020+ regional data.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["synthetic data", "demo mode", "why is the dashboard using synthetic", "demo"]):
            text = (
                "The current dashboard operates in DEMO MODE using calibrated synthetic benchmark scenarios to demonstrate "
                "end-to-end spatiotemporal nowcasting, cell tracking, and GIS visualization. Dataset loaders are fully prepared "
                "to ingest verified 2020+ East India regional radar and satellite feeds once loaded.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["dbz", "reflectivity", "decibels"]):
            text = (
                "Radar reflectivity in dBZ (decibels of Z) measures the intensity of radar energy reflected back by precipitation droplets.\n\n"
                "• < 20 dBZ: Very light drizzle / fog\n"
                "• 20–35 dBZ: Light to moderate steady rain\n"
                "• 35–45 dBZ: Heavy rain showers\n"
                "• 45–55 dBZ: Intense thunderstorm with gusty winds\n"
                "• >50 dBZ / 55–65+ dBZ: Severe supercell, torrential downpour, potential hail\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["lead time", "forecast horizon", "horizons", "how far ahead", "forecasts"]):
            text = (
                "STORMTRACE provides spatiotemporal nowcasts across 6 discrete forecast horizons (+15, +30, +45, +60, +90, +120 min) "
                "with calibrated epistemic uncertainty bounds (MC-Dropout) at each lead time.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["east india", "domain", "coordinates", "geographic"]):
            text = (
                "The primary STORMTRACE East India monitoring domain covers geographic coordinates:\n"
                "• Longitude: 83.5°E to 89.8°E\n"
                "• Latitude: 20.0°N to 26.3°N\n"
                "This regional grid spans West Bengal, Odisha, Jharkhand, and Bihar.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["datasets", "data sources", "provenance", "insat", "era5", "imerg", "wglc"]):
            text = (
                "STORMTRACE integrates five multimodal data streams:\n"
                "1. Radar (DWR): Reflectivity (dBZ) and radial velocity fields.\n"
                "2. Satellite (INSAT-3DS): Multichannel brightness temperatures (TIR1/TIR2/WV).\n"
                "3. Reanalysis (ERA5): Thermodynamic parameters (CAPE, CIN, wind shear).\n"
                "4. Precipitation (GPM IMERG): Calibrated half-hourly precipitation rates.\n"
                "5. Lightning (WGLC): 2010–2020 monthly mean climatological baseline.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["what is a thunderstorm", "define thunderstorm", "thunderstorm definition", "what is thunderstorm"]):
            text = (
                "A Thunderstorm is a dynamic mesoscale weather system produced by cumulonimbus clouds and characterized by lightning and thunder. "
                "Driven by atmospheric convection, thunderstorms feature vigorous updrafts, heavy precipitation, gusty winds, and occasionally hail.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["red area", "red zone", "what does red mean"]):
            text = (
                "Red areas on the map indicate high convective thunderstorm probability (>80%) or intense radar reflectivity "
                "(>50 dBZ) expected within the selected lead time. Severe precipitation, strong wind gusts, or lightning are likely in that zone.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["lightning", "physics", "charge"]):
            text = (
                "Lightning is an electrostatic discharge caused by charge separation inside convective clouds (cumulonimbus). "
                "In the mixed-phase zone (-10°C to -25°C), ascending ice crystals collide with descending graupel, transferring negative charge "
                "to the cloud base until dielectric breakdown occurs.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["safety", "30/30", "safe outside", "go outside"]):
            text = (
                "Severe Thunderstorm & Lightning Safety Guidelines:\n"
                "• 30/30 Rule: If the time between lightning and thunder is under 30 seconds, seek enclosed shelter immediately. Stay inside for 30 minutes after the last thunder.\n"
                "• Safe Shelters: Substantial enclosed buildings or metal-roofed vehicles. Avoid trees, open fields, and bodies of water.\n\n"
                f"{self.disclaimer}"
            )
        elif any(w in query for w in ["kolkata", "bengal"]):
            actions.append({"type": "SET_MAP_VIEW", "payload": {"lon": 88.36, "lat": 22.57, "zoom": 8.5}, "chipText": "📍 Moved to Kolkata"})
            text = f"Navigating to Kolkata / West Bengal in the East India domain. {self.disclaimer}"
        elif any(w in query for w in ["ranchi", "jharkhand"]):
            actions.append({"type": "SET_MAP_VIEW", "payload": {"lon": 85.31, "lat": 23.34, "zoom": 8.5}, "chipText": "📍 Moved to Ranchi"})
            text = f"Navigating to Ranchi / Jharkhand in the East India domain. {self.disclaimer}"
        elif any(w in query for w in ["chennai", "tamil nadu"]):
            actions.append({"type": "SET_MAP_VIEW", "payload": {"lon": 80.27, "lat": 13.08, "zoom": 8.5}, "chipText": "📍 Moved to Chennai"})
            text = f"Navigating to Chennai, Tamil Nadu. {self.disclaimer}"
        else:
            text = (
                f"STORMTRACE AI Assistant: Monitoring active convective cells, radar reflectivity (dBZ), and spatiotemporal forecasts. "
                f"How can I help you with storm analysis, radar interpretation, or safety guidelines?\n\n{self.disclaimer}"
            )

        return {
            "status": "success",
            "reply": text,
            "provider": "local_fallback",
            "model": "rule_based_grounded",
            "actions": actions,
            "card": card
        }


def get_ai_provider() -> AIProvider:
    """Factory to retrieve configured AI provider based on environment variables."""
    # Load .env if present
    env_file = os.path.join(os.path.dirname(__file__), "..", "..", "..", ".env")
    if os.path.exists(env_file):
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

    provider_name = os.getenv("AI_PROVIDER", "gemini").lower()

    if provider_name == "gemini":
        from .gemini_provider import GeminiProvider
        api_key = os.getenv("GEMINI_API_KEY", "")
        model_name = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")
        if api_key and api_key != "your_gemini_api_key_here":
            return GeminiProvider(api_key=api_key, model=model_name)
        else:
            return LocalFallbackProvider()
    elif provider_name == "local":
        return LocalFallbackProvider()
    else:
        return LocalFallbackProvider()
