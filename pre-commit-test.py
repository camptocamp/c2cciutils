import requests
import hashlib
import os
import json
from typing import Optional, Dict, Any

class GitHubCache:
    def __init__(self, token: str, repo: str, owner: str):
        """
        Initialize GitHub Cache utility

        Args:
            token (str): GitHub token with actions:read and actions:write permissions
            repo (str): Repository name
            owner (str): Repository owner
        """
        self.token = token
        self.repo = repo
        self.owner = owner
        self.base_url = f"https://api.github.com/repos/{owner}/{repo}/actions/caches"
        self.headers = {
            "Accept": "application/vnd.github.v3+json",
            "Authorization": f"Bearer {token}",
            "X-GitHub-Api-Version": "2022-11-28"
        }

    def _calculate_hash(self, path: str) -> str:
        """Calculate SHA256 hash of a file"""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    def upload_cache(self, path: str, key: str) -> bool:
        """
        Upload a file to GitHub Actions cache

        Args:
            path (str): Path to file to upload
            key (str): Cache key

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return False

        # Get cache URL
        payload = {
            "key": key,
            "version": self._calculate_hash(path),
            "paths": [path]
        }

        response = requests.post(
            self.base_url,
            headers=self.headers,
            json=payload
        )

        if response.status_code != 200:
            print(f"Failed to get cache URL: {response.text}")
            return False

        cache_url = response.json().get("cache_url")

        # Upload file
        with open(path, "rb") as f:
            upload_response = requests.put(
                cache_url,
                headers={
                    "Content-Type": "application/octet-stream",
                    "Authorization": f"Bearer {self.token}"
                },
                data=f
            )

        return upload_response.status_code == 200

    def download_cache(self, key: str, dest_path: str) -> bool:
        """
        Download a cache by key

        Args:
            key (str): Cache key
            dest_path (str): Destination path for downloaded file

        Returns:
            bool: True if successful, False otherwise
        """
        # List caches to find the one we want
        response = requests.get(
            f"{self.base_url}?key={key}",
            headers=self.headers
        )

        if response.status_code != 200:
            print(f"Failed to list caches: {response.text}")
            return False

        caches = response.json().get("actions_caches", [])
        if not caches:
            print(f"No cache found for key: {key}")
            return False

        cache_id = caches[0]["id"]

        # Download cache
        download_response = requests.get(
            f"{self.base_url}/{cache_id}",
            headers=self.headers,
            stream=True
        )

        if download_response.status_code != 200:
            print(f"Failed to download cache: {download_response.text}")
            return False

        with open(dest_path, "wb") as f:
            for chunk in download_response.iter_content(chunk_size=8192):
                f.write(chunk)

        return True

    def list_caches(self) -> Optional[Dict[str, Any]]:
        """List all caches in the repository"""
        response = requests.get(
            self.base_url,
            headers=self.headers
        )

        if response.status_code != 200:
            print(f"Failed to list caches: {response.text}")
            return None

        return response.json()



# Usage example
# Initialiser le client
cache_client = GitHubCache(
    token="ghp_your_github_token",
    owner="votre-username",
    repo="votre-repo"
)

# Upload un fichier dans le cache
success = cache_client.upload_cache(
    path="path/to/your/file",
    key="mon-cache-key"
)

# Télécharger un cache
success = cache_client.download_cache(
    key="mon-cache-key",
    dest_path="path/to/destination"
)

# Lister tous les caches
caches = cache_client.list_caches()


# Avec githubkit

import os
import hashlib
from typing import Optional
from githubkit import GitHub, Response
from githubkit.exception import RequestError

class GitHubCacheManager:
    def __init__(self, token: str, owner: str, repo: str):
        """
        Initialize GitHub Cache manager using GitHubKit

        Args:
            token (str): GitHub token with actions:read and actions:write permissions
            owner (str): Repository owner
            repo (str): Repository name
        """
        self.gh = GitHub(token)
        self.owner = owner
        self.repo = repo

    def _calculate_hash(self, path: str) -> str:
        """Calculate SHA256 hash of a file for versioning"""
        sha256_hash = hashlib.sha256()
        with open(path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()

    async def upload_cache(self, path: str, key: str) -> bool:
        """
        Upload a file to GitHub Actions cache

        Args:
            path (str): Path to file to upload
            key (str): Cache key

        Returns:
            bool: True if successful, False otherwise
        """
        if not os.path.exists(path):
            print(f"File not found: {path}")
            return False

        try:
            # Create cache entry
            response = await self.gh.rest.actions.create_repository_cache(
                owner=self.owner,
                repo=self.repo,
                data={
                    "key": key,
                    "version": self._calculate_hash(path),
                    "paths": [path]
                }
            )

            cache_url = response.parsed_data.cache_url

            # Upload the file to the cache URL
            with open(path, "rb") as f:
                await self.gh.rest.actions.upload_cache_file(
                    url=cache_url,
                    data=f.read()
                )
            return True

        except RequestError as e:
            print(f"Error uploading cache: {e}")
            return False

    async def download_cache(self, key: str, dest_path: str) -> bool:
        """
        Download a cache by key

        Args:
            key (str): Cache key
            dest_path (str): Destination path for downloaded file

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # List caches to find the one we want
            response = await self.gh.rest.actions.get_repository_caches(
                owner=self.owner,
                repo=self.repo,
                key=key
            )

            if not response.parsed_data.actions_caches:
                print(f"No cache found for key: {key}")
                return False

            cache_id = response.parsed_data.actions_caches[0].id

            # Download the cache
            cache_data = await self.gh.rest.actions.download_cache_file(
                owner=self.owner,
                repo=self.repo,
                cache_id=cache_id
            )

            # Write the cache data to file
            with open(dest_path, "wb") as f:
                f.write(cache_data.content)

            return True

        except RequestError as e:
            print(f"Error downloading cache: {e}")
            return False

    async def list_caches(self) -> Optional[Response]:
        """
        List all caches in the repository

        Returns:
            Optional[Response]: Response containing cache information or None if error
        """
        try:
            return await self.gh.rest.actions.get_repository_caches(
                owner=self.owner,
                repo=self.repo
            )
        except RequestError as e:
            print(f"Error listing caches: {e}")
            return None

    async def delete_cache(self, key: str) -> bool:
        """
        Delete a cache by key

        Args:
            key (str): Cache key to delete

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            response = await self.gh.rest.actions.get_repository_caches(
                owner=self.owner,
                repo=self.repo,
                key=key
            )

            if not response.parsed_data.actions_caches:
                print(f"No cache found for key: {key}")
                return False

            cache_id = response.parsed_data.actions_caches[0].id

            await self.gh.rest.actions.delete_repository_cache(
                owner=self.owner,
                repo=self.repo,
                cache_id=cache_id
            )

            return True

        except RequestError as e:
            print(f"Error deleting cache: {e}")
            return False

# Usage example

import asyncio

async def main():
    cache_manager = GitHubCacheManager(
        token="ghp_your_github_token",
        owner="votre-username",
        repo="votre-repo"
    )

    # Upload un fichier
    success = await cache_manager.upload_cache(
        path="path/to/your/file",
        key="mon-cache-key"
    )

    # Télécharger un cache
    success = await cache_manager.download_cache(
        key="mon-cache-key",
        dest_path="path/to/destination"
    )

    # Lister les caches
    caches = await cache_manager.list_caches()

    # Supprimer un cache
    success = await cache_manager.delete_cache(key="mon-cache-key")

# Exécuter le code asynchrone
asyncio.run(main())
