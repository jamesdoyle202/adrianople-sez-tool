import base64
import json
from typing import Any, Dict, List, Optional

import requests
import streamlit as st

GITHUB_OWNER = "jamesdoyle202"
GITHUB_REPO = "adrianople-sez-tool"
GITHUB_BRANCH = "main"
GITHUB_API_BASE = "https://api.github.com"

INDEX_PATH = "data/index.json"
POLYGONS_DIR = "data/polygons"


class GitHubAPIError(Exception):
    pass


def _headers() -> Dict[str, str]:
    try:
        token = st.secrets["GITHUB_TOKEN"]
    except (KeyError, FileNotFoundError) as exc:
        raise GitHubAPIError("GitHub token is not configured.") from exc

    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _get_file(path: str) -> Optional[Dict[str, Any]]:
    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    response = requests.get(
        url,
        headers=_headers(),
        params={"ref": GITHUB_BRANCH},
        timeout=30,
    )

    if response.status_code == 404:
        return None

    if not response.ok:
        raise GitHubAPIError(f"GitHub request failed with status {response.status_code}.")

    return response.json()


def _put_file(path: str, content: str, commit_message: str) -> None:
    existing = _get_file(path)
    payload: Dict[str, Any] = {
        "message": commit_message,
        "content": base64.b64encode(content.encode("utf-8")).decode("ascii"),
        "branch": GITHUB_BRANCH,
    }

    if existing:
        payload["sha"] = existing["sha"]

    url = f"{GITHUB_API_BASE}/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{path}"
    response = requests.put(url, headers=_headers(), json=payload, timeout=30)

    if not response.ok:
        raise GitHubAPIError(f"GitHub request failed with status {response.status_code}.")


def read_index() -> List[Dict[str, Any]]:
    file_data = _get_file(INDEX_PATH)
    if file_data is None:
        return []

    content = base64.b64decode(file_data["content"]).decode("utf-8")
    data = json.loads(content)
    return data if isinstance(data, list) else []


def check_duplicate(
    index_data: List[Dict[str, Any]],
    country_normalized: str,
    sez_name_normalized: str,
) -> Optional[Dict[str, Any]]:
    for entry in index_data:
        if (
            entry.get("country_normalized") == country_normalized
            and entry.get("sez_name_normalized") == sez_name_normalized
        ):
            return entry
    return None


def write_geojson(filename: str, geojson_data: Dict[str, Any], commit_message: str) -> None:
    path = f"{POLYGONS_DIR}/{filename}"
    content = json.dumps(geojson_data, indent=2) + "\n"
    _put_file(path, content, commit_message)


def write_index(index_data: List[Dict[str, Any]], commit_message: str) -> None:
    content = json.dumps(index_data, indent=2) + "\n"
    _put_file(INDEX_PATH, content, commit_message)
