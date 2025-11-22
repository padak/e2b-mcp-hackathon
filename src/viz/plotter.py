"""
Visualization module for comparing simulation results with market odds.
"""

import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import TypedDict


class SimulationResult(TypedDict):
    probability: float
    ci_95: float
    n_runs: int
    results: list[int]


class ModelInfo(TypedDict, total=False):
    """Information about the simulation model for display."""
    name: str
    description: str
    agents: list[dict]  # [{"name": "Investor", "count": 50, "behavior": "..."}]
    parameters: dict  # {"interest_rate": 5.5, "inflation": 3.2}


def create_chart(
    simulation: SimulationResult,
    market_odds: float,
    title: str
) -> str:
    """
    Create an interactive HTML chart comparing simulation results with market odds.

    Args:
        simulation: Dict with probability, ci_95, n_runs, and results
        market_odds: Polymarket probability (0-1)
        title: Market question

    Returns:
        HTML string with interactive Plotly chart
    """
    prob = simulation["probability"]
    ci = simulation["ci_95"]
    n_runs = simulation["n_runs"]
    results = simulation["results"]

    # Calculate difference
    diff = prob - market_odds
    diff_sign = "+" if diff > 0 else ""

    # Count outcomes
    yes_count = sum(results)
    no_count = n_runs - yes_count

    fig = go.Figure()

    # Bar chart for Yes/No outcomes
    fig.add_trace(go.Bar(
        x=["No", "Yes"],
        y=[no_count, yes_count],
        marker_color=["#ef4444", "#22c55e"],
        text=[f"{no_count}<br>({100*no_count/n_runs:.0f}%)",
              f"{yes_count}<br>({100*yes_count/n_runs:.0f}%)"],
        textposition="auto",
        name="Simulation Results"
    ))

    # Add horizontal line for market odds
    fig.add_hline(
        y=market_odds * n_runs,
        line_dash="dash",
        line_color="#3b82f6",
        line_width=2,
        annotation_text=f"Market: {market_odds:.0%}",
        annotation_position="right"
    )

    # Summary annotation
    summary_text = (
        f"<b>Simulation:</b> {prob:.0%} ± {ci:.0%}<br>"
        f"<b>Market:</b> {market_odds:.0%}<br>"
        f"<b>Difference:</b> {diff_sign}{diff*100:.1f}pp"
    )

    fig.add_annotation(
        text=summary_text,
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        xanchor="left", yanchor="top",
        showarrow=False,
        bordercolor="#666",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(255,255,255,0.9)",
        font=dict(size=12)
    )

    # Layout
    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=16)
        ),
        xaxis_title="Outcome",
        yaxis_title=f"Count (out of {n_runs} runs)",
        showlegend=False,
        template="plotly_white",
        height=500,
        margin=dict(t=80, b=60, l=60, r=40)
    )

    return fig.to_html(include_plotlyjs=True, full_html=True)


def create_distribution_chart(
    simulation: SimulationResult,
    market_odds: float,
    title: str
) -> str:
    """
    Alternative visualization showing probability distribution.

    Creates a gauge chart comparing simulation vs market probability.
    """
    prob = simulation["probability"]
    ci = simulation["ci_95"]
    diff = prob - market_odds
    diff_sign = "+" if diff > 0 else ""

    fig = go.Figure()

    # Simulation gauge
    fig.add_trace(go.Indicator(
        mode="gauge+number",
        value=prob * 100,
        number={"suffix": "%", "font": {"size": 40}},
        title={"text": "Simulation", "font": {"size": 16}},
        gauge={
            "axis": {"range": [0, 100], "ticksuffix": "%"},
            "bar": {"color": "#22c55e"},
            "bgcolor": "white",
            "borderwidth": 2,
            "bordercolor": "#ccc",
            "steps": [
                {"range": [0, 50], "color": "#fee2e2"},
                {"range": [50, 100], "color": "#dcfce7"}
            ],
            "threshold": {
                "line": {"color": "#3b82f6", "width": 4},
                "thickness": 0.75,
                "value": market_odds * 100
            }
        },
        domain={"x": [0.1, 0.9], "y": [0.3, 1]}
    ))

    # Summary text
    summary = (
        f"Simulation: {prob:.0%} ± {ci:.0%} | "
        f"Market: {market_odds:.0%} | "
        f"Diff: {diff_sign}{diff*100:.1f}pp"
    )

    fig.add_annotation(
        text=summary,
        xref="paper", yref="paper",
        x=0.5, y=0.1,
        xanchor="center",
        showarrow=False,
        font=dict(size=14)
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=16)
        ),
        height=400,
        margin=dict(t=80, b=60)
    )

    return fig.to_html(include_plotlyjs=True, full_html=True)


