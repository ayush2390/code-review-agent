# GitHub Code Review Agent

This project implements an autonomous code review agent system that utilizes AI to analyze GitHub pull requests. The agent leverages a combination of FastAPI, Celery, and a chosen LLM model (or Ollama for local model running) to provide efficient and insightful code reviews.

PS : I have deployed this project on vercel as serverless functions but in free version I can start long running celery workers on vercel hence it is not working on free deployment :(

## Features

* **Asynchronous Processing:** 
    * Utilizes Celery for efficient task handling and improved performance.
    * Stores task results in [**Redis**] for easy retrieval and persistence.
    * Implements robust task status tracking (pending, completed, failed).
    * Handles errors gracefully with informative error messages.

* **AI-Powered Code Analysis:**
    * Analyzes code for:
        * Code style and formatting issues
        * Potential bugs and errors
        * Performance improvements
        * Best practices adherence
    * Employs langchain for intelligent code analysis.

* **FastAPI-Based API:**
    * Exposes the following endpoints:
        * **POST /analyze-pr:** Accepts GitHub PR details (repo, PR number) and initiates the code review process.
        * **GET /status/<task_id>:** Retrieves the current status of a specific analysis task.
        * **GET /results/<task_id>:** Fetches the detailed analysis results for a given task.

* **User-Friendly Output:**
    * Provides structured analysis results in JSON format, including:
        * List of files with identified issues.
        * Detailed information about each issue (type, line number, description, suggestion).
        * Summary of the overall code review findings.

## Installation

1. **Clone the repository:**

   ```bash
   git clone https://github.com/your-username/github-code-review-agent.git
   ```
2. **got to the repository:**
   ```bash
   cd github-code-review-agent
   ```
3. **Create the virtual environment:**
   ```bash
   python3 -m venv venv
   ```
4. **Activate the environment:**
   ```bash
   source venv/bin/activate  # For Windows: venv\Scripts\activate
   ```
5. **Install the requirements:**
   ```bash
   pip install -r requirements.txt
    ```
6. **Start the server:**
   ```bash
   uvicorn app.main:app --reload
    ```

5. **Start the Celery worker in a different terminal:**
   ```bash
   celery -A app.worker worker --loglevel=info
    ```
## Dummy Env file

```bash
CELERY_BROKER_URL=redis://127.0.0.1:6379/0
CELERY_RESULT_BACKEND=redis://127.0.0.1:6379/0
LLM_API_KEY=your_llm_api_key (OpenAI Secret key)
```
## Design document (How this Project is built ?)

- This project includes 3 APIs mainly "/analyze-pr", "/status/{task_id}", "result/{task_id}"
- When you will hit the post method on first api /analyze-pr it will invoke a celery task in background
- this task will create an CodeReviewAgent which will analyze github PRs
- now this CodeReviewAgent has a method analyze_pr which will fetch pr_details and files
- and now these files will be passed through 4 Different Analyzers 
- BugAnaylzer, StyleAnalyzer, PerformanceAnalyzer and BestPractice analyzer
- These analyzers classes have analyze method defined in them which will parse the file content into tree using (AST- abstract syntax tree)
- we are using this tree nodes to visit the code and check the issues or any errors
- if any issue is found we are storing it into CodeIssue data class
- and then we are return all the issues and their proper details in the response
- we can fetch status of the task using "/status/{task_id}" api 
- and we can get result of the task using "/result/{task_id}" api
- I have broken down code into different modules, GithubClient , CodeReviewAgent, Analyzers
