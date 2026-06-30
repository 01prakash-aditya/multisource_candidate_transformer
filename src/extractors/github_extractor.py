import logging
import requests
from typing import List
from urllib.parse import urlparse
from .base import BaseExtractor, RawRecord

logger = logging.getLogger(__name__)

class GitHubExtractor(BaseExtractor):
    def __init__(self, token: str = None):
        """
        Optional GitHub token to avoid rate limits.
        """
        self.headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            self.headers["Authorization"] = f"token {token}"

    def _extract_username(self, source_input: str) -> str:
        # If it's a URL, extract the username
        if "github.com" in source_input:
            path = urlparse(source_input).path
            return path.strip('/').split('/')[0]
        return source_input.strip()

    def extract(self, source_input: str) -> List[RawRecord]:
        """
        source_input is either a GitHub username or a GitHub profile URL.
        """
        username = self._extract_username(source_input)
        if not username:
            return []

        raw_data = {"username": username}

        try:
            # Fetch profile
            profile_resp = requests.get(
                f"https://api.github.com/users/{username}",
                headers=self.headers,
                timeout=10
            )
            
            if profile_resp.status_code == 200:
                raw_data.update(profile_resp.json())
            elif profile_resp.status_code == 404:
                logger.warning(f"GitHub user {username} not found (404).")
            elif profile_resp.status_code == 403:
                logger.warning(f"GitHub API rate limit exceeded for {username}.")
            else:
                logger.warning(f"GitHub API error {profile_resp.status_code} for {username}.")

            # Fetch repos for languages (skills)
            repos_resp = requests.get(
                f"https://api.github.com/users/{username}/repos?per_page=100",
                headers=self.headers,
                timeout=10
            )
            
            languages = set()
            if repos_resp.status_code == 200:
                for repo in repos_resp.json():
                    if repo.get("language"):
                        languages.add(repo["language"])
            
            raw_data["extracted_languages"] = list(languages)

        except requests.RequestException as e:
            logger.error(f"Network error fetching GitHub profile for {username}: {e}")
            # Graceful degradation on network error

        return [RawRecord(
            source_type="github",
            source_identifier=source_input,
            raw_data=raw_data
        )]
