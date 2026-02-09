from __future__ import annotations

import os
from dotenv import load_dotenv
from serializd import SerializdClient

# Load .env exactly once when this module is imported
load_dotenv()


def create_client() -> SerializdClient:
    client = SerializdClient()

    username = os.getenv("SERIALIZD_USERNAME")
    password = os.getenv("SERIALIZD_PASSWORD")

    if username and password:
        client.login(email=username, password=password)

    return client
