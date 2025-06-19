import streamlit as st

def render_performance_metrics(task_summary: dict, new_conversation_container=None):
    with new_conversation_container:
        with st.expander("📊 Performance Metrics"):
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Stage 1 (NL→SQL)", f"{task_summary.get('stage1_duration_s', 0):.1f}s")
            with col2:
                st.metric("Stage 2 (Execution)", f"{task_summary.get('execution_duration_s', 0):.4f}s")
            with col3:
                st.metric("Total Time", f"{task_summary.get('total_duration_s', 0):.1f}s")
    
            if task_summary.get('rows_returned'):
                st.metric("Rows Returned", task_summary['rows_returned'])
