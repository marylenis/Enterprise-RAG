#!/usr/bin/env python3
"""
Automated evaluation pipeline for Enterprise RAG system
"""

import asyncio
import argparse
import json
from datetime import datetime
from src.evaluation import RAGEvaluator


async def main():
    parser = argparse.ArgumentParser(description="Run RAG system evaluation")
    parser.add_argument(
        "--mode",
        choices=["single", "compare", "continuous"],
        default="single",
        help="Evaluation mode",
    )
    parser.add_argument(
        "--domain", default="enterprise", help="Domain for test queries"
    )
    parser.add_argument(
        "--interval", type=int, default=24, help="Interval in hours for continuous mode"
    )
    parser.add_argument("--output", help="Output file for results")
    parser.add_argument("--queries", help="JSON file with custom test queries")

    args = parser.parse_args()

    evaluator = RAGEvaluator()

    # Load custom queries if provided
    if args.queries:
        with open(args.queries, "r") as f:
            test_queries = json.load(f)
    else:
        test_queries = evaluator.generate_test_queries(args.domain)

    print(f"🚀 Starting RAG evaluation in {args.mode} mode")
    print(f"📊 Domain: {args.domain}")
    print(f"📝 Test queries: {len(test_queries)}")

    if args.mode == "single":
        results = await evaluator.evaluate_system(test_queries)

        print("\n=== Evaluation Results ===")
        for metric, scores in results["overall_scores"].items():
            print(f"{metric}: {scores['mean']:.3f} (±{scores['std']:.3f})")

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Results saved to: {args.output}")

    elif args.mode == "compare":
        results = evaluator.compare_engines(test_queries)

        print("\n=== Engine Comparison ===")
        print("Hybrid Engine Scores:")
        for metric, scores in results["hybrid"].items():
            print(f"  {metric}: {scores['mean']:.3f}")

        print("\nVector-Only Engine Scores:")
        for metric, scores in results["vector_only"].items():
            print(f"  {metric}: {scores['mean']:.3f}")

        print("\nImprovements:")
        for metric, improvement in results["improvement"].items():
            print(
                f"  {metric}: {improvement['absolute']:+.3f} ({improvement['percentage']:+.1f}%)"
            )

        if args.output:
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\n💾 Comparison saved to: {args.output}")

    elif args.mode == "continuous":
        print(f"🔄 Starting continuous evaluation every {args.interval} hours")
        await evaluator.run_continuous_evaluation(args.interval, test_queries)


if __name__ == "__main__":
    asyncio.run(main())
