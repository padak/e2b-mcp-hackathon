"""Arena Orchestrator - Runs evaluations across models, modes, and trials.

The orchestrator:
1. Loads questions from data source
2. For each (question, model, mode, trial) combination:
   - Spawns E2B sandbox
   - Uploads and runs arena_runner.py
   - Collects results
3. Aggregates results for scoring
"""

import asyncio
import json
import logging
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

from e2b_code_interpreter import Sandbox

from .data.loader import load_questions, load_sample_questions
from .data.questions import Question
from .models.config import ModelConfig, get_model, get_default_models, MODELS

logger = logging.getLogger(__name__)


@dataclass
class RunConfig:
    """Configuration for an arena run."""

    questions_path: Optional[str] = None  # None = use sample questions
    models: list[str] = field(default_factory=lambda: ["gpt-4o-mini"])
    modes: list[str] = field(default_factory=lambda: ["direct", "simulation"])
    trials: int = 1
    max_questions: Optional[int] = None
    max_turns: int = 10
    output_dir: str = "results/arena"


@dataclass
class RunResult:
    """Result of a single evaluation run."""

    question_id: str
    model_id: str
    mode: str
    trial: int
    success: bool
    prediction: Optional[dict]  # {probability, reasoning, valid}
    metrics: dict
    duration_s: float
    error: Optional[str] = None
    resolved_outcome: Optional[float] = None  # Ground truth

    def to_dict(self) -> dict:
        return {
            "question_id": self.question_id,
            "model_id": self.model_id,
            "mode": self.mode,
            "trial": self.trial,
            "success": self.success,
            "prediction": self.prediction,
            "metrics": self.metrics,
            "duration_s": self.duration_s,
            "error": self.error,
            "resolved_outcome": self.resolved_outcome,
        }


