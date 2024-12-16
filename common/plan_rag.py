from common.llm import call_llm
from swarm.util import debug_print


def plan_rag_query(query, agent="finance", **kwargs):
    debug_print(True, f"Processing tool call: {plan_rag_query.__name__}")
    debug_print(True, f"Processing tree call: PLAN_RAG")
    if agent == "macro":
        plan_query = call_llm(
            f"""
            You are a helpful AI agent.
            You are tasked with writing a detailed step-by-step plan to answer the complex query given to you, which is: '{query}'.
            Your plan should focus specifically on conducting a domain analysis of the product and providing market insights about trends, opportunities, and competitors.
            Break down the query into sub-parts, determine retrieval points for each sub-part, and specify how to retrieve the relevant documents for each sub-part.
            Answer this question as a RAG planning agent and assume you have access to the appropriate documents and data as needed.
            The steps you generate need to be clear and should be written in a way that they can be input to another RAG model as queries for retrieval and step-by-step processing.
            Ensure each step of the plan is a separate line in the message and can also be used as a query for retrieval by another RAG agent.
            Put primary focus on the quality of the query for the RAG agent.
            Do NOT output a plan with more than 5 steps and try to minimize the number of steps to as low as possible, preferably 2 or 3.
            Do NOT include a final step to synthesize the information, only steps for retrieval as that will be done separately.

            Here is the step-by-step plan to conduct a domain analysis of the product and provide market insights:
            1. Identify the specific product field from the query (e.g., smartphones) and list all major companies in that field (e.g., Apple, Samsung, Xiaomi).
            2. Retrieve comprehensive data on each identified company, including market share, product offerings, recent innovations, financial performance, and customer demographics.
            3. Analyze the competitive landscape by identifying key competitors, their strengths and weaknesses, and their market strategies.
            4. Investigate current market trends related to the product field, focusing on consumer preferences, technological advancements, and regulatory influences.
            5. Identify potential opportunities for growth and innovation within the product field, considering emerging markets and shifts in consumer behavior.
            """
        )
        return plan_query

    if agent == "M&A":
        companies = kwargs.get("companies")
        input_docs = kwargs.get("input_docs")
        output_doc = kwargs.get("output_doc")
        if companies is None or len(companies) != 2:
            raise ValueError("The 'companies' argument is required for the M&A agent.")
        if input_docs is None:
            raise ValueError("The 'input_docs' argument is required for the M&A agent.")
        if output_doc is None:
            raise ValueError("The 'output_doc' argument is required for the M&A agent.")

        prompt = f"""
        You are a helpful AI agent.
        You are tasked with writing a detailed step-by-step plan to formulate a merger and acquisition agreement between two companies, {companies[0]} and {companies[1]}.
        Currently, you are in the process of drafting the {output_doc} document.
        For this, you will break down the process into multiple steps, each of which will involve retrieving relevant information from the following documents: {', '.join(input_docs)} of both the companies.
        Your plan should include steps to retrieve information from each document and how to combine them to form the final agreement.
        Answer this question as a RAG planning agent and assume you have access to the appropriate documents and data as is needed.
        The steps you generate need to be clear, and should be written in a way that they can be input to another RAG model as queries for retrieval and step-by-step processing.
        Ensure each step of the plan is a separate line in the message and that can also be used a query for retrieval by another RAG agent.
        Put primary focus on the quality of the query for the RAG agent.
        Output a plan with a minimal number of steps, preferrably 3-4.
        Do NOT include a final step to synthesize the information, only steps for retrieval as that will be done separately.
        """
        plan_query = call_llm(prompt)
        return plan_query

    if agent == "CA":
        userinfo = kwargs.get("userinfo")
        if userinfo is None:
            userinfo = "You do not have any user information."
        section = kwargs.get("section")
        userinfo_str = "\n\n".join(userinfo)
        prompt = f"""
        You are a helpful AI agent.
        You are tasked with writing a detailed step-by-step plan to answer the query '{query}' for a user.
        Your job is to write a detailed step-by-step plan that answers the query.
        You should use the information provided in the document and any relevant resources available to you.
        The relevant information is that you are an expert in the field of chartered accountancy and finance, particularly in the area of income tax laws and regulations in India.
        You need to search for the information related to the sections on section {', '.join(section)} in the documents inputted by the user.
        The relevant documents input by the user are described as:
        {userinfo_str}
        Ensure your plan has only 2-3 steps. Do NOT include a final step to synthesize the information, only steps for retrieval as that will be done separately.
        An example plan would be that the first step is to retrieve the user's relevant documents and the second step is to retrieve the relevant information from the income tax laws.
        Ensure each step of the plan is a separate line in the message and that can also be used a query for retrieval by another RAG agent.
        """
        plan_query = call_llm(prompt)
        debug_print(True, f"Plan query: {plan_query}")
        return plan_query
    expertise = " "
    if agent == "finance":
        expertise = "You are an expert in the field of finance. Your answer should be tailored accordingly."
    elif agent == "legal":
        expertise = (
            "You are a legal expert. Your answer should be tailored accordingly."
        )

    plan_query = call_llm(
        f"""
        You are a helpful AI agent.
        You are tasked with writing a detailed step-by-step plan to answer the complex query given to you, which is: '{query}'.
        Your plan should include steps as to process each part of the query.
        This is done by breaking down the query into sub-parts, then determining retrieval points for each sub-part, followed by finally retrieving the documents for each sub-part along with a description of how the parts should be combined to form the final answer.
        Answer this question as a RAG planning agent and assume you have access to the appropriate documents and data as is needed.
        The steps you generate need to be clear, and should be written in a way that they can be input to another RAG model as queries for retrieval and step-by-step processing.
        Ensure each step of the plan is a separate line in the message and that can also be used a query for retrieval by another RAG agent.
        Put primary focus on the quality of the query for the RAG agent.
        {expertise}
        Do NOT output a plan with more than 3 steps and try to minimise the number of steps to as low as possible, preferrably 2 or 3.
        Do NOT include a final step to synthesize the information, only steps for retrieval as that will be done separately.
        """
    )

    return plan_query


def single_plan_rag_step_query(step):
    debug_print(True, f"Processing tool call: {single_plan_rag_step_query.__name__}")
    query_prompt = f"""You are a helpful prompt engineering assistant that must generate a query to feed to an LLM based on the given step in a multi-step plan.
        The step you must generate a query for is: {step}
        The query you generate should be clear and concise, and should be designed to retrieve the most relevant documents and information for the given step.
        It should be a query and not a statement, and must be no longer than 2 sentences.
        You must keep in mind that you are an expert in the field of finance and legalities, and that the query you generate should be tailored accordingly.
        """
    query_ = call_llm(query_prompt)
    return query_