def create_convergence_chart(
    simulation: SimulationResult,
    market_odds: float,
    title: str
) -> str:
    """
    Create a convergence chart showing how simulation probability evolves.

    Shows running average of Monte Carlo results compared to market odds,
    with confidence bands that narrow as more runs complete.
    """
    results = simulation["results"]
    n_runs = len(results)

    # Calculate running statistics
    cumsum = np.cumsum(results)
    run_numbers = np.arange(1, n_runs + 1)
    running_prob = cumsum / run_numbers

    # Calculate running confidence interval (95%)
    running_ci = 1.96 * np.sqrt(running_prob * (1 - running_prob) / run_numbers)

    fig = go.Figure()

    # Confidence band
    fig.add_trace(go.Scatter(
        x=np.concatenate([run_numbers, run_numbers[::-1]]),
        y=np.concatenate([
            (running_prob + running_ci) * 100,
            (running_prob - running_ci)[::-1] * 100
        ]),
        fill='toself',
        fillcolor='rgba(34, 197, 94, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% CI',
        showlegend=True
    ))

    # Running probability line
    fig.add_trace(go.Scatter(
        x=run_numbers,
        y=running_prob * 100,
        mode='lines',
        line=dict(color='#22c55e', width=2),
        name='Simulation'
    ))

    # Market odds line
    fig.add_hline(
        y=market_odds * 100,
        line_dash="dash",
        line_color="#3b82f6",
        line_width=2,
        annotation_text=f"Polymarket: {market_odds:.0%}",
        annotation_position="right"
    )

    # Final values annotation
    final_prob = simulation["probability"]
    ci = simulation["ci_95"]
    diff = final_prob - market_odds
    diff_sign = "+" if diff > 0 else ""

    fig.add_annotation(
        text=(
            f"<b>Final Result</b><br>"
            f"Simulation: {final_prob:.0%} ± {ci:.0%}<br>"
            f"Market: {market_odds:.0%}<br>"
            f"Diff: {diff_sign}{diff*100:.1f}pp"
        ),
        xref="paper", yref="paper",
        x=0.02, y=0.98,
        xanchor="left", yanchor="top",
        showarrow=False,
        bordercolor="#666",
        borderwidth=1,
        borderpad=8,
        bgcolor="rgba(255,255,255,0.9)",
        font=dict(size=11)
    )

    fig.update_layout(
        title=dict(
            text=title,
            x=0.5,
            xanchor="center",
            font=dict(size=16)
        ),
        xaxis_title="Simulation Run",
        yaxis_title="Probability (%)",
        yaxis=dict(range=[0, 100]),
        template="plotly_white",
        height=500,
        margin=dict(t=80, b=60, l=60, r=80),
        legend=dict(
            yanchor="bottom",
            y=0.02,
            xanchor="right",
            x=0.98
        )
    )

    return fig.to_html(include_plotlyjs=True, full_html=True)


