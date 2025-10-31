import os
import requests

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

HEADERS = {
    "apikey": SUPABASE_KEY,
    "Authorization": f"Bearer {SUPABASE_KEY}",
    "Content-Type": "application/json"
}


def get_all(table: str):
    url = f"{SUPABASE_URL}/rest/v1/{table}?select=*"
    res = requests.get(url, headers=HEADERS)
    res.raise_for_status()
    return res.json()


def insert_row(table: str, data: dict):
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    res = requests.post(url, headers=HEADERS, json=data)
    res.raise_for_status()
    return res.json()


def delete_row(table: str, row_id: int):
    url = f"{SUPABASE_URL}/rest/v1/{table}?id=eq.{row_id}"
    res = requests.delete(url, headers=HEADERS)
    res.raise_for_status()
    return {"status": "deleted"}