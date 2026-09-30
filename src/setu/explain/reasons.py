from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

Language = Literal["en", "hi", "ta", "te"]


@dataclass(frozen=True)
class Reason:
    code: str
    weight: float
    text: str
    text_localized: str
    audio_url: str | None = None


TEMPLATES: dict[str, dict[str, str]] = {
    "FAN_IN_BURST": {
        "en": "This account received money from {n} new people in the last {h} hours.",
        "hi": "इस खाते में पिछले {h} घंटों में {n} नए लोगों से पैसे आए हैं। भुगतान से पहले रुककर जांच करें।",
        "ta": "இந்தக் கணக்கிற்கு கடந்த {h} மணி நேரத்தில் {n} புதிய நபர்களிடமிருந்து பணம் வந்துள்ளது. செலுத்தும் முன் நிறுத்திச் சரிபாருங்கள்.",
        "te": "ఈ ఖాతాకు గత {h} గంటల్లో {n} కొత్త వ్యక్తుల నుండి డబ్బు వచ్చింది. చెల్లించే ముందు ఒకసారి ఆగి తనిఖీ చేయండి.",
    },
    "FAST_PASS_THROUGH": {
        "en": "Money sent here tends to be moved out within minutes.",
        "hi": "इस खाते में आया पैसा अक्सर कुछ ही मिनटों में आगे भेज दिया जाता है।",
        "ta": "இந்தக் கணக்கிற்கு வரும் பணம் சில நிமிடங்களில் வெளியே அனுப்பப்படுவது வழக்கம்.",
        "te": "ఈ ఖాతాకు వచ్చిన డబ్బు తరచుగా కొన్ని నిమిషాల్లోనే బయటకు పంపబడుతోంది.",
    },
    "NEW_ACCOUNT_HIGH_VELOCITY": {
        "en": "This account is only {d} days old but is handling a lot of payments.",
        "hi": "यह खाता केवल {d} दिन पुराना है, लेकिन इसमें बहुत भुगतान हो रहे हैं।",
        "ta": "இந்தக் கணக்கு வெறும் {d} நாட்கள் பழையது, ஆனால் இதில் அதிக பணப்பரிவர்த்தனைகள் நடக்கின்றன.",
        "te": "ఈ ఖాతా కేవలం {d} రోజుల పాతది, కానీ చాలా చెల్లింపులను నిర్వహిస్తోంది.",
    },
    "FIRST_TIME_PAYEE_LARGE": {
        "en": "You've never paid this person, and this amount is much larger than your usual.",
        "hi": "आपने इस व्यक्ति को पहले कभी भुगतान नहीं किया है और यह रकम सामान्य से काफी अधिक है।",
        "ta": "நீங்கள் இதற்கு முன் இந்த நபருக்குப் பணம் செலுத்தியதில்லை; இந்தத் தொகை வழக்கத்தை விட அதிகம்.",
        "te": "మీరు ఈ వ్యక్తికి ఇంతకు ముందు చెల్లించలేదు; ఈ మొత్తం మీ సాధారణ మొత్తంకంటే చాలా ఎక్కువ.",
    },
    "UNSOLICITED_COLLECT": {
        "en": "This is a request to collect money. Real payments to you never need approval like this.",
        "hi": "यह पैसे लेने का अनुरोध है। आपको मिलने वाले असली भुगतान के लिए ऐसी मंजूरी नहीं चाहिए।",
        "ta": "இது பணம் வசூலிக்கும் கோரிக்கை. உங்களுக்கு வரும் உண்மையான பணப்பரிவர்த்தனைக்கு இப்படியான ஒப்புதல் தேவையில்லை.",
        "te": "ఇది డబ్బు వసూలు చేసే అభ్యర్థన. మీకు వచ్చే నిజమైన చెల్లింపుకు ఇటువంటి ఆమోదం అవసరం లేదు.",
    },
    "LINKED_TO_FLAGGED": {
        "en": "This account is closely linked to accounts already reported for suspicious activity.",
        "hi": "यह खाता संदिग्ध गतिविधि के लिए पहले से रिपोर्ट किए गए खातों से जुड़ा है।",
        "ta": "இந்தக் கணக்கு சந்தேகத்திற்குரிய செயல்பாட்டுக்காக ஏற்கனவே தெரிவிக்கப்பட்ட கணக்குகளுடன் நெருக்கமாக இணைந்துள்ளது.",
        "te": "ఈ ఖాతా అనుమానాస్పద కార్యకలాపాల కోసం ఇప్పటికే నివేదించబడిన ఖాతాలతో దగ్గరగా అనుసంధానమై ఉంది.",
    },
}


def build_reasons(codes: list[tuple[str, float]], lang: Language) -> list[Reason]:
    reasons: list[Reason] = []
    for code, weight in codes[:2]:
        values = {"n": 40, "h": 2, "d": 4}
        localized = TEMPLATES[code].get(lang, TEMPLATES[code]["en"]).format(**values)
        reasons.append(Reason(code, round(weight, 2), TEMPLATES[code]["en"].format(**values), localized))
    return reasons

