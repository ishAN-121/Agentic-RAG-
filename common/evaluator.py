from typing import Dict, Any, Tuple
import json
from .llm import call_llm
from agent import run_pipeline

class EvaluationCriteria:
    relevance_threshold: float = 0.7
    quality_threshold: float = 0.7
    evaluation_aspects = [
        "relevance",
        "factual_accuracy",
        "completeness",
        "coherence",
        "context_usage"
    ]

class LLMEvaluatorAgent:
    def __init__(
        self,
        criteria: EvaluationCriteria = EvaluationCriteria()
    ):

    def create_evaluation_prompt(
        self, 
        query: str, 
        response: str, 
        context: str = None
    ) -> str:
        """Create a structured prompt for LLM evaluation."""
        return f"""You are an expert evaluator for RAG systems. Evaluate the following response based on these criteria:

    Query: {query}

    Response to evaluate: {response}

    Retrieved Context: {context if context else 'No context provided'}

    For each aspect below, provide:
    1. A score between 0.0 and 1.0
    2. A brief justification

    Evaluate these aspects:
    - relevance: How well does the response address the query?
    - factual_accuracy: Are the facts consistent with the context?
    - completeness: Does the response fully address all aspects of the query?
    - coherence: Is the response well-structured and logical?
    - context_usage: How effectively is the provided context utilized?

    Provide your evaluation in JSON format:
    {{
        "aspect_name": {{
            "score": float,
            "justification": "string"
        }}
    }}"""


    def evaluate_response(
        self, 
        query: str, 
        response: str, 
        context: str = None
    ) -> Tuple[bool, Dict[str, Any]]:
        """
        Evaluate response using LLM-based analysis.
        Returns (is_acceptable, detailed_metrics)
        """
        evaluation_prompt = self.create_evaluation_prompt(query, response, context)
        llm_response = call_llm(evaluation_prompt)
        try:
            evaluation_results = json.loads(llm_response[7:-3])
            metrics = {
                aspect: {
                    "score": evaluation_results[aspect]["score"],
                    "justification": evaluation_results[aspect]["justification"]
                }
                for aspect in self.criteria.evaluation_aspects
            }

            overall_score = sum(
                metrics[aspect]["score"] 
                for aspect in self.criteria.evaluation_aspects
            ) / len(self.criteria.evaluation_aspects)

            relevance_score = metrics["relevance"]["score"]

            is_acceptable = (
                relevance_score >= self.criteria.relevance_threshold and
                overall_score >= self.criteria.quality_threshold
            )

            metrics["overall_score"] = overall_score

            return is_acceptable, metrics

        except json.JSONDecodeError:
            return False, {"error": "Failed to parse LLM evaluation"}

class EnhancedRAGPipeline:
    def __init__(self):
        self.evaluator = LLMEvaluatorAgent()

    def generate_response(self, query: str, max_retries: int = 2) -> Dict[str, Any]:
        """Enhanced pipeline with LLM evaluation and detailed feedback."""
        attempts = []

        for attempt in range(max_retries):
            response,context = run_pipeline(query)

            is_acceptable, metrics = self.evaluator.evaluate_response(
                query, response, context
            )

            attempts.append({
                "attempt": attempt + 1,
                "response": response,
                "metrics": metrics
            })

            if is_acceptable:
                return {
                    "final_response": response,
                    "evaluation_metrics": metrics,
                    "attempts": attempts
                }

        best_attempt = max(attempts, key=lambda x: x["metrics"].get("overall_score", 0))
        return {
            "final_response": best_attempt["response"],
            "evaluation_metrics": best_attempt["metrics"],
            "attempts": attempts,
            "warning": "Max retries reached without meeting quality thresholds"
        }