class ArenaOrchestrator:
    """Orchestrates arena evaluations across models and questions."""

    def __init__(
        self,
        config: RunConfig,
        api_key: Optional[str] = None,
    ):
        """Initialize the orchestrator.

        Args:
            config: Run configuration
            api_key: OpenRouter API key (or from OPENROUTER_API_KEY env var)
        """
        self.config = config
        self.api_key = api_key or os.environ.get("OPENROUTER_API_KEY")
        self.results: list[RunResult] = []

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")

    def load_questions(self) -> list[Question]:
        """Load questions based on config."""
        if self.config.questions_path:
            questions = load_questions(
                self.config.questions_path,
                max_questions=self.config.max_questions,
            )
        else:
            questions = load_sample_questions()
            if self.config.max_questions:
                questions = questions[: self.config.max_questions]

        logger.info(f"Loaded {len(questions)} questions")
        return questions

    def get_models(self) -> list[ModelConfig]:
        """Get model configurations."""
        models = []
        for model_key in self.config.models:
            try:
                models.append(get_model(model_key))
            except KeyError:
                # Allow direct OpenRouter model IDs
                models.append(
                    ModelConfig(
                        id=model_key,
                        name=model_key,
                        provider="openrouter",
                        router_id=model_key,
                        input_price=0,
                        output_price=0,
                        context_length=128000,
                    )
                )
        return models

    def run(self) -> list[RunResult]:
        """Run the full arena evaluation (synchronous wrapper)."""
        return asyncio.run(self.run_async())

    async def run_async(self) -> list[RunResult]:
        """Run the full arena evaluation."""
        questions = self.load_questions()
        models = self.get_models()

        total_runs = (
            len(questions)
            * len(models)
            * len(self.config.modes)
            * self.config.trials
        )
        logger.info(
            f"Starting arena: {len(questions)} questions × "
            f"{len(models)} models × {len(self.config.modes)} modes × "
            f"{self.config.trials} trials = {total_runs} runs"
        )

        run_count = 0
        for question in questions:
            for model in models:
                for mode in self.config.modes:
                    for trial in range(1, self.config.trials + 1):
                        run_count += 1
                        logger.info(
                            f"[{run_count}/{total_runs}] "
                            f"{question.id} | {model.id} | {mode} | trial {trial}"
                        )

                        result = await self._run_single(
                            question=question,
                            model=model,
                            mode=mode,
                            trial=trial,
                        )
                        self.results.append(result)

                        # Log result
                        if result.success and result.prediction:
                            pred = result.prediction["probability"]
                            logger.info(f"  → Prediction: {pred:.2%}")
                        else:
                            logger.warning(f"  → Failed: {result.error}")

        return self.results

    async def _run_single(
        self,
        question: Question,
        model: ModelConfig,
        mode: str,
        trial: int,
    ) -> RunResult:
        """Run a single evaluation in E2B sandbox."""
        try:
            result_dict = await self._run_in_sandbox(
                question=question,
                model=model,
                mode=mode,
                trial=trial,
            )

            return RunResult(
                question_id=question.id,
                model_id=model.id,
                mode=mode,
                trial=trial,
                success=result_dict.get("success", False),
                prediction=result_dict.get("prediction"),
                metrics=result_dict.get("metrics", {}),
                duration_s=result_dict.get("duration_s", 0),
                error=result_dict.get("error"),
                resolved_outcome=question.resolved_outcome,
            )

        except Exception as e:
            logger.error(f"Sandbox error: {e}")
            return RunResult(
                question_id=question.id,
                model_id=model.id,
                mode=mode,
                trial=trial,
                success=False,
                prediction=None,
                metrics={},
                duration_s=0,
                error=str(e),
                resolved_outcome=question.resolved_outcome,
            )

    async def _run_in_sandbox(
        self,
        question: Question,
        model: ModelConfig,
        mode: str,
        trial: int,
    ) -> dict:
        """Execute arena runner in E2B sandbox."""
        # Create sandbox
        sbx = Sandbox.create()

        try:
            # Install dependencies
            sbx.commands.run("pip install -q openai")

            # Upload runner files
            runner_code = self._get_runner_code()
            sbx.files.write("/home/user/arena_runner.py", runner_code)

            tools_code = self._get_tools_code()
            sbx.files.write("/home/user/tools.py", tools_code)

            hooks_code = self._get_hooks_code()
            sbx.files.write("/home/user/hooks.py", hooks_code)

            prompts_code = self._get_prompts_code()
            sbx.files.write("/home/user/prompts.py", prompts_code)

            # Build command
            cmd = (
                f"cd /home/user && OPENROUTER_API_KEY='{self.api_key}' "
                f"python arena_runner.py "
                f'--question "{question.question}" '
                f'--description "{question.description or ""}" '
                f'--market-id "{question.id}" '
                f"--volume {question.volume} "
                f'--closed-time "{question.closed_time or ""}" '
                f"--mode {mode} "
                f'--model "{model.id}" '
                f"--trial {trial} "
                f"--max-turns {self.config.max_turns}"
            )

            # Run
            result = sbx.commands.run(cmd, timeout=240)

            if result.exit_code != 0:
                return {
                    "success": False,
                    "error": f"Exit code {result.exit_code}: {result.stderr}",
                }

            # Parse JSON output
            try:
                return json.loads(result.stdout)
            except json.JSONDecodeError as e:
                return {
                    "success": False,
                    "error": f"Invalid JSON output: {e}\nStdout: {result.stdout[:500]}",
                }

        finally:
            sbx.kill()

    def _get_runner_code(self) -> str:
        """Get arena_runner.py source code."""
        path = Path(__file__).parent / "runner" / "arena_runner.py"
        return path.read_text()

    def _get_tools_code(self) -> str:
        """Get tools.py source code."""
        path = Path(__file__).parent / "runner" / "tools.py"
        return path.read_text()

    def _get_hooks_code(self) -> str:
        """Get hooks.py source code."""
        path = Path(__file__).parent / "runner" / "hooks.py"
        return path.read_text()

    def _get_prompts_code(self) -> str:
        """Get prompts.py source code."""
        path = Path(__file__).parent / "runner" / "prompts.py"
        return path.read_text()

    def save_results(self, output_dir: Optional[str] = None) -> str:
        """Save results to JSON file.

        Args:
            output_dir: Output directory (default from config)

        Returns:
            Path to saved file
        """
        output_dir = output_dir or self.config.output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = Path(output_dir) / f"arena_results_{timestamp}.json"

        data = {
            "timestamp": timestamp,
            "config": {
                "questions_path": self.config.questions_path,
                "models": self.config.models,
                "modes": self.config.modes,
                "trials": self.config.trials,
                "max_questions": self.config.max_questions,
            },
            "results": [r.to_dict() for r in self.results],
            "summary": self._compute_summary(),
        }

        with open(output_path, "w") as f:
            json.dump(data, f, indent=2)

        logger.info(f"Results saved to {output_path}")
        return str(output_path)

    def _compute_summary(self) -> dict:
        """Compute summary statistics."""
        total = len(self.results)
        successful = sum(1 for r in self.results if r.success)
        with_prediction = sum(1 for r in self.results if r.prediction)

        return {
            "total_runs": total,
            "successful_runs": successful,
            "runs_with_prediction": with_prediction,
            "success_rate": successful / total if total > 0 else 0,
            "prediction_rate": with_prediction / total if total > 0 else 0,
        }


async def run_arena(
    models: list[str] = None,
    modes: list[str] = None,
    trials: int = 1,
    max_questions: int = None,
    questions_path: str = None,
    output_dir: str = "results/arena",
) -> list[RunResult]:
    """Convenience function to run arena evaluation.

    Args:
        models: List of model keys (default: ["gpt-4o-mini"])
        modes: List of modes (default: ["direct", "simulation"])
        trials: Number of trials per combination
        max_questions: Max questions to evaluate
        questions_path: Path to questions JSON (default: sample questions)
        output_dir: Output directory for results

    Returns:
        List of RunResult objects
    """
    config = RunConfig(
        questions_path=questions_path,
        models=models or ["gpt-4o-mini"],
        modes=modes or ["direct", "simulation"],
        trials=trials,
        max_questions=max_questions,
        output_dir=output_dir,
    )

    orchestrator = ArenaOrchestrator(config)
    results = await orchestrator.run_async()
    orchestrator.save_results()

    return results
