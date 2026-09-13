import re
import base64
from typing import NamedTuple, Optional

class ExtractedPayload(NamedTuple):
    raw_b64: str
    raw_bytes: bytes
    magic: bytes
    key_len: int
    key_str: str
    payload_bytes: bytes

def extract_payload(code: str) -> Optional[ExtractedPayload]:
    m = re.search(r'\"([A-Za-z0-9\+\/\=\_\-]{100,})\"', code)
    if not m:
        return None

    raw_b64 = m.group(1)
    raw_bytes = base64.b64decode(raw_b64)
    
    if len(raw_bytes) < 10 or b'Xen' not in raw_bytes[:10]:
        return None

    magic = raw_bytes[1:5]
    key_len = int.from_bytes(raw_bytes[5:9], 'little')
    key_bytes = raw_bytes[9:9 + key_len - 1]
    key_str = key_bytes.decode('utf-8', errors='ignore')
    payload_bytes = raw_bytes[9 + key_len:]

    return ExtractedPayload(
        raw_b64=raw_b64,
        raw_bytes=raw_bytes,
        magic=magic,
        key_len=key_len,
        key_str=key_str,
        payload_bytes=payload_bytes
    )
