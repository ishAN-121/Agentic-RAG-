from swarm import Agent
from general_agent.zero_retrieval import zero_retrieval_agent
from general_agent.single_retrieval import single_retrieval_agent
from general_agent.multi_retrieval import multi_retrieval_agent
from swarm.util import debug_print


def transfer_to_general_agent() -> Agent:
    debug_print(True, f"Processing tree call: GENERAL_QUERY")
    """Transfer queries to expert agent"""
    return Agent(
        name="General Agent",
        instructions="You are an expert at routing queries to a zero, single or multi-retrieval agent based on the complexity of the query. Since you are domain agnostic, route the queries based on whether or not the query requires zero, single or multiple RAG steps.",
        functions=[zero_retrieval_agent,single_retrieval_agent, multi_retrieval_agent],
    )
