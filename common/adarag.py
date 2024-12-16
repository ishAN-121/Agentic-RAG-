from swarm import Agent
from finance_agent.agent import transfer_to_finance_agent
from legal_agent.agent import transfer_to_legal_agent
from general_agent.agent import transfer_to_general_agent
from swarm.util import debug_print


def adarag_agent():
    debug_print(True, f"Processing tool call: {adarag_agent.__name__}")
    debug_print(True, f"Processing tree call: AdaRAG")
    return Agent(
        name="AdaRAG",
        instructions="""You are an expert in routing user questions to agents which can answer finance specific queries or legal specific queries or other, general, queries""",
        functions=[
            transfer_to_finance_agent,
            transfer_to_legal_agent,
            transfer_to_general_agent,
        ],
    )
