"""CLI for LLM Prediction Arena.

Usage:
    python -m arena run [OPTIONS]
    python -m arena score RESULTS_FILE
    python -m arena list-models
"""

import argparse
import asyncio
import json
import logging
import sys
from pathlib import Path

# Load environment variables from .env
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not installed, rely on environment variables

from .orchestrator import ArenaOrchestrator, RunConfig
from .scoring import score_results_file, compare_models
from .models.config import MODELS, get_default_models

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def cmd_run(args):
    """Run arena evaluation."""
    config = RunConfig(
        questions_path=args.questions,
        models=args.models.split(",") if args.models else ["gpt-4o-mini"],
        modes=args.modes.split(",") if args.modes else ["direct", "simulation"],
        trials=args.trials,
        max_questions=args.max_questions,
        max_turns=args.max_turns,
        output_dir=args.output_dir,
    )

    print(f"\n{'='*60}")
    print("LLM PREDICTION ARENA")
    print(f"{'='*60}")
    print(f"Models: {config.models}")
    print(f"Modes: {config.modes}")
    print(f"Trials: {config.trials}")
    print(f"Max questions: {config.max_questions or 'all'}")
    print(f"{'='*60}\n")

    orchestrator = ArenaOrchestrator(config)

    try:
        results = orchestrator.run()
        output_path = orchestrator.save_results()

        print(f"\n{'='*60}")
        print("RESULTS SUMMARY")
        print(f"{'='*60}")
        print(f"Total runs: {len(results)}")
        print(f"Successful: {sum(1 for r in results if r.success)}")
        print(f"With prediction: {sum(1 for r in results if r.prediction)}")
        print(f"\nResults saved to: {output_path}")

        # Score if we have results
        if results:
            scores = score_results_file(output_path)
            scores.print_summary()

    except KeyboardInterrupt:
        print("\n\nInterrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error: {e}")
        sys.exit(1)


def cmd_score(args):
    """Score existing results file."""
    if not Path(args.results_file).exists():
        print(f"Error: File not found: {args.results_file}")
        sys.exit(1)

    scores = score_results_file(args.results_file)
    scores.print_summary()

    if args.compare:
        rankings = compare_models(scores)
        print("\n" + "=" * 60)
        print("MODEL RANKINGS")
        print("=" * 60)

        for mode in ["direct", "simulation"]:
            ranking_key = f"{mode}_ranking"
            if rankings.get(ranking_key):
                print(f"\n{mode.upper()} MODE:")
                for r in rankings[ranking_key]:
                    print(f"  #{r['rank']}: {r['model_id']} (Brier: {r['brier_score']:.4f})")


def cmd_list_models(args):
    """List available models."""
    print("\nAvailable Models:")
    print("-" * 60)
    print(f"{'Key':<20} {'Provider':<12} {'Model ID'}")
    print("-" * 60)

    for key, model in MODELS.items():
        default = " (default)" if key in ["gpt-4o", "claude-sonnet-4", "gemini-2.0-flash"] else ""
        print(f"{key:<20} {model.provider:<12} {model.id}{default}")

    print("-" * 60)
    print("\nDefault models for arena:")
    for m in get_default_models():
        print(f"  - {m.name} ({m.id})")


def cmd_quick_test(args):
    """Run a quick test with one question and one model."""
    config = RunConfig(
        questions_path=None,  # Use sample questions
        models=[args.model or "gpt-4o-mini"],
        modes=["direct", "simulation"],
        trials=1,
        max_questions=1,
        max_turns=5,
        output_dir="results/arena/quick_test",
    )

    print(f"\n{'='*60}")
    print("QUICK TEST")
    print(f"{'='*60}")
    print(f"Model: {config.models[0]}")
    print(f"Testing both direct and simulation modes")
    print(f"{'='*60}\n")

    orchestrator = ArenaOrchestrator(config)
    results = orchestrator.run()

    print(f"\n{'='*60}")
    print("QUICK TEST RESULTS")
    print(f"{'='*60}")

    for r in results:
        status = "✓" if r.success else "✗"
        pred = f"{r.prediction['probability']:.2%}" if r.prediction else "N/A"
        print(f"{status} {r.mode}: {pred}")
        if r.prediction:
            print(f"   Reasoning: {r.prediction['reasoning'][:80]}...")


def main():
    parser = argparse.ArgumentParser(
        description="LLM Prediction Arena - Benchmark LLMs on prediction markets",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run quick test with default model
  python -m arena quick-test

  # Run with specific models
  python -m arena run --models gpt-4o-mini,claude-sonnet-4

  # Run only simulation mode with 3 trials
  python -m arena run --modes simulation --trials 3

  # Score existing results
  python -m arena score results/arena/arena_results_20241201_120000.json
        """,
    )

    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Run command
    run_parser = subparsers.add_parser("run", help="Run arena evaluation")
    run_parser.add_argument(
        "--questions",
        type=str,
        default=None,
        help="Path to questions JSON file (default: sample questions)",
    )
    run_parser.add_argument(
        "--models",
        type=str,
        default=None,
        help="Comma-separated list of models (default: gpt-4o-mini)",
    )
    run_parser.add_argument(
        "--modes",
        type=str,
        default=None,
        help="Comma-separated modes: direct,simulation (default: both)",
    )
    run_parser.add_argument(
        "--trials",
        type=int,
        default=1,
        help="Number of trials per combination (default: 1)",
    )
    run_parser.add_argument(
        "--max-questions",
        type=int,
        default=None,
        help="Maximum number of questions (default: all)",
    )
    run_parser.add_argument(
        "--max-turns",
        type=int,
        default=10,
        help="Max conversation turns per run (default: 10)",
    )
    run_parser.add_argument(
        "--output-dir",
        type=str,
        default="results/arena",
        help="Output directory (default: results/arena)",
    )

    # Score command
    score_parser = subparsers.add_parser("score", help="Score existing results")
    score_parser.add_argument("results_file", type=str, help="Path to results JSON file")
    score_parser.add_argument(
        "--compare",
        action="store_true",
        help="Show model comparison rankings",
    )

    # List models command
    subparsers.add_parser("list-models", help="List available models")

    # Quick test command
    quick_parser = subparsers.add_parser("quick-test", help="Run quick test")
    quick_parser.add_argument(
        "--model",
        type=str,
        default=None,
        help="Model to test (default: gpt-4o-mini)",
    )

    args = parser.parse_args()

    if args.command == "run":
        cmd_run(args)
    elif args.command == "score":
        cmd_score(args)
    elif args.command == "list-models":
        cmd_list_models(args)
    elif args.command == "quick-test":
        cmd_quick_test(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
