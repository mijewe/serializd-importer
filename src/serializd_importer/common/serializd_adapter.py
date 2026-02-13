from __future__ import annotations

import os
from dotenv import load_dotenv
from serializd import SerializdClient

# Load .env exactly once when this module is imported
load_dotenv()


def create_client() -> SerializdClient:
    client = SerializdClient()

    username = os.getenv("SERIALIZD_EMAIL")
    password = os.getenv("SERIALIZD_PASSWORD")

    if username and password:
        try:
            result = client.login(email=username, password=password)
        except Exception as e:
            raise
    else:
        print("DEBUG: No credentials found, skipping login")

    return client
