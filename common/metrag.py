from common.llm import call_llm
from nltk.sentiment.vader import SentimentIntensityAnalyzer
import numpy as np
from swarm.util import debug_print
from concurrent.futures import ThreadPoolExecutor


def metrag_score(document, query, agent, doc_):
    debug_print(True, f"Processing tool call: {metrag_score.__name__}")
    debug_print(True, f"Processing tree call: MetRAG")
    good_utility = "The document is absolutely outstanding and exceeds expectations in addressing the query. It is exceptionally relevant, brilliantly complete, impeccably accurate, and presented with crystal-clear clarity. Its consistency is flawless, making it an invaluable and extraordinary resource of immense utility!"
    bad_utility = "The document is utterly disappointing and fails to meet even basic expectations in addressing the query. It lacks relevance, is incomplete, riddled with inaccuracies, and confusingly presented. Its inconsistency undermines any potential value, making it a frustrating and entirely unhelpful resource."
    prompt = f"""
    You are a helpful AI agent.
    You are tasked with evaluating the utility of a document in answering a query.
    Certain criteria for utility are defined as follows:
    - Relevance: How relevant is the document to the query?
    - Completeness: How complete is the information in the document?
    - Accuracy: How accurate is the information in the document?
    - Clarity: How clear and concise is the information in the document?
    - Consistency: How consistent is the information in the document?
    Point to Note: A document may not be semantically similar to the query but may still be useful in answering the query.
    A query which has high utility will be able to answer the query effectively and for such a query a possible output could be:
    '{good_utility}'
    A query which has low utility will not be able to answer the query effectively and for such a query a possible output could be:
    '{bad_utility}'
    Evaluate the utility of the following document in answering the query:
    '{query}'.
    The document is as follows:
    '{document}'
    """

    if agent == "finance":
        added_info = """
        You must keep in mind that you are an expert in the field of finance, and that the response you generate should be tailored accordingly.
        For instance, for relevancy you also need to consider whether the document contains the relevant terms and whether it is focused on the company which is the same as the query.
        If there is no reference to the company of the query in the document, it is not relevant, then output the same output as that for a low utility document.
        """
        prompt = prompt + added_info

    if agent == "legal":
        added_info = """
        You must keep in mind that you are a legal expert and that the response you generate should be tailored accordingly.
        For instance, for relevancy you also need to consider whether the document contains the relevant terms and whether it is focused on the terminologies and case information which are contained in the query.
        If there is no reference to the either of the terminologies or case information in the document, it is not relevant. In such cases, output the same response as that for a low utility document.
        """
        prompt = prompt + added_info

    if agent == "macro":
        added_info = """
        You must keep in mind that you are an expert in market analysis, and that the response you generate should be tailored accordingly.
        For instance, for relevancy, you need to consider whether the document contains relevant terms related to the product field and whether it focuses on the companies identified in the query (e.g., Apple, Samsung, Xiaomi).
        If there is no reference to the companies or the product field specified in the query within the document, it is not relevant. In such cases, output the same response as that for a low utility document.
        Additionally, ensure that the insights you provide are actionable and reflect current market trends, opportunities, and competitive dynamics.
        """
        prompt = prompt + added_info

    if agent == "M&A":
        added_info = """
        You must keep in mind that you are an expert in mergers and acquisitions, and that the response you generate should be tailored accordingly.
        For instance, for relevancy, you need to consider whether the document contains relevant information about the companies involved in the merger and acquisition agreement.
        If there is no reference to the companies or the agreement details in the document, it is not relevant. In such cases, output the same response as that for a low utility document.
        Additionally, ensure that the information retrieved from each document is accurate and can be used to draft the final agreement effectively.
        """
        prompt = prompt + added_info

    if agent == "CA":
        added_info = """
        You must keep in mind that you are an expert in customer assistance, and that the response you generate should be tailored accordingly.
        For instance, for relevancy, you need to consider whether the document contains relevant information about the user and/or the query and its relevant income tax deductions, and related sections
        If there is no reference to any such information in the document, it is not relevant. In such cases, output the same response as that for a low utility document.
        Additionally, ensure that the document provides clear and accurate information that can assist in answering the query effectively.
        """
        prompt = prompt + added_info

    response = call_llm(prompt)
    return doc_, SentimentIntensityAnalyzer().polarity_scores(response).get("compound")


def metrag_filter(documents, query, agent):
    debug_print(True, f"Processing tool call: {metrag_filter.__name__}")
    with ThreadPoolExecutor() as executor:
        if type(documents[0]) == str:
            documents = [{"text": doc} for doc in documents]
        results = executor.map(
            lambda doc: metrag_score(doc["text"], query, agent, doc), documents
        )
    score_dict = [result for result in results]
    if len(score_dict) == 0:
        return []
    metrag_threshold = np.percentile(list([b for (a, b) in score_dict]), 25)
    return [doc for (doc, score) in score_dict if score > metrag_threshold]
