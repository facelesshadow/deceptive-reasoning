from core.graphs import build_graph
from langchain_google_genai import ChatGoogleGenerativeAI
model = ChatGoogleGenerativeAI(model="gemini-2.0-flash-lite", google_api_key="...")

print(model.invoke("HEY"))

graph = build_graph(model)

print(graph.invoke({"messages":"Can you write me a report on laptop?"}))