import re

_PATTERN = re.compile(
    r"WHY_1:\s*(?P<why1>.+?)\s*Q1:\s*(?P<q1>.+?)\s*WHY_2:\s*(?P<why2>.+?)\s*Q2:\s*(?P<q2>.+?)\s*\Z",
    re.DOTALL | re.IGNORECASE
)

def parse_why_q(block: str):
    text = (block or "").strip()
    m = _PATTERN.search(text)
    if not m:
        return None
    return {
        "reason_q1": m.group("why1").strip(),
        "question1": m.group("q1").strip(),
        "reason_q2": m.group("why2").strip(),
        "question2": m.group("q2").strip(),
    }
