"""Arena Orchestrator - Runs evaluations across models, modes, and trials.

The orchestrator:
1. Loads questions from data source
2. Creates a single E2B sandbox (reused across all runs)
3. For each (question, model, mode, trial) combination:
   - Runs arena_runner.py in the shared sandbox
   - Collects results
4. Aggregates results for scoring

Optimizations:
- Sandbox reuse: Single sandbox for all runs (saves ~10-15s per run)
- Dependency caching: pip install once at sandbox creation
- File upload caching: Upload runner files once
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

# Cache for runner code (avoid re-reading files)
_runner_code_cache: dict[str, str] = {}


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
    log: Optional[dict] = None  # Full conversation log with tool calls

    def to_dict(self) -> dict:
        result = {
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
        # Include log only if present (can be large)
        if self.log:
            result["log"] = self.log
        return result


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

        # Sandbox management
        self._sandbox: Optional[Sandbox] = None
        self._sandbox_initialized: bool = False

        if not self.api_key:
            raise ValueError("OPENROUTER_API_KEY required")

    def _create_sandbox(self) -> Sandbox:
        """Create and initialize a sandbox with dependencies."""
        logger.info("Creating E2B sandbox (60 min lifetime)...")
        sbx = Sandbox.create(timeout=3600)  # 60 minutes lifetime

        # Install dependencies once
        logger.info("Installing dependencies (openai, mesa, numpy)...")
        sbx.commands.run("pip install -q openai mesa==2.1.5 numpy")

        # Upload runner files once
        logger.info("Uploading runner files...")
        sbx.files.write("/home/user/arena_runner.py", self._get_runner_code())
        sbx.files.write("/home/user/tools.py", self._get_tools_code())
        sbx.files.write("/home/user/hooks.py", self._get_hooks_code())
        sbx.files.write("/home/user/prompts.py", self._get_prompts_code())

        logger.info("Sandbox ready")
        return sbx

    def _get_sandbox(self) -> Sandbox:
        """Get or create the shared sandbox."""
        if self._sandbox is None or not self._sandbox_initialized:
            self._sandbox = self._create_sandbox()
            self._sandbox_initialized = True
        return self._sandbox

    def _cleanup_sandbox(self) -> None:
        """Clean up the sandbox."""
        if self._sandbox is not None:
            try:
                self._sandbox.kill()
            except Exception as e:
                logger.warning(f"Error killing sandbox: {e}")
            self._sandbox = None
            self._sandbox_initialized = False

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

        try:
            # Create sandbox once for all runs
            sbx = self._get_sandbox()

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
                                sbx=sbx,
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

        finally:
            # Clean up sandbox
            self._cleanup_sandbox()

        return self.results

    async def _run_single(
        self,
        sbx: Sandbox,
        question: Question,
        model: ModelConfig,
        mode: str,
        trial: int,
    ) -> RunResult:
        """Run a single evaluation in the shared E2B sandbox."""
        try:
            result_dict = await self._run_in_sandbox(
                sbx=sbx,
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
                log=result_dict.get("log"),  # Include conversation log
            )

        except Exception as e:
            logger.error(f"Run error: {e}")
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
        sbx: Sandbox,
        question: Question,
        model: ModelConfig,
        mode: str,
        trial: int,
    ) -> dict:
        """Execute arena runner in the shared E2B sandbox.

        Dependencies and files are already installed/uploaded in _create_sandbox().
        """
        # Escape quotes in question text for shell command
        escaped_question = question.question.replace('"', '\\"').replace("'", "\\'")
        escaped_description = (question.description or "").replace('"', '\\"').replace("'", "\\'")

        # Build command
        cmd = (
            f"cd /home/user && OPENROUTER_API_KEY='{self.api_key}' "
            f"python arena_runner.py "
            f'--question "{escaped_question}" '
            f'--description "{escaped_description}" '
            f'--market-id "{question.id}" '
            f"--volume {question.volume} "
            f'--closed-time "{question.closed_time or ""}" '
            f"--mode {mode} "
            f'--model "{model.id}" '
            f"--trial {trial} "
            f"--max-turns {self.config.max_turns}"
        )

        # Run (no sandbox setup needed - already done)
        result = sbx.commands.run(cmd, timeout=300)  # 5 min timeout per run

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

    def _get_runner_code(self) -> str:
        """Get arena_runner.py source code (cached)."""
        if "runner" not in _runner_code_cache:
            path = Path(__file__).parent / "runner" / "arena_runner.py"
            _runner_code_cache["runner"] = path.read_text()
        return _runner_code_cache["runner"]

    def _get_tools_code(self) -> str:
        """Get tools.py source code (cached)."""
        if "tools" not in _runner_code_cache:
            path = Path(__file__).parent / "runner" / "tools.py"
            _runner_code_cache["tools"] = path.read_text()
        return _runner_code_cache["tools"]

    def _get_hooks_code(self) -> str:
        """Get hooks.py source code (cached)."""
        if "hooks" not in _runner_code_cache:
            path = Path(__file__).parent / "runner" / "hooks.py"
            _runner_code_cache["hooks"] = path.read_text()
        return _runner_code_cache["hooks"]

    def _get_prompts_code(self) -> str:
        """Get prompts.py source code (cached)."""
        if "prompts" not in _runner_code_cache:
            path = Path(__file__).parent / "runner" / "prompts.py"
            _runner_code_cache["prompts"] = path.read_text()
        return _runner_code_cache["prompts"]

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
