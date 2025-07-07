import pandas as pd

import streamlit as st
from src.components.performance_metrics import render_performance_metrics
from src.components.task_tracker import TaskTracker
from src.nl2sql.nl2sql import convert_nl2sql
from src.nl2sql.prompt.prompt_builder import prompt_factory
from src.nl2sql.utils.data_builder import load_data
from src.nl2sql.utils.enums import EXAMPLE_TYPE, REPR_TYPE, SELECTOR_TYPE
from src.render_utils import generate_text_stream
from src.sql_utils import execute_sql_select, get_sqlite_connection


class QueryPilotChat:
    def __init__(self):
        self.PATH_DATA = "BIRD_dataset/"
        self.prompt_repr = REPR_TYPE.CODE_REPRESENTATION
        self.example_type = EXAMPLE_TYPE.QA
        self.selector_type = SELECTOR_TYPE.EUC_DISTANCE_QUESTION_MASK
        self.k_shot = 7
        self.MAX_ROWS = 100  # Maximum number of rows to return
        self.DATABASE_PATH = "./BIRD_dataset/databases/financial/financial.sqlite"

    def initialize_session_state(self):
        """Initialize session state variables"""
        if "initialized" not in st.session_state:
            st.session_state.initialized = False
            st.session_state.data = None
            st.session_state.prompt = None
            st.session_state.task_tracker = TaskTracker()

        if "messages" not in st.session_state:
            st.session_state.messages = []

    def initialize_data_and_prompt(self):
        """Initialize data and prompt if not already done"""
        if not st.session_state.initialized:
            with st.spinner("Initializing Query Pilot..."):
                st.session_state.data = load_data("bird", self.PATH_DATA, None)
                databases = st.session_state.data.get_databases()
                print("start getting prompt")
                st.session_state.prompt = prompt_factory(
                    self.prompt_repr, self.k_shot, self.example_type, self.selector_type
                )(data=st.session_state.data, tokenizer="None")
                print("done getting prompt")

                # Mark initialization as complete
                st.session_state.initialized = True

    def render_chat_history(self):
        """Display existing chat messages"""
        for _, msg in enumerate(st.session_state.messages):
            with st.chat_message(msg["role"]):
                if "text" in msg:
                    st.write(msg["text"])
                if "table" in msg:
                    st.dataframe(msg["table"])
                if "chart" in msg:
                    st.line_chart(msg["chart"])
                if "task_summary" in msg and msg["task_summary"]:
                    summary = msg["task_summary"]
                    with st.expander("📊 Performance Metrics"):
                        col1, col2, col3 = st.columns(3)
                        with col1:
                            st.metric(
                                "Stage 1 (NL→SQL)", f"{summary.get('stage1_duration_s', 0):.1f}s"
                            )
                        with col2:
                            st.metric(
                                "Stage 2 (Execution)",
                                f"{summary.get('execution_duration_s', 0):.1f}s",
                            )
                        with col3:
                            st.metric("Total Time", f"{summary.get('total_duration_s', 0):.1f}s")

                        if summary.get("rows_returned"):
                            st.metric("Rows Returned", summary["rows_returned"])

    def process_user_question(self, question: str):
        """Process a user question through the complete pipeline"""
        # Create a container for the new conversation
        new_conversation_container = st.container()

        # Step 1: User provides a prompt - Start task tracking
        with new_conversation_container:
            with st.chat_message("user"):
                st.markdown(question)
        st.session_state.messages.append({"role": "user", "text": question})

        # Start tracking this task
        task_tracker = st.session_state.task_tracker
        task_id = task_tracker.start_task(question)

        # Step 2: Generate SQL from natural language
        final_sql_select = self._generate_sql(question, task_tracker, new_conversation_container)
        if not final_sql_select:
            return

        # Step 3: Execute SQL and get results
        sql_execution_result = self._execute_sql(
            final_sql_select, task_tracker, new_conversation_container
        )
        if sql_execution_result is None:
            return

        # Step 4: Generate response
        self._generate_response(sql_execution_result, task_tracker, new_conversation_container)

        # Add JavaScript to scroll to the new conversation
        st.markdown(
            """
            <script>
            // Scroll to the bottom of the page to show new content
            window.scrollTo(0, document.body.scrollHeight);
            </script>
            """,
            unsafe_allow_html=True,
        )

    def _generate_sql(self, question: str, task_tracker: TaskTracker, container) -> str | None:
        """Generate SQL from natural language question"""
        final_sql_select = ""
        is_valid_sql_generated = False

        with get_sqlite_connection(self.DATABASE_PATH) as conn:
            # Stage 1: Natural Language to SQL Generation
            with container:
                with st.spinner(
                    "🔄 Stage 1: Converting natural language to SQL...", show_time=True
                ):
                    retry_counter = 1
                    retry_limit = 3

                    while not is_valid_sql_generated and retry_counter <= retry_limit:
                        # Convert text (prompt) to SQL with task tracking
                        generated_sql_select = convert_nl2sql(
                            question, st.session_state.data, st.session_state.prompt, task_tracker
                        )

                        # # Validate sql syntax
                        # is_valid_sql_in_loop, validate_message = validate_sql_query(conn, generated_sql)
                        # if not is_valid_sql_in_loop:
                        #     st.write(f"Can not generate valid SQL in #{retry_counter} attempt(s).")
                        #     st.write(f"Reason: {validate_message}")
                        #     retry_counter += 1
                        #     continue

                        # # Analyze sql performance
                        # is_performant_query, analyze_message = analyze_query_plan(conn, generated_sql)
                        # if not is_performant_query:
                        #     st.write(f"Generated SQL is not performant in #{retry_counter} attempt(s).")
                        #     st.write(f"Reason: {analyze_message}")
                        #     retry_counter += 1
                        #     continue

                        is_valid_sql_generated = True
                        final_sql_select = generated_sql_select

            if not is_valid_sql_generated:
                with container:
                    st.write(f"Failed to generate valid SQL after {retry_limit} attempts.")
                task_tracker.record_error(
                    f"Failed to generate valid SQL after {retry_limit} attempts"
                )
                return None

            # Show Stage 1 completion
            task_summary = task_tracker.get_task_summary()
            with container:
                if task_summary.get("stage1_duration_s"):
                    st.success(f"✅ Stage 1 completed in {task_summary['stage1_duration_s']:.1f}s")
                    st.write(f"Generated SQL query: `{final_sql_select}`")

        return final_sql_select

    def _execute_sql(
        self, final_sql_select: str, task_tracker: TaskTracker, container
    ) -> pd.DataFrame | None:
        """Execute SQL query and return results"""
        sql_execution_result: pd.DataFrame | None = None

        with get_sqlite_connection(self.DATABASE_PATH) as conn:
            with container:
                with st.spinner("⚡ Stage 2: Executing SQL query...", show_time=True):
                    try:
                        # First, get total count of rows
                        count_query = (
                            f"SELECT COUNT(*) as total_rows FROM ({final_sql_select}) as subquery"
                        )
                        total_rows = execute_sql_select(conn, count_query, task_tracker).iloc[0][
                            "total_rows"
                        ]

                        # Add LIMIT clause if not present
                        if "LIMIT" not in final_sql_select.upper():
                            final_sql_select = f"{final_sql_select} LIMIT {self.MAX_ROWS}"

                        sql_execution_result = execute_sql_select(
                            conn, final_sql_select, task_tracker
                        )

                        # Add warning if results are truncated
                        if total_rows > self.MAX_ROWS:
                            st.warning(
                                f"⚠️ Results are limited to {self.MAX_ROWS} rows out of {total_rows} total rows. Please refine your query for more specific results."
                            )

                    except Exception as err:
                        st.write(
                            f"Can't execute the generated SQL: {final_sql_select} due to {err}"
                        )
                        task_tracker.record_error(str(err))
                        return None

            # Show Stage 2 completion
            task_summary = task_tracker.get_task_summary()
            print(f"task_summary: {task_summary}")
            with container:
                if task_summary.get("execution_duration_s"):
                    st.success(
                        f"✅ Stage 2 completed in {task_summary['execution_duration_s']:.4f}s"
                    )
                    st.write(f"Executing SQL successfully: `{final_sql_select}`")

        return sql_execution_result

    def _generate_response(
        self, sql_execution_result: pd.DataFrame, task_tracker: TaskTracker, container
    ):
        """Generate and display the response to the user"""
        with container:
            with st.chat_message("assistant"):
                # Mock data generation for text, table, and chart
                text_stream = generate_text_stream("This is a text answer to the query.")
                table_data = sql_execution_result
                chart_data = sql_execution_result

                full_text = ""
                if text_stream is not None:
                    st.write("Text Answer:")
                    full_text = st.write_stream(text_stream)

                if table_data is not None:
                    st.write("Table Answer:")
                    st.dataframe(table_data)

                # if chart_data is not None:
                #    st.write("Chart Answer:")
                #    st.line_chart(chart_data)

        final_task_summary = task_tracker.get_task_summary()
        render_performance_metrics(final_task_summary, container)

        st.session_state.messages.append(
            {
                "role": "assistant",
                "text": full_text,
                "table": table_data,
                "chart": chart_data,
                "task_summary": final_task_summary,
            }
        )
