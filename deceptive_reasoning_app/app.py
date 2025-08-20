from core.graphs import graph_final
from langchain_core.messages import AIMessage

import streamlit as st

st.title("LangGraph Planner Demo")
user_input = st.text_area("Enter your problem:")



# User input
# user_input = st.text_area("Enter your problem:")

NODE_LABELS = {
    "parse_problem": "Understanding the problem...",
    "generate_plans": "Generating Plans...",
    "simulator": "Simulating...",
    "critique": "Critiquing...",
    "recommended_plan": "Choosing best path...",
    "refiner": "Refining the approach...",
    "final_answer": "Final Answer"
}

if st.button("Run"):
    if user_input.strip():
        st.info("Streaming results...")

        final_placeholder = st.empty()

        for event in graph_final.stream({"messages": [("user", user_input)]}):
            for node, state in event.items():
                # Extract clean text
                val = None
                if isinstance(state, dict):
                    first_val = list(state.values())[0]
                    if isinstance(first_val, AIMessage):
                        val = first_val.content
                    else:
                        val = str(first_val)
                else:
                    val = str(state)

                label = NODE_LABELS.get(node, node)

                if node == "final_answer":
                    final_placeholder.subheader(label)
                    final_placeholder.write(val)
                else:
                    with st.expander(label, expanded=False):
                        st.write(val)

        st.success("Completed.")
    else:
        st.warning("Please enter a problem first.")