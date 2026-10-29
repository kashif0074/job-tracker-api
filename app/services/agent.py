import os
import json
from typing import Annotated, TypedDict

from langchain_groq import ChatGroq
from langchain_core.tools import tool
from langchain_core.messages import HumanMessage
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
from langgraph.graph.message import add_messages

from app.services.scraper import scrape_job_sync


@tool
def scrape_job(url: str) -> str:
    """Scrape a job posting URL and return the title and description."""
    result = scrape_job_sync(url)
    if not result["success"]:
        return f"Failed to scrape: {result['error']}"
    return f"Title: {result['title']}\n\nDescription: {result['description']}"


@tool
def extract_skills_from_text(text: str) -> str:
    """Extract required skills from a job description."""
    from app.services.ai_service import extract_skills
    skills = extract_skills(text)
    return json.dumps(skills)


tools = [scrape_job, extract_skills_from_text]

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    api_key=os.getenv("GROQ_API_KEY"),
    temperature=0,
)
llm_with_tools = llm.bind_tools(tools)


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


def agent_node(state: AgentState):
    return {"messages": [llm_with_tools.invoke(state["messages"])]}


graph_builder = StateGraph(AgentState)
graph_builder.add_node("agent", agent_node)
graph_builder.add_node("tools", ToolNode(tools))
graph_builder.set_entry_point("agent")


def should_continue(state: AgentState):
    last = state["messages"][-1]
    if hasattr(last, "tool_calls") and last.tool_calls:
        return "tools"
    return END


graph_builder.add_conditional_edges(
    "agent", should_continue, {"tools": "tools", END: END}
)
graph_builder.add_edge("tools", "agent")

agent_app = graph_builder.compile()


async def run_agent(user_prompt: str) -> str:
    """
    Run the agent with a user prompt.
    Returns the final message content.
    """
    initial_state = {"messages": [HumanMessage(content=user_prompt)]}
    result = await agent_app.ainvoke(initial_state)
    return result["messages"][-1].content