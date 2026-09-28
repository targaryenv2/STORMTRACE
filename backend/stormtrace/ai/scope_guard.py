"""Deterministic Project-Scope Guard for STORMTRACE AI Assistant.

Ensures the assistant responds ONLY to queries directly related to the
STORMTRACE project, its meteorological science, AI models, data provenance,
system architecture, and dashboard functionality. Rejects all off-topic or
general-purpose queries with a polite, standard scope refusal.
"""

import re
from typing import Tuple

LOCALIZED_SCOPE_REFUSALS = {
    "en": (
        "I'm the STORMTRACE AI Assistant, designed to answer questions about the "
        "STORMTRACE project, its data, AI models, forecasting workflow, dashboard, "
        "results, and limitations. I can't help with unrelated general-knowledge or "
        "non-STORMTRACE questions."
    ),
    "hi": "मैं STORMTRACE AI सहायक हूँ, जो केवल STORMTRACE परियोजना, इसके डेटा, AI मॉडल, पूर्वानुमान वर्कफ़्लो, डैशबोर्ड, परिणाम और सीमाओं से संबंधित प्रश्नों के उत्तर देने के लिए डिज़ाइन किया गया है। मैं असंबंधित सामान्य ज्ञान या गैर-STORMTRACE प्रश्नों में मदद नहीं कर सकता।",
    "bn": "আমি STORMTRACE AI সহকারী, যা শুধুমাত্র STORMTRACE প্রকল্প, এর ডেটা, AI মডেল, পূর্বাভাস প্রক্রিয়া, ড্যাশবোর্ড, ফলাফল এবং সীমাবদ্ধতা সম্পর্কিত প্রশ্নের উত্তর দেওয়ার জন্য তৈরি করা হয়েছে। আমি সম্পর্কহীন সাধারণ জ্ঞান বা অ-STORMTRACE প্রশ্নের উত্তর দিতে পারি না।",
    "ta": "நான் STORMTRACE AI உதவியாளர், STORMTRACE திட்டம், அதன் தரவு, AI மாதிரிகள், முன்னறிவிப்பு பணிப்பாய்வு, டாஷ்போர்டு, முடிவுகள் மற்றும் வரம்புகள் பற்றிய கேள்விகளுக்கு மட்டுமே பதிலளிக்க வடிவமைக்கப்பட்டுள்ளேன்.",
    "te": "నేను STORMTRACE AI అసిస్టెంట్‌ని, కేవలం STORMTRACE ప్రాజెక్ట్, దాని డేటా, AI నమూనాలు, సూచన వర్క్‌ఫ్లో, డాష్‌బోర్డ్, ఫలితాలు మరియు పరిమితుల గురించిన ప్రశ్నలకు సమాధానమివ్వడానికి రూపొందించబడ్డాను.",
    "mr": "मी STORMTRACE AI सहाय्यक आहे, जो केवळ STORMTRACE प्रकल्प, त्याचा डेटा, AI मॉडेल, अंदाज वर्कफ्लो, डॅशबोर्ड, निकाल आणि मर्यादा यासंबंधीच्या प्रश्नांची उत्तरे देण्यासाठी डिझाइन केला आहे.",
    "gu": "હું STORMTRACE AI સહાયક છું, જે ફક્ત STORMTRACE પ્રોજેક્ટ, તેના ડેટા, AI મોડેલ્સ, આગાહી વર્કફ્લો, ડેશબોર્ડ, પરિણામો અને મર્યાદાઓ સંબંધિત પ્રશ્નોના જવાબો આપવા માટે રચાયેલ છે.",
    "kn": "ನಾನು STORMTRACE AI ಸಹಾಯಕ, STORMTRACE ಯೋಜನೆ, ಅದರ ಡೇಟಾ, AI ಮಾದರಿಗಳು, ಮುನ್ಸೂಚನೆ ವರ್ಕ್‌ಫ್ಲೋ, ಡ್ಯಾಶ್‌ಬೋರ್ಡ್, ಫಲಿತಾಂಶಗಳು ಮತ್ತು ಮಿತಿಗಳ ಕುರಿತಾದ ಪ್ರಶ್ನೆಗಳಿಗೆ ಮಾತ್ರ ಉತ್ತರಿಸಲು ವಿನ್ಯಾಸಗೊಳಿಸಲಾಗಿದೆ.",
    "ml": "ഞാൻ STORMTRACE AI അസിസ്റ്റന്റാണ്, STORMTRACE പ്രോജക്റ്റ്, അതിന്റെ ഡാറ്റ, AI മോഡലുകൾ, പ്രവചന വർക്ക്ഫ്ലോ, ഡാഷ്‌ബോർഡ്, ഫലങ്ങൾ, പരിമിതികൾ എന്നിവയെക്കുറിച്ചുള്ള ചോദ്യങ്ങൾക്ക് മാത്രം ഉത്തരം നൽകാൻ രൂപകൽപ്പന ചെയ്‌തിരിക്കുന്നു.",
    "pa": "ਮੈਂ STORMTRACE AI ਸਹਾਇਕ ਹਾਂ, ਜੋ ਸਿਰਫ਼ STORMTRACE ਪ੍ਰੋਜੈਕਟ, ਇਸਦੇ ਡੇਟਾ, AI ਮਾਡਲ, ਪੂਰਵ-ਅਨੁਮਾਨ ਵਰਕਫਲੋ, ਡੈਸ਼ਬੋਰਡ, ਨਤੀਜੇ ਅਤੇ ਸੀਮਾਵਾਂ ਬਾਰੇ ਸਵਾਲਾਂ ਦੇ ਜਵਾਬ ਦੇਣ ਲਈ ਤਿਆਰ ਕੀਤਾ ਗਿਆ ਹੈ।",
    "ur": "میں STORMTRACE AI اسسٹنٹ ہوں، جو صرف STORMTRACE پروجیکٹ، اس کے ڈیٹا، AI ماڈلز، پیشین گوئی کے ورک فلو، ڈیش بورڈ، نتائج اور حدود کے بارے میں سوالات کے جوابات دینے کے لیے بنایا گیا ہے۔",
    "or": "ମୁଁ STORMTRACE AI ସହାୟକ, କେବଳ STORMTRACE ପ୍ରକଳ୍ପ, ଏହାର ତଥ୍ୟ, AI ମଡେଲ୍, ପୂର୍ବାନୁମାନ କାର୍ଯ୍ୟପ୍ରବାହ, ଡ୍ୟାସବୋର୍ଡ, ଫଳାଫଳ ଏବଂ ସୀମାବଦ୍ଧତା ସମ୍ବନ୍ଧୀୟ ପ୍ରଶ୍ନର ଉତ୍ତର ଦେବା ପାଇଁ ଡିଜାଇନ୍ କରାଯାଇଛି।",
    "as": "মই STORMTRACE AI সহায়ক, কেৱল STORMTRACE প্ৰকল্প, ইয়াৰ তথ্য, AI মডেল, পূৰ্বানুমান কাৰ্যপ্ৰবাহ, ডেচবৰ্ড, ফলাফল আৰু সীমাবদ্ধতা সম্পৰ্কীয় প্ৰশ্নৰ উত্তৰ দিবলৈ ডিজাইন কৰা হৈছে।"
}

