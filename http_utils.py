import os
import urllib.request
import urllib.robotparser
import logging
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")


def build_user_agent():
    """Build User-Agent string from environment variables.

    All four BOT_* variables are required — the script exits with a clear
    error if any are missing.  This prevents forkers from accidentally
    running with someone else's bot identity.
    """
    name = os.getenv("BOT_NAME")
    version = os.getenv("BOT_VERSION")
    url = os.getenv("BOT_URL")
    email = os.getenv("BOT_EMAIL")

    missing = [
        label
        for value, label in [
            (name, "BOT_NAME"),
            (version, "BOT_VERSION"),
            (url, "BOT_URL"),
            (email, "BOT_EMAIL"),
        ]
        if not value
    ]
    if missing:
        raise EnvironmentError(
            f"Missing required environment variable(s): {', '.join(missing)}. "
            "Set them to identify your bot honestly. Example:\n"
            "  BOT_NAME=PoolOccupancyBot BOT_VERSION=1.0 "
            "BOT_URL=https://github.com/you/repo BOT_EMAIL=you@example.com"
        )

    parts = [f"+{url}", f"+mailto:{email}"]
    return f"{name}/{version} ({'; '.join(parts)})"


BOT_USER_AGENT = build_user_agent()

_robots_cache: dict[str, urllib.robotparser.RobotFileParser] = {}


def can_fetch(url: str) -> bool:
    """Check whether *url* is allowed by the site's robots.txt.

    Parsed robots.txt files are cached per domain so we don't re-fetch
    on every request.
    """
    parsed = urlparse(url)
    domain = f"{parsed.scheme}://{parsed.netloc}"

    if domain not in _robots_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(f"{domain}/robots.txt")
        try:
            rp.read()
        except Exception as e:
            logging.warning(
                "Could not fetch robots.txt for %s, assuming allowed: %s", domain, e
            )
        _robots_cache[domain] = rp

    return _robots_cache[domain].can_fetch(BOT_USER_AGENT, url)


def fetch_url(url: str) -> str | None:
    """Fetch a URL as an honest bot, respecting robots.txt.

    Returns the decoded HTML content, or *None* if the URL is blocked
    by robots.txt or the request fails.
    """
    if not can_fetch(url):
        logging.warning("Blocked by robots.txt: %s", url)
        return None

    try:
        req = urllib.request.Request(url, headers={"User-Agent": BOT_USER_AGENT})
        response = urllib.request.urlopen(req)
        return response.read().decode("utf-8")
    except Exception as e:
        logging.error("Error fetching %s: %s", url, e)
        return None