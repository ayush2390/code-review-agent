import requests
from typing import Dict, Optional, List
import base64

class GitHubClient:
    def __init__(self):
        self.base_url = "https://api.github.com"
    
    def get_pr_details(
        self, 
        repo_url: str, 
        pr_number: int, 
        token: Optional[str] = None
    ) -> Dict:
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            headers["Authorization"] = f"token {token}"
            
        # get owner and repo from URL
        owner, repo = self._parse_repo_url(repo_url)
        
        # Get PR details
        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}",
            headers=headers
        )
        response.raise_for_status()
        
        return response.json()
    
    def get_pr_files(
        self, 
        repo_url: str, 
        pr_number: int, 
        token: Optional[str] = None
    ) -> List[Dict]:
        headers = self._get_headers(token)
        owner, repo = self._parse_repo_url(repo_url)
        
        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/pulls/{pr_number}/files",
            headers=headers
        )
        response.raise_for_status()
        return response.json()

    def get_file_content(
        self, 
        repo_url: str, 
        file_path: str, 
        commit_sha: str,
        token: Optional[str] = None
    ) -> str:
        headers = self._get_headers(token)
        owner, repo = self._parse_repo_url(repo_url)
        
        response = requests.get(
            f"{self.base_url}/repos/{owner}/{repo}/contents/{file_path}?ref={commit_sha}",
            headers=headers
        )
        response.raise_for_status()
        
        content = response.json()
        if "content" in content:
            return base64.b64decode(content["content"]).decode('utf-8')
        return ""

    def _get_headers(self, token: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Accept": "application/vnd.github.v3+json"
        }
        if token:
            headers["Authorization"] = f"token {token}"
        return headers
  
    def _parse_repo_url(self, repo_url: str) -> tuple[str, str]:
        # pulling owner and repo from GitHub URL
        parts = repo_url.rstrip("/").split("/")
        return parts[-2], parts[-1]