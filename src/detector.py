import re
from typing import Dict, Any, List

class DetectionResult:
    def __init__(self, is_synapse_xen: bool, version: str = "v1.1.2", confidence: float = 0.0, details: List[str] = None):
        self.is_synapse_xen = is_synapse_xen
        self.version = version
        self.confidence = confidence
        self.details = details or []

    def __repr__(self):
        return f"<DetectionResult Xen={self.is_synapse_xen} ver={self.version} conf={self.confidence:.2f}>"

def detect_synapse_xen(code: str) -> DetectionResult:
    details = []
    score = 0.0

    if "--[[" in code and "Synapse Xen v1.1.2" in code:
        details.append("Matched explicit Synapse Xen v1.1.2 header comment")
        score += 0.5

    if "VM Hash:" in code:
        details.append("Matched Synapse Xen VM Hash field")
        score += 0.2

    if "SynapseXen_" in code:
        details.append("Matched SynapseXen_ variable namespace")
        score += 0.2

    b64_match = re.search(r'\"([A-Za-z0-9\+\/\=\_\-]{100,})\"', code)
    if b64_match:
        details.append("Matched embedded Base64 payload string")
        score += 0.1

    is_xen = score >= 0.3
    return DetectionResult(is_synapse_xen=is_xen, version="v1.1.2", confidence=min(score, 1.0), details=details)
