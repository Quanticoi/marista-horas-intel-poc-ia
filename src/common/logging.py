import json
import logging
import re
from datetime import datetime, timezone

SENSITIVE = re.compile(r"(?i)(password|token|secret|authorization|credential|access.key)")


def redact(value):
    if isinstance(value, dict):
        return {k: "[REDACTED]" if SENSITIVE.search(k) else redact(v) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v) for v in value]
    if isinstance(value, str):
        value = re.sub(r"(?i)(Bearer\s+)\S+", r"\1[REDACTED]", value)
        value = re.sub(r"(://)[^\s/@]+:[^\s/@]+@", r"\1[REDACTED]@", value)
        return re.sub(r"(?i)((?:password|token|secret|authorization|credential|access[_-]?key)\s*[=:]\s*)[^\s,;]+", r"\1[REDACTED]", value)
    return value


def event(service, message, level="INFO", **fields):
    payload = json.dumps(redact({"timestamp": datetime.now(timezone.utc).isoformat(),
          "service": service, "level": level, "message": message, **fields}), default=str)
    print(payload, flush=True)
    # Per-process/day files avoid cross-container rotation races; dashboard reads JSONL.
    import os
    from pathlib import Path
    directory = os.getenv("EVENT_DIRECTORY")
    if directory:
        import socket
        target = Path(directory)
        target.mkdir(parents=True, exist_ok=True)
        day = datetime.now(timezone.utc).strftime("%Y%m%d")
        with (target / f"{day}-{socket.gethostname()}-{os.getpid()}.jsonl").open("a", encoding="utf-8") as stream:
            stream.write(payload + "\n")
