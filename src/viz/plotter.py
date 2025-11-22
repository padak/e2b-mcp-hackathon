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
            subplot_titles=("Final Results", "Convergence Over Time", "", ""),
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
        textfont=dict(size=14),
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

    # Calculate trading metrics
    diff = prob - market_odds
    diff_sign = "+" if diff > 0 else ""

    # Confidence check - is market odds outside our CI?
    sim_low = prob - ci
    sim_high = prob + ci
    market_in_ci = sim_low <= market_odds <= sim_high

    # Trading signal
    if abs(diff) < 0.05:
        signal = "HOLD"
        signal_color = "#6b7280"  # gray
    elif diff > 0:
        signal = "BUY YES"
        signal_color = "#059669"  # green
    else:
        signal = "BUY NO"
        signal_color = "#dc2626"  # red

    # Expected Value calculation (per $100 bet)
    # Guard against division by zero at boundaries
    if not 0 < market_odds < 1:
        ev = 0
        bet_side = "YES" if diff >= 0 else "NO"
    elif diff > 0:
        # Bet on YES - market undervalues YES
        payout_multiplier = 1 / market_odds
        ev = prob * 100 * payout_multiplier - 100
        bet_side = "YES"
    else:
        # Bet on NO - market undervalues NO
        payout_multiplier = 1 / (1 - market_odds)
        ev = (1 - prob) * 100 * payout_multiplier - 100
        bet_side = "NO"

    # Confidence level
    if market_in_ci:
        confidence = "LOW"
        confidence_note = "Market within CI"
    elif abs(diff) > 0.15:
        confidence = "HIGH"
        confidence_note = f"Strong edge ({abs(diff)*100:.0f}pp)"
    else:
        confidence = "MEDIUM"
        confidence_note = f"Moderate edge ({abs(diff)*100:.0f}pp)"

    # Build summary with trading info
    summary_line = (
        f"<span style='font-size:13px'>"
        f"<b style='color:{signal_color}'>{signal}</b> | "
        f"Simulation: {prob:.0%} ± {ci:.0%} | "
        f"Market: {market_odds:.0%} | "
        f"Diff: {diff_sign}{diff*100:.1f}pp | "
        f"EV: {'+' if ev > 0 else ''}{ev:.0f}/100 on {bet_side} | "
        f"Confidence: {confidence}"
        f"</span>"
    )

    # Add model info if provided
    if model_info:
        # Build model info text with header
        info_parts = ["<b style='font-size:18px'>Model Details</b>"]

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

        # Add as annotation in bottom panel - centered
        fig.add_annotation(
            text=model_text,
            xref="paper", yref="paper",
            x=0.5, y=0.22,
            xanchor="center", yanchor="top",
            showarrow=False,
            font=dict(size=16),
            align="left"
        )

        # Hide axes for model info panel
        fig.update_xaxes(visible=False, row=2, col=1)
        fig.update_yaxes(visible=False, row=2, col=1)

        chart_height = 850
    else:
        chart_height = 500

    fig.update_layout(
        title=dict(
            text=f"{title}<br>{summary_line}",
            x=0.5,
            xanchor="center",
            font=dict(size=22),
            y=0.97
        ),
        template="plotly_white",
        height=chart_height,
        margin=dict(t=120, b=120, l=80, r=80),
        font=dict(size=16)  # Base font size
    )

    # Larger axis labels
    fig.update_yaxes(title_text="Count", title_font_size=18, tickfont_size=14, row=1, col=1)
    fig.update_yaxes(title_text="Probability (%)", title_font_size=18, tickfont_size=14, range=[0, 100], row=1, col=2)
    fig.update_xaxes(title_text="Outcome", title_font_size=18, tickfont_size=14, row=1, col=1)
    fig.update_xaxes(title_text="Run #", title_font_size=18, tickfont_size=14, row=1, col=2)

    return fig.to_html(include_plotlyjs=True, full_html=True)


