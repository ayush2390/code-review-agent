from langchain_openai import ChatOpenAI
from langchain.agents import initialize_agent, Tool
from langchain.memory import ConversationBufferMemory
from .github import GitHubClient
from .analyzers import (
    StyleAnalyzer,
    BugAnalyzer,
    PerformanceAnalyzer,
    BestPracticesAnalyzer
)
import logging
from typing import Dict, List, Any, Set

logger = logging.getLogger(__name__)
class CodeReviewAgent:
    def __init__(self, llm_api_key: str):
        self.llm = ChatOpenAI(api_key=llm_api_key)
        self.github_client = GitHubClient()
        self.memory = ConversationBufferMemory()
        self.analyzers = self._initialize_analyzers()
        self.tools = self._initialize_tools()
        self.agent = initialize_agent(
            self.tools,
            self.llm,
            agent="conversational-react-description",
            memory=self.memory
        )
    
    def _initialize_analyzers(self):
        return {
            "style": StyleAnalyzer(),
            "bugs": BugAnalyzer(),
            "performance": PerformanceAnalyzer(),
            "best_practices": BestPracticesAnalyzer()
        }

    def _initialize_tools(self):
        return [
            Tool(
                name="Style Analysis",
                func=self.analyzers["style"].analyze,
                description="Analyze code style and formatting"
            ),
            Tool(
                name="Bug Analysis",
                func=self.analyzers["bugs"].analyze,
                description="Detect potential bugs and errors"
            ),
            Tool(
                name="Performance Analysis",
                func=self.analyzers["performance"].analyze,
                description="Identify performance improvements"
            ),
            Tool(
                name="Best Practices",
                func=self.analyzers["best_practices"].analyze,
                description="Check adherence to best practices"
            )
        ]
    
    def analyze_pr(
        self, 
        repo_url: str, 
        pr_number: int, 
        github_token: str | None = None
    ) -> Dict[str, Any]:
        try:
            
            pr_data = self.github_client.get_pr_details(repo_url, pr_number, github_token) # fetch pr details
            pr_files = self.github_client.get_pr_files(repo_url, pr_number, github_token)  # fetch pr files
            
            results = {
                "pr_number": pr_number,
                "repo_url": repo_url,
                "files": [],
                "summary": {
                    "total_files": len(pr_files),
                    "total_issues": 0,
                    "critical_issues": 0,
                    "issues_by_type": {
                        "style": 0,
                        "bug": 0,
                        "performance": 0,
                        "best_practice": 0
                    }
                }
            }

            # Analyze each file
            for file_info in pr_files:
                # not analyzing deleted files
                if file_info["status"] == "removed":
                    continue
                
                # Get file content from the PR's head commit
                file_content = self.github_client.get_file_content(
                    repo_url,
                    file_info["filename"],
                    pr_data["head"]["sha"],
                    github_token
                )
                
                if not file_content:
                    logger.warning(f"Could not get content for file: {file_info['filename']}")
                    continue

                file_analysis = self._analyze_file(
                    filename=file_info["filename"],
                    content=file_content,
                    patch=file_info.get("patch", "")
                )
                
                results["files"].append(file_analysis)
                
                # Update summary statistics
                self._update_summary_stats(results["summary"], file_analysis["issues"])

            return results

        except Exception as e:
            logger.error(f"Error analyzing PR: {str(e)}")
            raise
    
    def _analyze_file(
        self, 
        filename: str, 
        content: str,
        patch: str
    ) -> Dict[str, Any]:
        """Analyze a single file using all available analyzers."""
        file_result = {
            "name": filename,
            "issues": [],
            "patch": patch
        }
        print("This is the content of the file",content)
        # Only analyze certain file types
        if not self._should_analyze_file(filename):
            return file_result

        try:
            # Run all analyzers
            for analyzer_type, analyzer in self.analyzers.items():
                issues = analyzer.analyze(content)
                for issue in issues:
                    issue["analyzer"] = analyzer_type
                file_result["issues"].extend(issues)

            # Sort issues by line number
            file_result["issues"].sort(key=lambda x: x["line"])

        except Exception as e:
            logger.error(f"Error analyzing file {filename}: {str(e)}")
            file_result["issues"].append({
                "type": "error",
                "line": 0,
                "description": f"Error analyzing file: {str(e)}",
                "suggestion": "Please check file content and format",
                "severity": "high"
            })

        return file_result

    def _should_analyze_file(self, filename: str) -> bool:
        """Determine if a file should be analyzed based on its extension."""
        analyzable_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', 
            '.java', '.cpp', '.hpp', '.c', '.h',
            '.go', '.rs', '.rb', '.php'
        }
        return any(filename.endswith(ext) for ext in analyzable_extensions)

    def _update_summary_stats(
        self, 
        summary: Dict[str, Any], 
        issues: List[Dict[str, Any]]
    ) -> None:
        """Update the summary statistics with issues from a file."""
        summary["total_issues"] += len(issues)
        
        for issue in issues:
            # Update issues by type
            issue_type = issue.get("type", "other")
            summary["issues_by_type"][issue_type] = \
                summary["issues_by_type"].get(issue_type, 0) + 1
            
            # Update critical issues count
            if issue.get("severity") in ["high", "critical"]:
                summary["critical_issues"] += 1
                
