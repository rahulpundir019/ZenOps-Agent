from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    if not path.is_file():
        return
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip("'").strip('"')
        os.environ.setdefault(key, value)


_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Settings:
    model: str = os.environ.get("GEMINI_MODEL", "gemini-3.1-flash-lite")
    app_name: str = os.environ.get("INCIDENT_APP_NAME", "network_incident_agent")
    project_id: str = os.environ.get("GOOGLE_CLOUD_PROJECT", "network-incident-agent")
    user_id: str = os.environ.get("INCIDENT_USER_ID", "local_test")
    max_retries: int = int(os.environ.get("INCIDENT_MAX_RETRIES", "4"))
    retry_delay_seconds: float = float(os.environ.get("INCIDENT_RETRY_DELAY_SECONDS", "15"))
    log_lookback_minutes: int = int(os.environ.get("INCIDENT_LOG_LOOKBACK_MINUTES", "30"))
    log_limit: int = int(os.environ.get("INCIDENT_LOG_LIMIT", "40"))
    test_log_name: str = os.environ.get("INCIDENT_TEST_LOG_NAME", "network-incident-test-log")


settings = Settings()
