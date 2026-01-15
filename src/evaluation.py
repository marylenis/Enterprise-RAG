import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import (
    faithfulness,
    answer_relevancy,
    context_recall,
    context_precision,
    context_entity_recall,
    answer_correctness,
)
from src.containers import Container
from src.hybrid_engine import HybridQueryEngine
from src.vector_store import VectorIndexManager
from src.graph_manager import GraphManager


class RAGEvaluator:
    def __init__(self):
        self.container = Container()
        self.hybrid_engine = self.container.hybrid_engine()
        self.vector_manager = self.container.vector_manager()
        self.graph_manager = self.container.graph_manager()

        # Evaluation metrics
        self.metrics = [
            faithfulness,
            answer_relevancy,
            context_recall,
            context_precision,
            context_entity_recall,
            answer_correctness,
        ]

    def create_evaluation_dataset(self, test_queries: List[Dict[str, Any]]) -> Dataset:
        """
        Create evaluation dataset from test queries
        Expected format: [
            {
                "question": "What is the company's policy on remote work?",
                "ground_truth": "The company allows remote work up to 3 days per week...",
                "contexts": ["Relevant document excerpt 1", "Relevant document excerpt 2"],
                "reference": "Optional reference answer"
            }
        ]
        """
        dataset_dict = {
            "question": [],
            "ground_truth": [],
            "contexts": [],
            "answer": [],
            "reference": [],
        }

        for query_data in test_queries:
            # Get response from our RAG system
            response = self.hybrid_engine.custom_query(query_data["question"])

            dataset_dict["question"].append(query_data["question"])
            dataset_dict["ground_truth"].append(query_data["ground_truth"])
            dataset_dict["contexts"].append(query_data.get("contexts", []))
            dataset_dict["answer"].append(str(response))
            dataset_dict["reference"].append(query_data.get("reference", ""))

        return Dataset.from_dict(dataset_dict)

    async def evaluate_system(
        self, test_queries: List[Dict[str, Any]], save_results: bool = True
    ) -> Dict[str, Any]:
        """
        Evaluate the RAG system using RAGAS metrics
        """
        print("Creating evaluation dataset...")
        dataset = self.create_evaluation_dataset(test_queries)

        print("Running RAGAS evaluation...")
        results = evaluate(dataset=dataset, metrics=self.metrics)

        # Convert results to dictionary
        results_dict = results.to_pandas().to_dict("records")

        # Calculate overall statistics
        overall_scores = {}
        for metric in self.metrics:
            metric_name = metric.name
            scores = [
                result[metric_name] for result in results_dict if metric_name in result
            ]
            if scores:
                overall_scores[metric_name] = {
                    "mean": sum(scores) / len(scores),
                    "min": min(scores),
                    "max": max(scores),
                    "std": (
                        sum((x - sum(scores) / len(scores)) ** 2 for x in scores)
                        / len(scores)
                    )
                    ** 0.5,
                }

        evaluation_report = {
            "timestamp": datetime.utcnow().isoformat(),
            "total_queries": len(test_queries),
            "overall_scores": overall_scores,
            "detailed_results": results_dict,
            "system_info": {
                "engine_type": "hybrid",
                "vector_store": "qdrant",
                "graph_store": "falkordb",
                "embedding_model": "text-embedding-3-small",
            },
        }

        if save_results:
            await self.save_evaluation_results(evaluation_report)

        return evaluation_report

    async def save_evaluation_results(self, results: Dict[str, Any]):
        """Save evaluation results to file and database"""
        # Save to file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"evaluation_results_{timestamp}.json"

        results_dir = "evaluations"
        os.makedirs(results_dir, exist_ok=True)

        filepath = os.path.join(results_dir, filename)
        with open(filepath, "w") as f:
            json.dump(results, f, indent=2)

        print(f"Evaluation results saved to: {filepath}")

        # TODO: Save to database for tracking over time
        # self.save_to_database(results)

    def generate_test_queries(self, domain: str = "enterprise") -> List[Dict[str, Any]]:
        """
        Generate sample test queries for evaluation
        """
        if domain == "enterprise":
            return [
                {
                    "question": "What is the company's remote work policy?",
                    "ground_truth": "The company allows employees to work remotely up to 3 days per week, with manager approval. All remote work arrangements must be documented in the HR system.",
                    "contexts": [
                        "Remote Work Policy: Employees may request remote work arrangements for up to 3 days per week. Manager approval required. All arrangements must be documented in HR system.",
                        "HR Guidelines: Remote work requests should be submitted through the employee portal and approved by direct managers within 5 business days.",
                    ],
                },
                {
                    "question": "How are performance reviews conducted?",
                    "ground_truth": "Performance reviews are conducted quarterly, with a formal annual review. Employees receive feedback from their manager and peers through the company's performance management system.",
                    "contexts": [
                        "Performance Review Process: Quarterly check-ins and annual formal reviews. Feedback collected from managers and peers through the performance management system.",
                        "Review Timeline: Q1-Q3 quarterly reviews, Q4 annual review with compensation discussion.",
                    ],
                },
                {
                    "question": "What are the IT security requirements?",
                    "ground_truth": "All employees must use company-approved devices, enable multi-factor authentication, and complete annual security training. Personal devices are prohibited for accessing company data.",
                    "contexts": [
                        "IT Security Policy: Company-approved devices only, MFA required for all systems, annual security training mandatory.",
                        "Device Management: Personal devices prohibited for company data access. All devices must be enrolled in mobile device management.",
                    ],
                },
                {
                    "question": "What benefits are available to employees?",
                    "ground_truth": "Employees receive health insurance, dental insurance, vision coverage, 401(k) with company match, paid time off, and professional development stipend. Benefits start on day 1 of employment.",
                    "contexts": [
                        "Employee Benefits: Health, dental, vision insurance, 401(k) with 4% match, PTO, professional development stipend. Benefits effective day 1.",
                        "Health Coverage: Multiple plan options available, company covers 80% of premium costs for employee-only coverage.",
                    ],
                },
                {
                    "question": "How does the expense reimbursement process work?",
                    "ground_truth": "Employees submit expenses through the Concur system within 30 days of purchase. Expenses require manager approval and receipt documentation. Reimbursement is processed within 2 weeks of approval.",
                    "contexts": [
                        "Expense Policy: Submit through Concur within 30 days, manager approval required, receipt documentation mandatory.",
                        "Reimbursement Timeline: Processed within 2 weeks of manager approval. Direct deposit preferred.",
                    ],
                },
            ]

        return []

    def compare_engines(self, test_queries: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Compare performance between hybrid and vector-only engines
        """
        print("Comparing engine performance...")

        results = {}

        # Test hybrid engine
        print("Testing hybrid engine...")
        hybrid_results = asyncio.run(
            self.evaluate_system(test_queries, save_results=False)
        )
        results["hybrid"] = hybrid_results["overall_scores"]

        # Test vector-only engine
        print("Testing vector-only engine...")
        # Temporarily switch engine
        original_engine = self.hybrid_engine
        self.hybrid_engine = self.container.vector_only_engine()

        vector_results = asyncio.run(
            self.evaluate_system(test_queries, save_results=False)
        )
        results["vector_only"] = vector_results["overall_scores"]

        # Restore original engine
        self.hybrid_engine = original_engine

        # Calculate improvement
        improvement = {}
        for metric in results["hybrid"]:
            if metric in results["vector_only"]:
                hybrid_score = results["hybrid"][metric]["mean"]
                vector_score = results["vector_only"][metric]["mean"]
                improvement[metric] = {
                    "absolute": hybrid_score - vector_score,
                    "percentage": ((hybrid_score - vector_score) / vector_score * 100)
                    if vector_score > 0
                    else 0,
                }

        results["improvement"] = improvement
        results["comparison_timestamp"] = datetime.utcnow().isoformat()

        return results

    async def run_continuous_evaluation(
        self,
        interval_hours: int = 24,
        test_queries: Optional[List[Dict[str, Any]]] = None,
    ):
        """
        Run continuous evaluation at specified intervals
        """
        if test_queries is None:
            test_queries = self.generate_test_queries()

        while True:
            print(f"Running scheduled evaluation at {datetime.now()}")

            try:
                results = await self.evaluate_system(test_queries)

                # Check if scores meet minimum thresholds
                thresholds = {
                    "faithfulness": 0.8,
                    "answer_relevancy": 0.7,
                    "context_precision": 0.8,
                    "context_recall": 0.7,
                }

                alerts = []
                for metric, threshold in thresholds.items():
                    if metric in results["overall_scores"]:
                        score = results["overall_scores"][metric]["mean"]
                        if score < threshold:
                            alerts.append(f"{metric}: {score:.3f} < {threshold}")

                if alerts:
                    print(f"⚠️ Quality alerts: {', '.join(alerts)}")
                    # TODO: Send alert to monitoring system
                else:
                    print("✅ All quality metrics above thresholds")

            except Exception as e:
                print(f"❌ Evaluation failed: {e}")

            # Wait for next interval
            await asyncio.sleep(interval_hours * 3600)


# CLI interface for running evaluations
if __name__ == "__main__":
    evaluator = RAGEvaluator()

    # Generate test queries
    test_queries = evaluator.generate_test_queries("enterprise")

    # Run evaluation
    print("Starting RAG system evaluation...")
    results = asyncio.run(evaluator.evaluate_system(test_queries))

    print("\n=== Evaluation Results ===")
    for metric, scores in results["overall_scores"].items():
        print(f"{metric}: {scores['mean']:.3f} (±{scores['std']:.3f})")

    print(f"\nDetailed results saved to: evaluations/")