SCOPE_REFUSAL_MESSAGE = LOCALIZED_SCOPE_REFUSALS["en"]

def get_scope_refusal(lang: str = "en") -> str:
    """Returns the scope refusal message localized to the requested language code."""
    clean_lang = (lang or "en").lower().split("-")[0].split("_")[0]
    return LOCALIZED_SCOPE_REFUSALS.get(clean_lang, LOCALIZED_SCOPE_REFUSALS["en"])


# Explicit injection and override patterns
PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(all\s+|previous\s+|prior\s+)?instructions",
    r"disregard\s+(all\s+|previous\s+|prior\s+)?instructions",
    r"system\s+prompt",
    r"jailbreak",
    r"you\s+are\s+now\s+(dan|unrestricted|free|an?\s+ai\s+without\s+rules)",
    r"act\s+as\s+(a\s+general|an\s+unrestricted|someone\s+else)",
    r"bypass\s+(the\s+)?guard",
    r"override\s+(the\s+)?system",
]

# Explicit off-topic indicators
OFF_TOPIC_PATTERNS = [
    r"\b(capital\s+of\s+[a-z]+)\b",
    r"\b(who\s+is|who\s+was)\s+(elon\s+musk|bill\s+gates|jeff\s+bezos|trump|biden|modi|obama|newton|einstein|messi|ronaldo)\b",
    r"\b(tell\s+me\s+a\s+joke|make\s+me\s+laugh|write\s+a\s+joke)\b",
    r"\b(write\s+(me\s+)?(a\s+)?(python\s+game|game|poem|song|story|resume|cv|cover\s+letter|essay|novel|code\s+for\s+flappy\s+bird|snake\s+game))\b",
    r"\b(cricket\s+score|ipl\s+score|football\s+score|who\s+won\s+the\s+match|who\s+won\s+the\s+election|election\s+results?)\b",
    r"\b(recipe\s+for|how\s+to\s+cook|how\s+to\s+bake|ingredients\s+for|make\s+a\s+cake|pasta\s+recipe)\b",
    r"\b(translate\s+(this|the\s+following|to\s+french|to\s+spanish|to\s+german))\b",
    r"\b(weather\s+in\s+(london|paris|new\s+york|berlin|tokyo|sydney|madrid|rome|toronto))\b",
    r"\b(movie\s+recommendation|best\s+movies?|song\s+lyrics|bitcoin\s+price|stock\s+price\s+of)\b",
    r"\b(what\s+is\s+the\s+meaning\s+of\s+life|who\s+created\s+you\s+originally)\b",
]

