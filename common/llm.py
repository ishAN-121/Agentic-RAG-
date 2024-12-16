from typing import Optional
from langchain_openai import ChatOpenAI
import requests


def call_llm(prompt, call_o1: Optional[bool] = False):
    try:
        if call_o1:
            return call_o1(prompt)
        return call_openai_4o_mini(prompt)
    except:
        try:
            return call_llama_7b(prompt)
        except:
            return "Error: No LLM model available."


def call_llama_7b(prompt):
    response = requests.post(
        "https://8003-01jdya9bpnhj5dqyfzh17zdghv.cloudspaces.litng.ai/predict",
        json={"input": prompt},
    )
    return response.json()["output"]["content"]


def call_openai_4o_mini(prompt):
    llm = ChatOpenAI(model="gpt-4o-mini")
    return llm.invoke(prompt).content


def call_openai_o1(prompt):
    llm = ChatOpenAI(model="o1-mini")
    return llm.invoke(prompt).content