def create_dashboard(
    simulation: SimulationResult,
    market_odds: float,
    title: str,
    model_info: ModelInfo | None = None
) -> str:
    """
    Create a combined dashboard with bar chart, convergence plot, and model info.
    """
    results = simulation["results"]
    n_runs = len(results)
    prob = simulation["probability"]
    ci = simulation["ci_95"]

    # Calculate running stats
    cumsum = np.cumsum(results)
    run_numbers = np.arange(1, n_runs + 1)
    running_prob = cumsum / run_numbers
    running_ci = 1.96 * np.sqrt(running_prob * (1 - running_prob) / run_numbers)

    # Count outcomes
    yes_count = sum(results)
    no_count = n_runs - yes_count

    # Create layout based on whether we have model info
    if model_info:
        fig = make_subplots(
            rows=2, cols=2,
            subplot_titles=("Final Results", "Convergence Over Time", "Model Details", ""),
            column_widths=[0.4, 0.6],
            row_heights=[0.7, 0.3],
            specs=[[{}, {}], [{"colspan": 2}, None]]
        )
    else:
        fig = make_subplots(
            rows=1, cols=2,
            subplot_titles=("Final Results", "Convergence Over Time"),
            column_widths=[0.4, 0.6]
        )

    # Left: Bar chart
    fig.add_trace(go.Bar(
        x=["No", "Yes"],
        y=[no_count, yes_count],
        marker_color=["#ef4444", "#22c55e"],
        text=[f"{no_count}<br>({100*no_count/n_runs:.0f}%)",
              f"{yes_count}<br>({100*yes_count/n_runs:.0f}%)"],
        textposition="auto",
        showlegend=False
    ), row=1, col=1)

    # Right: Convergence
    fig.add_trace(go.Scatter(
        x=np.concatenate([run_numbers, run_numbers[::-1]]),
        y=np.concatenate([
            (running_prob + running_ci) * 100,
            (running_prob - running_ci)[::-1] * 100
        ]),
        fill='toself',
        fillcolor='rgba(34, 197, 94, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        name='95% CI',
        showlegend=False
    ), row=1, col=2)

    fig.add_trace(go.Scatter(
        x=run_numbers,
        y=running_prob * 100,
        mode='lines',
        line=dict(color='#22c55e', width=2),
        name='Simulation',
        showlegend=False
    ), row=1, col=2)

    # Market line on convergence chart
    fig.add_hline(
        y=market_odds * 100,
        line_dash="dash",
        line_color="#3b82f6",
        line_width=2,
        row=1, col=2
    )

    # Market line on bar chart (scaled to count)
    fig.add_hline(
        y=market_odds * n_runs,
        line_dash="dash",
        line_color="#3b82f6",
        line_width=2,
        row=1, col=1
    )

    # Summary - in title
    diff = prob - market_odds
    diff_sign = "+" if diff > 0 else ""

    summary_line = (
        f"<span style='font-size:11px'>"
        f"Simulation: {prob:.0%} ± {ci:.0%}  |  "
        f"Polymarket: {market_odds:.0%}  |  "
        f"Diff: {diff_sign}{diff*100:.1f}pp</span>"
    )

    # Add model info if provided
    if model_info:
        # Build model info text
        info_parts = []

        if "name" in model_info:
            info_parts.append(f"<b>{model_info['name']}</b>")

        if "description" in model_info:
            info_parts.append(model_info["description"])

        if "agents" in model_info:
            agent_lines = []
            for agent in model_info["agents"]:
                line = f"• <b>{agent['name']}</b>"
                if "count" in agent:
                    line += f" ({agent['count']})"
                if "behavior" in agent:
                    line += f": {agent['behavior']}"
                agent_lines.append(line)
            info_parts.append("<br>".join(agent_lines))

        if "parameters" in model_info:
            param_str = " | ".join([f"{k}: {v}" for k, v in model_info["parameters"].items()])
            info_parts.append(f"<i>Parameters: {param_str}</i>")

        model_text = "<br><br>".join(info_parts)

        # Add as annotation in bottom panel
        fig.add_annotation(
            text=model_text,
            xref="paper", yref="paper",
            x=0.02, y=0.25,
            xanchor="left", yanchor="top",
            showarrow=False,
            font=dict(size=10),
            align="left"
        )

        # Hide axes for model info panel
        fig.update_xaxes(visible=False, row=2, col=1)
        fig.update_yaxes(visible=False, row=2, col=1)

        chart_height = 650
    else:
        chart_height = 500

    fig.update_layout(
        title=dict(
            text=f"{title}<br>{summary_line}",
            x=0.5,
            xanchor="center",
            font=dict(size=16),
            y=0.98
        ),
        template="plotly_white",
        height=chart_height,
        margin=dict(t=80, b=60, l=60, r=60)
    )

    fig.update_yaxes(title_text="Count", row=1, col=1)
    fig.update_yaxes(title_text="Probability (%)", range=[0, 100], row=1, col=2)
    fig.update_xaxes(title_text="Outcome", row=1, col=1)
    fig.update_xaxes(title_text="Run #", row=1, col=2)

    return fig.to_html(include_plotlyjs=True, full_html=True)


if __name__ == "__main__":
    # Generate realistic random results (not just sorted 1s and 0s)
    np.random.seed(42)
    results = list(np.random.binomial(1, 0.65, 200))

    test_simulation = {
        "probability": sum(results) / len(results),
        "ci_95": 1.96 * np.sqrt(0.65 * 0.35 / 200),
        "n_runs": 200,
        "results": results
    }

    title = "Will the Fed cut interest rates in December 2024?"
    market_odds = 0.72

    # Model info for demo
    test_model_info = {
        "name": "Economic Shock Agent-Based Model",
        "description": "Simulates market reaction to Fed interest rate decisions using heterogeneous agents with different risk profiles and investment strategies.",
        "agents": [
            {"name": "Investors", "count": 50, "behavior": "React to rate changes based on risk tolerance"},
            {"name": "Consumers", "count": 30, "behavior": "Adjust spending based on borrowing costs"},
            {"name": "Firms", "count": 20, "behavior": "Modify investment plans based on capital costs"}
        ],
        "parameters": {
            "interest_rate": "5.5%",
            "inflation": "3.2%",
            "sentiment": "neutral"
        }
    }

    # Test convergence chart
    html = create_convergence_chart(
        simulation=test_simulation,
        market_odds=market_odds,
        title=title
    )
    with open("/tmp/test_convergence.html", "w") as f:
        f.write(html)

    # Test dashboard with model info
    html = create_dashboard(
        simulation=test_simulation,
        market_odds=market_odds,
        title=title,
        model_info=test_model_info
    )
    with open("/tmp/test_dashboard.html", "w") as f:
        f.write(html)

    print("Charts saved:")
    print("  - /tmp/test_convergence.html (time series)")
    print("  - /tmp/test_dashboard.html (combined view with model info)")
    print(f"\nSimulation: {test_simulation['probability']:.0%}")
    print(f"Market: {market_odds:.0%}")
    print(f"Difference: {(test_simulation['probability'] - market_odds) * 100:+.1f}pp")