# Comprehensive STORMTRACE project, meteorological, ML, and systems concepts
PROJECT_KEYWORDS = [
    # Core brand & problem
    "stormtrace", "nowcast", "nowcasting", "thunderstorm", "storm", "convective",
    "convection", "lightning", "radar", "satellite", "insat", "insat3ds", "insat-3ds",
    "nwp", "era5", "imerg", "gpm", "wglc", "dwr", "terls", "thumba",
    # Radar & physics
    "dbz", "reflectivity", "decibel", "decibels", "echo", "cape", "cin", "updraft",
    "downdraft", "graupel", "hail", "supercell", "squall", "mesocyclone", "shear",
    "microburst", "downburst", "dielectric", "electrostatic", "flash rate",
    # Model architecture & ML
    "convlstm", "conv-lstm", "spatiotemporal", "multimodal", "forecastnet",
    "mc dropout", "mc-dropout", "dropout", "epistemic", "uncertainty",
    "loss", "training", "train", "weights", "checkpoint", "pytorch", "model",
    "architecture", "layer", "encoder", "decoder", "optical flow", "advection",
    # Forecast horizons & evaluation
    "horizon", "horizons", "lead time", "lead times", "15 min", "30 min", "45 min",
    "60 min", "90 min", "120 min", "csi", "pod", "far", "brier", "critical success",
    "probability of detection", "false alarm", "skill score", "accuracy", "evaluation",
    "metric", "metrics", "benchmark", "validation",
    # Target domain & geography
    "east india", "domain", "coordinates", "geographic", "grid", "resolution",
    "west bengal", "kolkata", "odisha", "bhubaneswar", "jharkhand", "ranchi",
    "bihar", "patna", "gangetic", "kalbaishakhi", "nor'wester",
    # System & Dashboard
    "system", "pipeline", "backend", "frontend", "dashboard", "api", "endpoint",
    "synthetic", "demo", "demo mode", "data source", "provenance", "limitation",
    "limitations", "future work", "deployment", "docker", "geoserver", "openlayers",
    "map", "threat", "red area", "color scale", "severity", "cell tracking", "tracker",
    "analog", "analogs", "safety", "30/30", "shelter", "aviation", "flight", "imd", "mosdac"
]


def classify_project_scope(message: str) -> Tuple[str, bool]:
    """Classifies a user query as PROJECT_RELATED or OFF_TOPIC.
    
    Returns:
        (category, is_project_related): Tuple of ('PROJECT_RELATED'|'OFF_TOPIC', bool)
    """
    clean_msg = message.strip().lower()
    if not clean_msg:
        return "OFF_TOPIC", False

    # 1. Check prompt injection attempts
    for pattern in PROMPT_INJECTION_PATTERNS:
        if re.search(pattern, clean_msg, re.IGNORECASE):
            return "OFF_TOPIC", False

    # 2. Check explicit off-topic patterns
    for pattern in OFF_TOPIC_PATTERNS:
        if re.search(pattern, clean_msg, re.IGNORECASE):
            return "OFF_TOPIC", False

    # 3. Check for presence of project keywords
    has_project_keyword = any(kw in clean_msg for kw in PROJECT_KEYWORDS)

    if has_project_keyword:
        return "PROJECT_RELATED", True

    # 4. Short general greetings or system help queries
    if re.match(r"^(hi|hello|hey|help|namaste|greetings|who are you|what can you do)\b", clean_msg, re.IGNORECASE):
        return "PROJECT_RELATED", True

    # 5. Default fallback to OFF_TOPIC for any ungrounded query
    return "OFF_TOPIC", False
