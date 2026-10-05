"""M11: Linguistic Feature Extractor.

Extracts psychological distress indicators across 8 distinct dimensions
(Fear, Threat, Helplessness, Urgency, Negative Affect, Help Requests,
Self-Blame, Uncertainty) in both English, Hindi (Devanagari), and Romanized Hindi (Hinglish).
"""

from typing import Dict, List, Pattern, Union
import re

from packages.schemas.text import LinguisticFeatures, NormalizedTranscript

# Multilingual regex lexicons per psychological distress dimension
_LEXICONS: Dict[str, List[str]] = {
    "fear": [
        r"\b(afraid|terrified|scared|panic|panicking|frightened|petrified|trembling|horror)\b",
        r"(डर|डरी|डरा|भय|भयभीत|कांप|घबराहट|घबरा|खौफ)",
        r"\b(darr?|dara|dari|ghabrahat|khauf)\b",
    ],
    "threat": [
        r"\b(kill|killing|hurt|hurting|weapon|knife|gun|pistol|attack|attacked|choke|strangle|beat|beating|abuse|abusing|violence|threat|threatened|threatening|threatens|shoot|shooting|bleed|bleeding)\b",
        r"(मार|मारना|मारेगा|मारेगी|जान से|चोट|चाकू|बंदूक|हमला|गला घोंट|पीटा|पीट|धमकी|खून)",
        r"\b(maar|maarega|maaregi|chaaku|bandook|hamla|dhamki|khoon)\b",
    ],
    "helplessness": [
        r"\b(can'?t take it|cannot take it|trapped|nowhere to go|no way out|helpless|hopeless|cannot do this|give up|ending it all|no choice)\b",
        r"(लाचार|बेबस|असहाय|कोई रास्ता नहीं|फंस गई|फंस गया|कुछ नहीं हो सकता|हार मान)",
        r"\b(laach?ar|bebas|phas gay[ai]|koi raasta nahi)\b",
    ],
    "urgency": [
        r"\b(immediately|right now|hurry|emergency|urgent|urgently|quick|quickly|fast|asap|now now)\b",
        r"(अभी|तुरंत|जल्दी|फौरन|आपातकाल|इमरजेंसी|जल्दी आओ)",
        r"\b(abhi|turant|jaldi|fauran|emergency)\b",
    ],
    "negative_affect": [
        r"\b(pain|crying|cried|tears|weeping|suffering|depressed|depression|miserable|scream|screaming|agony|awful|terrible|devastated)\b",
        r"(दर्द|रोना|रो रही|रो रहा|आंसू|चीख|चीखना|तड़प|तकलीफ|परेशान|बर्दाश्त नहीं)",
        r"\b(dard|ro rah[ai]|aansoo|pareshan|takleef)\b",
    ],
    "help_request": [
        r"\b(please\s+help(\s+me)?|help\s+me|send\s+police|send\s+an?\s+ambulance|save\s+me|someone\s+help|call\s+(?:911|112|100)|assist\s+me|rescue\s+me|help\s+us)\b",
        r"(मदद करो|मदद कीजिए|मुझे बचाओ|बचाओ|पुलिस भेजो|एम्बुलेंस भेजो|सहायता)",
        r"\b(madad|bachao|police bhejo|ambulance bhejo)\b",
    ],

    "self_blame": [
        r"\b(my fault|my mistake|i caused this|i deserve this|i shouldn'?t have|all my fault|hate myself)\b",
        r"(मेरी गलती|मेरी वजह से|मेरा कसूर|मैंने ही किया|मेरी खता)",
        r"\b(meri galti|meri wajah se|mera kasoor)\b",
    ],
    "uncertainty": [
        r"\b(maybe|perhaps|i don'?t know|don'?t know what to do|confused|what should i do|lost|unsure)\b",
        r"(शायद|पता नहीं|क्या करूं|कुछ समझ नहीं आ रहा|भटक)",
        r"\b(shayad|pata nahi|kya karu)\b",
    ],
}

# Precompile patterns
_COMPILED_LEXICONS: Dict[str, List[Pattern]] = {
    dim: [re.compile(pat, re.IGNORECASE) for pat in patterns]
    for dim, patterns in _LEXICONS.items()
}


def extract_linguistic_features(
    transcript: Union[NormalizedTranscript, str],
    language: str = "en",
) -> LinguisticFeatures:
    """Spec M11: Extract psychological distress indicators from transcript text.

    Args:
        transcript: NormalizedTranscript object or raw string.
        language: Language code.

    Returns:
        LinguisticFeatures object populated with detected terms per dimension.
    """
    text = transcript.text if isinstance(transcript, NormalizedTranscript) else transcript
    if not text or not text.strip():
        return LinguisticFeatures()

    found_by_dim: Dict[str, List[str]] = {dim: [] for dim in _LEXICONS}

    for dim, patterns in _COMPILED_LEXICONS.items():
        matched_set = set()
        for pat in patterns:
            for match in pat.finditer(text):
                matched_set.add(match.group(0).strip())
        found_by_dim[dim] = sorted(list(matched_set))

    total_count = sum(len(items) for items in found_by_dim.values())

    return LinguisticFeatures(
        fear_indicators=found_by_dim["fear"],
        threat_indicators=found_by_dim["threat"],
        helplessness_indicators=found_by_dim["helplessness"],
        urgency_indicators=found_by_dim["urgency"],
        negative_affect_indicators=found_by_dim["negative_affect"],
        help_request_indicators=found_by_dim["help_request"],
        self_blame_indicators=found_by_dim["self_blame"],
        uncertainty_indicators=found_by_dim["uncertainty"],
        indicator_count=total_count,
    )
