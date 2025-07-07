import uuid
from datetime import datetime
from typing import Any


class TaskTracker:
    """
    Tracks the two-stage process of natural language to SQL conversion and execution.

    Stage 1: Natural Language to SQL Generation
    Stage 2: SQL Query Execution
    """

    def __init__(self):
        self.session_tasks: dict[str, dict[str, Any]] = {}
        self.current_task_id: str | None = None

    def start_task(self, user_input: str) -> str:
        """
        Start tracking a new task when user enters natural language query.

        Args:
            user_input (str): The natural language query from user

        Returns:
            str: Unique task ID for this session
        """
        task_id = str(uuid.uuid4())
        current_time = datetime.now()

        self.current_task_id = task_id
        self.session_tasks[task_id] = {
            "task_id": task_id,
            "user_input": user_input,
            "nl_timestamp": current_time,
            "sql_generation_timestamp": None,
            "stage1_duration_s": None,
            "sql_generated": None,
            "sql_execution_timestamp": None,
            "execution_duration_s": None,
            "rows_returned": None,
            "status": "started",
            "error_message": None,
            "retry_count": 0,
            "total_duration_s": None,
        }

        return task_id

    def record_sql_generation(self, sql_query: str) -> None:
        """
        Record when SQL query is generated (end of Stage 1).

        Args:
            sql_query (str): The generated SQL query
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return

        current_time = datetime.now()
        task = self.session_tasks[self.current_task_id]

        task["sql_generated"] = sql_query
        task["sql_generation_timestamp"] = current_time
        task["stage1_duration_s"] = round((current_time - task["nl_timestamp"]).total_seconds(), 2)
        task["status"] = "sql_generated"

    def record_sql_execution_start(self) -> None:
        """
        Record when SQL execution begins (start of Stage 2).
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return

        current_time = datetime.now()
        task = self.session_tasks[self.current_task_id]

        task["sql_execution_timestamp"] = current_time
        task["status"] = "executing"

    def record_sql_execution_complete(
        self, rows_returned: int, execution_duration_s: float
    ) -> None:
        """
        Record when SQL execution completes (end of Stage 2).

        Args:
            rows_returned (int): Number of rows returned by the query
            execution_duration_s (float): Duration of SQL execution in seconds
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return

        current_time = datetime.now()
        task = self.session_tasks[self.current_task_id]

        task["rows_returned"] = rows_returned
        task["execution_duration_s"] = execution_duration_s
        task["status"] = "completed"
        task["total_duration_s"] = round((current_time - task["nl_timestamp"]).total_seconds(), 2)

    def record_error(self, error_message: str) -> None:
        """
        Record error information if something goes wrong.

        Args:
            error_message (str): Description of the error
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return

        task = self.session_tasks[self.current_task_id]
        task["error_message"] = error_message
        task["status"] = "error"

    def increment_retry(self) -> None:
        """
        Increment retry counter when retrying a failed operation.
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return

        self.session_tasks[self.current_task_id]["retry_count"] += 1

    def get_current_task(self) -> dict[str, Any] | None:
        """
        Get the current task data.

        Returns:
            Optional[Dict[str, Any]]: Current task data or None if no current task
        """
        if not self.current_task_id or self.current_task_id not in self.session_tasks:
            return None

        return self.session_tasks[self.current_task_id].copy()

    def get_task_summary(self) -> dict[str, Any]:
        """
        Get a summary of the current task with key metrics.

        Returns:
            Dict[str, Any]: Task summary with timing information
        """
        task = self.get_current_task()
        if not task:
            return {}

        return {
            "task_id": task["task_id"],
            "status": task["status"],
            "stage1_duration_s": task["stage1_duration_s"],
            "execution_duration_s": task["execution_duration_s"],
            "total_duration_s": task["total_duration_s"],
            "rows_returned": task["rows_returned"],
            "retry_count": task["retry_count"],
            "error_message": task["error_message"],
        }

    def get_session_history(self) -> list:
        """
        Get all tasks from the current session.

        Returns:
            list: List of all task summaries in the session
        """
        return [self.session_tasks[task_id] for task_id in self.session_tasks]

    def clear_session(self) -> None:
        """
        Clear all session data.
        """
        self.session_tasks.clear()
        self.current_task_id = None
