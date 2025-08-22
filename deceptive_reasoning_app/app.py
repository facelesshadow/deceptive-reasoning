from core.graphs import build_graph
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain_core.messages import AIMessage
import streamlit as st


st.title("Deceptive Reasoning")
st.text("A langgraph reasoning alternative for non-reasoning Language models.")
# user_input = st.text_area("Enter your problem:")
st.sidebar.title("🔧 Settings")
provider = st.sidebar.selectbox("Select Provider", ["Gemini", "Groq"])


model = None
if provider == "Gemini":
    gemini_api_key = st.sidebar.text_input("Enter Gemini API Key", type="password")
    if gemini_api_key:
        model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            api_key=gemini_api_key
        )

elif provider == "Groq":
    groq_api_key = st.sidebar.text_input("Enter Groq API Key", type="password")
    if groq_api_key:
        model = ChatGroq(
            model="llama-3.1-8b-instant",
            api_key=groq_api_key
        )

if model:
    st.success(f"{provider} model loaded ✅")
    graph_final = build_graph(model)   # <-- pass model in
    # now run the graph with user input...
else:
    st.warning("Enter API key to start")


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



user_input = st.text_area("Enter your problem:")
    # if st.button("Run"):


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