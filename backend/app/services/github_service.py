"""GitHub REST API client with TTL cache and rate-limit awareness."""
from __future__ import annotations

import time
from collections import Counter

import requests
from flask import current_app

_CACHE: dict[str, dict] = {}


def _headers() -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "PrabhashaNexus/1.0",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    token = current_app.config.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _ttl() -> int:
    return current_app.config.get("GITHUB_CACHE_TTL_SECONDS", 600)


def _request(path: str) -> dict:
    username = current_app.config.get("GITHUB_USERNAME", "prabhasha-2001")
    url = path.format(username=username)
    response = requests.get(url, headers=_headers(), timeout=12)
    rate_limit = {
        "remaining": response.headers.get("X-RateLimit-Remaining"),
        "limit": response.headers.get("X-RateLimit-Limit"),
        "reset": response.headers.get("X-RateLimit-Reset"),
    }
    if response.status_code == 403 and response.headers.get("X-RateLimit-Remaining") == "0":
        raise RuntimeError("GitHub API rate limit exceeded")
    if response.status_code == 404:
        raise RuntimeError("GitHub user or resource not found")
    response.raise_for_status()
    return {"data": response.json(), "rate_limit": rate_limit}


def _cached(key: str, loader):
    entry = _CACHE.get(key)
    now = time.time()
    if entry and now - entry["fetched_at"] < _ttl():
        return {**entry, "cached": True}
    try:
        result = loader()
        entry = {
            "data": result["data"],
            "rate_limit": result.get("rate_limit", {}),
            "fetched_at": now,
            "cached": False,
        }
        _CACHE[key] = entry
        return entry
    except Exception as exc:
        if entry:
            return {**entry, "cached": True, "stale": True, "error": str(exc)}
        return {"data": None, "cached": False, "error": str(exc), "fetched_at": now}


def get_profile() -> dict:
    entry = _cached("profile", lambda: _request("https://api.github.com/users/{username}"))
    data = entry.get("data") or {}
    return {
        "configured": True,
        "cached": entry.get("cached", False),
        "stale": entry.get("stale", False),
        "error": entry.get("error"),
        "profile": {
            "login": data.get("login"),
            "name": data.get("name"),
            "bio": data.get("bio"),
            "avatar_url": data.get("avatar_url"),
            "html_url": data.get("html_url"),
            "public_repos": data.get("public_repos"),
            "followers": data.get("followers"),
            "following": data.get("following"),
            "location": data.get("location"),
        } if data else None,
        "rate_limit": entry.get("rate_limit", {}),
    }


def get_repos() -> dict:
    entry = _cached(
        "repos",
        lambda: _request("https://api.github.com/users/{username}/repos?per_page=100&sort=updated"),
    )
    repos = entry.get("data") or []
    languages = Counter(repo.get("language") for repo in repos if repo.get("language"))
    mapped = [
        {
            "id": repo.get("id"),
            "name": repo.get("name"),
            "full_name": repo.get("full_name"),
            "description": repo.get("description"),
            "html_url": repo.get("html_url"),
            "homepage": repo.get("homepage"),
            "language": repo.get("language"),
            "stargazers_count": repo.get("stargazers_count", 0),
            "forks_count": repo.get("forks_count", 0),
            "open_issues_count": repo.get("open_issues_count", 0),
            "topics": repo.get("topics", []),
            "updated_at": repo.get("updated_at"),
            "pushed_at": repo.get("pushed_at"),
            "fork": repo.get("fork", False),
            "archived": repo.get("archived", False),
        }
        for repo in repos
        if isinstance(repo, dict)
    ]
    mapped.sort(key=lambda repo: (repo["stargazers_count"], repo["updated_at"] or ""), reverse=True)
    return {
        "configured": True,
        "cached": entry.get("cached", False),
        "stale": entry.get("stale", False),
        "error": entry.get("error"),
        "repos": mapped,
        "stats": {
            "repository_count": len(mapped),
            "total_stars": sum(repo["stargazers_count"] for repo in mapped),
            "total_forks": sum(repo["forks_count"] for repo in mapped),
            "languages": dict(languages.most_common(10)),
        },
        "rate_limit": entry.get("rate_limit", {}),
        "fetched_at": entry.get("fetched_at"),
    }


def get_repo(name: str) -> dict:
    entry = _cached(
        f"repo:{name}",
        lambda: _request(f"https://api.github.com/repos/{{username}}/{name}"),
    )
    return {"data": entry.get("data"), "cached": entry.get("cached", False),
            "error": entry.get("error"), "rate_limit": entry.get("rate_limit", {})}


def refresh() -> None:
    _CACHE.clear()
