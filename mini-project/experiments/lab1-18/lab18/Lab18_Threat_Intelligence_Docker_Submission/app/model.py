"""Deterministic, synthetic threat telemetry: NOT a live threat feed."""
from datetime import datetime, timedelta, timezone
from collections import Counter
from random import Random

SOURCES = [f"sensor-{i:02d}" for i in range(1, 21)]
TYPES = ["phishing", "malware", "credential-abuse", "scanning", "data-exfiltration"]
TARGETS = [f"host-{i:03d}" for i in range(1, 101)]
FINGERPRINTS = [f"ioc-{i:03d}" for i in range(1, 50)]
BASE = datetime(2026, 11, 20, 0, 0, tzinfo=timezone.utc)

def make_threat(i: int) -> dict:
    r = Random(123456 + i)
    source = SOURCES[i % len(SOURCES)]
    threat_type = TYPES[(i // 7) % len(TYPES)]
    target = TARGETS[r.randrange(len(TARGETS))]
    fingerprint = FINGERPRINTS[r.randrange(len(FINGERPRINTS))]
    timestamp = BASE + timedelta(seconds=i % 86400, days=(i // 86400))
    confidence = round(0.15 + 0.8 * r.random(), 3)
    return {"threat_id": f"TH-{i:07d}", "from_source": source,
            "timestamp": timestamp, "day": timestamp.strftime('%Y-%m-%d'),
            "threat_type": threat_type, "target": target,
            "fingerprint": fingerprint, "confidence": confidence,
            "is_false_positive": confidence < 0.35}

def generate(n):
    for i in range(n): yield make_threat(i)

def summarize(records):
    return dict(Counter((r['from_source'], r['day']) for r in records))
