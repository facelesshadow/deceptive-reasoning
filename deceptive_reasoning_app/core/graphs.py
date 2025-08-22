from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
from langgraph.graph import StateGraph, MessagesState, START, END

class ExtendedState(MessagesState):
      parsed_problem: str
      plans: str
      sims: str
      recommend: str
      recommended_plan: str
      refined_plan: str

def build_graph(model):
  
  # model.invoke("hey")

  

  # Pretty rudimentary State for now, it ll work though


  def llm(state):
      print("LLM Node")
      return {"messages": model.invoke(state["messages"])}

  def cache(state):
      print('waste')
      return {"messages": state["messages"]}

      
  def parse_problem(state):
      prompt = f"""
  You are a problem parser.  
  Your task is to deeply understand the user's request and extract:  
  1. **Two Core objectives** : the main things they want.  
  2. **Constraints** : any limits, rules, or conditions.  
  3. **Key entities** : important objects, people, variables, or data.  
  4. **Success criteria** : what a good answer must achieve.  

  Do not solve the problem. Only rewrite and structure it for later reasoning.  
  Return the output as structured JSON.
  Problem:
      {state['messages']}
  """
      sys_msg = SystemMessage(content=prompt)
      return {'parsed_problem': model.invoke(prompt)}

  def generate_plans(state):
      prompt = f"""
  You are a strategic planner.  
  Given the parsed problem (core objective, constraints, key entities, success criteria),  
  generate multiple possible solution approaches.  

  Rules:  
  - Propose at least 3 distinct plans.  
  - Each plan should list the main steps, assumptions, and potential risks.  
  - Plans should stay within the provided constraints.  
  - Do not execute the solution. Only outline strategies. 

  Return the output as structured JSON.
  Problem:
  {state['parsed_problem']}
  """
      
      return {'plans': model.invoke(prompt)}

  def simulator(state):
      prompt1 = """You are a logical reasoner.  
  Given the problems and multiple solution plans, your job is to simulate each plan step-by-step,  
  check its feasibility, and evaluate it against the problem's constraints and success criteria.  

  Rules:
  - For each plan, simulate the steps in order.  
  - After each step, note expected outcomes and possible issues.  
  - Identify where the plan may fail or need adjustments.  
  - Do not give the final answer yet — only reasoning traces and evaluations.  

  Return output as JSON.
  Simulate reasoning in this format:
  "plan_evaluations": [
      {
        "plan_name": "Approach 1",
        "reasoning_chain": [
          {"step": "...", "expected_outcome": "...", "possible_issues": ["..."]},
          {"step": "...", "expected_outcome": "...", "possible_issues": ["..."]}
        ],
        "overall_feasibility": "High | Medium | Low",
        "notes": "..."
      },
      {
        "plan_name": "Approach 2",
        "reasoning_chain": [...],
        "overall_feasibility": "...",
        "notes": "..."
      }
    ]
  }
  """
      prompt2 = f"""
    Parsed Problems:
    {state['parsed_problem']}
    Solution Plans:
    {state['plans']}
  """
      return {'sims': model.invoke(prompt1 + prompt2)}


  def critique(state):
      prompt1 = f"""You are a self-critique and evaluation module.  
      Given simulated reasoning chains for multiple plans,  
      your task is to critically review them, identify flaws, and select the most promising approach.  

      Rules:  
      - Compare feasibility, risk, and alignment with success criteria.  
      - Point out specific weaknesses or logical gaps in each plan.  
      - Recommend one plan as the best candidate, with justification.  
      - Do not solve the problem — only select and justify the choice.  

      Return output as JSON.
      PARSED PROBLEM:
      {state['parsed_problem']}

      PLAN EVALUATIONS:
      {state['plans']}

      SIMULATIONS:
      {state['sims']}"""

      prompt2 = """Evaluate and select in this format:
      {
      "plan_reviews": [
          {
          "plan_name": "Approach 1",
          "strengths": ["...", "..."],
          "weaknesses": ["...", "..."],
          "risk_level": "High | Medium | Low",
          "alignment_with_criteria": "Strong | Moderate | Weak"
          },
          {
          "plan_name": "Approach 2",
          "strengths": [...],
          "weaknesses": [...],
          "risk_level": "...",
          "alignment_with_criteria": "..."
          }
      ],
      "recommended_plan": {
          "name": "...",
          "justification": "..."
      }
      }
      """
      
      return {'recommend': model.invoke(prompt1 + prompt2)}

  def recommended_plan(state):
      
      """
      string2 =    "recommended_plan": {
      #       "name": "...",
      #        "justification": "..."
        #  }
      #   
      string2.split("recommended_plan")[1:]"""


      recommend_plan_str = state['recommend'].content
      return {"recommended_plan": recommend_plan_str.split('recommended_plan')[1:]}

  def refiner(state):
    prompt1 = f"""
        You are a plan refiner.  
        Given the recommended plan and its identified weaknesses,  
        your job is to improve it while keeping the core objective and constraints intact.  

        Rules:  
        - Address each weakness directly with concrete changes.  
        - Reduce risk and improve feasibility.  
        - Keep all steps logically connected.  
        - If the plan is fundamentally flawed, propose a revised version from scratch that is stronger.  
        - Do not produce the final answer — only the improved plan.  

        Return output as JSON.
        
    PARSED PROBLEM:
    {state["parsed_problem"]}

    RECOMMENDED PLAN:
    {state['recommended_plan']}
        """
    prompt2 = """
  Refine the plan in this format:
  {
    "refined_plan": {
      "name": "...",
      "steps": ["...", "..."],
      "changes_made": ["...", "..."],
      "risk_level": "High | Medium | Low",
      "notes": "..."
    }
  }
    """

    return {'refined_plan': model.invoke(prompt1 + prompt2)}

  def final_answer(state):
      prompt1 = f"""
  You are a solution generator.  
  Given the refined plan, produce the final answer for the user.  

  Rules:  
  - Execute the refined plan step-by-step logically.  
  - Make sure all constraints are respected.  
  - Clearly explain the reasoning that led to this solution (summary form, not full internal thoughts).  
  - Present the answer in a clear, actionable, and well-structured format.  
  - If relevant, include recommended next steps or additional considerations.  

  Return only the final answer to the user — no JSON, no internal reasoning.

  PARSED PROBLEM:
  {state["parsed_problem"]}

  REFINED PLAN:
  {state['refined_plan']}

  Produce the final answer for the user in natural language.
  """
      return {'messages': model.invoke(prompt1)}

  builder_final = StateGraph(ExtendedState)


  builder_final.add_node('parse_problem', parse_problem)
  builder_final.add_node('generate_plans', generate_plans)
  builder_final.add_node('simulator', simulator)
  builder_final.add_node('critique', critique)
  builder_final.add_node('recommended_plan', recommended_plan)
  builder_final.add_node('refiner', refiner)
  builder_final.add_node('final_answer', final_answer)


  builder_final.add_edge(START, "parse_problem")
  builder_final.add_edge("parse_problem", "generate_plans")
  builder_final.add_edge("generate_plans", "simulator")
  builder_final.add_edge("simulator", "critique")
  builder_final.add_edge("critique", "recommended_plan")
  builder_final.add_edge("recommended_plan", "refiner")
  builder_final.add_edge("refiner", "final_answer")
  # builder_final.add_edge("finaL_answer", END)

  graph_final = builder_final.compile()
  return graph_final
#__all__ = ["graph_final"]
  # builder_final.compile()