def create_batch_dashboard(results: list, batch_name: str) -> str:
    """
    Create a summary dashboard for batch simulation results.

    Args:
        results: List of result dicts from batch simulation
        batch_name: Name of the batch (e.g., "politics", "top10_volume")

    Returns:
        HTML string with interactive summary dashboard
    """
    from datetime import datetime

    successful = [r for r in results if r.get("success")]
    failed = [r for r in results if not r.get("success")]

    # Sort by difference (largest discrepancy first)
    successful.sort(
        key=lambda r: abs(r.get("probability", 0) - r["market"]["yes_odds"]),
        reverse=True
    )

    # Create table data
    table_rows = []
    for i, r in enumerate(successful, 1):
        market = r["market"]
        prob = r.get("probability", 0)
        market_odds = market["yes_odds"]
        diff = prob - market_odds
        diff_sign = "+" if diff > 0 else ""

        # Determine color based on difference
        if abs(diff) > 0.15:
            row_color = "#fff3cd"  # Yellow for large diff
        elif abs(diff) > 0.10:
            row_color = "#f8f9fa"  # Light gray for medium diff
        else:
            row_color = "#d4edda"  # Green for close match

        table_rows.append({
            "rank": i,
            "question": market["question"][:60] + ("..." if len(market["question"]) > 60 else ""),
            "market_odds": f"{market_odds:.0%}",
            "simulation": f"{prob:.0%}",
            "diff": f"{diff_sign}{diff*100:.1f}pp",
            "ci": f"±{r.get('ci_95', 0):.0%}",
            "color": row_color,
            "result_dir": r.get("result_dir", "")
        })

    # Calculate summary stats
    if successful:
        diffs = [abs(r.get("probability", 0) - r["market"]["yes_odds"]) for r in successful]
        avg_diff = np.mean(diffs) * 100
        max_diff = max(diffs) * 100
        median_diff = np.median(diffs) * 100
    else:
        avg_diff = max_diff = median_diff = 0

    # Build HTML
    html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Batch Results: {batch_name}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background: #f5f5f5;
        }}
        .header {{
            background: #1e3a8a;
            color: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .stats {{
            display: flex;
            gap: 20px;
            margin-bottom: 20px;
        }}
        .stat-box {{
            background: white;
            padding: 15px 20px;
            border-radius: 8px;
            flex: 1;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .stat-box h3 {{
            margin: 0 0 5px 0;
            color: #666;
            font-size: 12px;
            text-transform: uppercase;
        }}
        .stat-box .value {{
            font-size: 24px;
            font-weight: bold;
            color: #1e3a8a;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            background: white;
            border-radius: 8px;
            overflow: hidden;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        th {{
            background: #374151;
            color: white;
            padding: 12px;
            text-align: left;
            font-size: 12px;
            text-transform: uppercase;
        }}
        td {{
            padding: 12px;
            border-bottom: 1px solid #e5e7eb;
        }}
        tr:hover {{
            background: #f3f4f6 !important;
        }}
        .question {{
            max-width: 400px;
        }}
        .diff-positive {{
            color: #059669;
            font-weight: bold;
        }}
        .diff-negative {{
            color: #dc2626;
            font-weight: bold;
        }}
        .link {{
            color: #3b82f6;
            text-decoration: none;
        }}
        .link:hover {{
            text-decoration: underline;
        }}
        .failed {{
            background: #fee2e2;
            padding: 10px;
            border-radius: 8px;
            margin-top: 20px;
        }}
        .failed h3 {{
            color: #dc2626;
            margin: 0 0 10px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Batch Simulation Results</h1>
        <p>{batch_name.replace('_', ' ').title()} | {datetime.now().strftime('%Y-%m-%d %H:%M')} | {len(results)} markets</p>
    </div>

    <div class="stats">
        <div class="stat-box">
            <h3>Successful</h3>
            <div class="value">{len(successful)}/{len(results)}</div>
        </div>
        <div class="stat-box">
            <h3>Avg Difference</h3>
            <div class="value">{avg_diff:.1f}pp</div>
        </div>
        <div class="stat-box">
            <h3>Max Difference</h3>
            <div class="value">{max_diff:.1f}pp</div>
        </div>
        <div class="stat-box">
            <h3>Median Difference</h3>
            <div class="value">{median_diff:.1f}pp</div>
        </div>
    </div>

    <table>
        <thead>
            <tr>
                <th>#</th>
                <th class="question">Question</th>
                <th>Market</th>
                <th>Simulation</th>
                <th>Diff</th>
                <th>CI</th>
                <th>Details</th>
            </tr>
        </thead>
        <tbody>
"""

    for row in table_rows:
        diff_class = "diff-positive" if row["diff"].startswith("+") else "diff-negative"
        link = f"<a class='link' href='{row['result_dir']}/result.html'>View</a>" if row["result_dir"] else ""

        html += f"""
            <tr style="background: {row['color']}">
                <td>{row['rank']}</td>
                <td class="question">{row['question']}</td>
                <td>{row['market_odds']}</td>
                <td>{row['simulation']}</td>
                <td class="{diff_class}">{row['diff']}</td>
                <td>{row['ci']}</td>
                <td>{link}</td>
            </tr>
"""

    html += """
        </tbody>
    </table>
"""

    # Add failed section if any
    if failed:
        html += f"""
    <div class="failed">
        <h3>Failed Simulations ({len(failed)})</h3>
        <ul>
"""
        for r in failed:
            question = r["market"]["question"][:60]
            error = r.get("error", "Unknown error")[:100]
            html += f"            <li><strong>{question}</strong>: {error}</li>\n"

        html += """
        </ul>
    </div>
"""

    html += """
</body>
</html>
"""

    return html


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
