from langchain_ollama import ChatOllama
from pydantic import BaseModel
from typing import List, Literal
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import MessagesState, START, END, StateGraph
from typing import Literal, List, Annotated
import operator
from langgraph.types import Send
from typing import TypedDict
from langgraph.types import interrupt



class Answer(BaseModel):
    response: Literal["Yes", "No"]

class State(MessagesState):
    answers: Annotated[List[Literal["Yes", "No"]], operator.add]
    problems: list
    solutions: Annotated[list, operator.add]
    final_ans: Annotated[list, operator.add]


class SolvingState(TypedDict):
    # messages: list  # if you're passing chat history through state
    what: str

class Solutions(BaseModel):
    solutions: List[str]


model = ChatOllama(model='gemma3:1b', temperature=0)
model_yn = model.with_structured_output(Answer)
solutions_model = model.with_structured_output(Solutions)



def assistant(state):
    prompt = """You are given a query / task. If you understand the query / have knowledge about the topic, return a 'Yes'.
    If you don't have clarity on the asked topic / query, simply return a 'No'.
    """
    response = model_yn.invoke([SystemMessage(content=prompt), state['messages'][-1]])
    return({'answers':[response.response]})

def check(state) -> Literal['solution_planner', 'fallback']:
    if(state['answers'][-1] == 'Yes'):
        return "solution_planner"
    elif(state['answers'][-1] == 'No'):
        return 'fallback'
    
def fallback(state):
    user_value = interrupt(f"Can you rephrase your question '{state['messages'][-1]}': ")

    prompt = """You are given a query / task. If you understand the query / have knowledge about the topic, return a 'Yes'.
    If you don't have clarity on the asked topic / query, simply return a 'No'.
    """
    response = model_yn.invoke([SystemMessage(content=prompt), user_value])

    return ({'messages': HumanMessage(content=user_value), 'answers': [response.response]})

def solution_planner(state):
    prompt = '''You are a problem solving planner. You are given a query / task by the user. 
    You have to break the problem down into smaller problems, and return all the smaller problems. 
    Each smaller problem statement should be as small as possible, and all of them combined should totally cover the whole problem.
    '''

    solutions = solutions_model.invoke([SystemMessage(content=prompt), state['messages'][-1]])
    return ({'problems': solutions.solutions})

def reduce1(state):
    return [
        Send("solving_node", {**state, "problems": p})
        for p in state["problems"]
    ]
    

def solving_node(state: SolvingState):
    print("Solving Node: Solution: ")
    prompt = """You are a problem solver. Given the main problem statement, and a smaller part of the problem, 
    You are to solve the SMALLER part of the problem in max 30 words.
    """
    human_prompt = f"""Problem Statement: "{state['messages'][-1].content}"
    Smaller Problem: "{state['problems']}"
    """
    answer = model.invoke([SystemMessage(content=prompt), HumanMessage(content=human_prompt)])
    return ({'solutions': [answer.content]})

def final_solver(state):
    print("Final Solution Node")
    solutions_string = " | ".join([s for s in state['solutions']])
    prompt = """You are a Markdown Writer. Given a problem statement / query / task, and answers seperated by '|'.
    you are to write an answer which contains each of the smaller answers, into one Final Answer.
    Do not add information from your own, only use the information provided in the context. 
    """
    human_prompt = f"""Problem Statement: "{state['messages'][-1].content}"
    Smaller solutions: "{solutions_string}"
    """
    answer = model.invoke([SystemMessage(content=prompt), HumanMessage(content=human_prompt)])
    return ({'final_ans': [answer.content], 'messages':answer})

builder = StateGraph(State)

builder.add_node("assistant", assistant)
builder.add_node('fallback', fallback)
builder.add_node('solution_planner', solution_planner)
builder.add_node('solving_node', solving_node)
builder.add_node('final_solver', final_solver)

builder.add_edge(START, 'assistant')
builder.add_conditional_edges('assistant', check)
builder.add_conditional_edges('fallback', check)
builder.add_conditional_edges("solution_planner", reduce1, ["solving_node"])
builder.add_edge('solving_node', 'final_solver')
builder.add_edge('final_solver', END)

graph = builder.compile()