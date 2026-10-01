"""Configura la instancia local de Metabase sin versionar sus credenciales."""

from __future__ import annotations

import json
import os
import secrets

import requests

from lab8_common import PROCESSED

BASE_URL = os.getenv("LAB8_METABASE_URL", "http://127.0.0.1:3000")
CREDENTIALS = PROCESSED / "metabase_credentials.json"
LOCAL_EMAIL = "lab8@localhost.invalid"


def credentials() -> dict:
    if CREDENTIALS.exists():
        return json.loads(CREDENTIALS.read_text(encoding="utf-8"))
    properties = requests.get(f"{BASE_URL}/api/session/properties", timeout=20)
    properties.raise_for_status()
    token = properties.json().get("setup-token")
    if not token:
        raise RuntimeError("Metabase ya está configurado y faltan credenciales locales. "
                           "Defina LAB8_MB_EMAIL y LAB8_MB_PASSWORD para esta instancia.")
    account = {
        "email": os.getenv("LAB8_MB_EMAIL", LOCAL_EMAIL),
        "password": os.getenv("LAB8_MB_PASSWORD", secrets.token_urlsafe(24)),
    }
    payload = {
        "token": token,
        "user": {"first_name": "Grupo", "last_name": "Uno", **account},
        "prefs": {"site_name": "Laboratorio 8 · DuckDB", "site_locale": "es",
                  "allow_tracking": False},
    }
    response = requests.post(f"{BASE_URL}/api/setup", json=payload, timeout=60)
    if not response.ok:
        raise RuntimeError(f"No se pudo configurar Metabase: {response.status_code} "
                           f"{response.text[:350]}")
    PROCESSED.mkdir(parents=True, exist_ok=True)
    CREDENTIALS.write_text(json.dumps(account, indent=2), encoding="utf-8")
    return account


def session() -> requests.Session:
    account = credentials()
    response = requests.post(f"{BASE_URL}/api/session",
                             json={"username": account["email"],
                                   "password": account["password"]}, timeout=30)
    response.raise_for_status()
    client = requests.Session()
    client.headers.update({"X-Metabase-Session": response.json()["id"]})
    return client


def main() -> int:
    client = session()
    response = client.get(f"{BASE_URL}/api/user/current", timeout=20)
    response.raise_for_status()
    print("Metabase configurado y autenticado. Cuenta local guardada en "
          "data/processed/metabase_credentials.json (ignorada por Git).")
    print("Usuario:", response.json().get("email"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
