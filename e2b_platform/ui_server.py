"""
Flask UI server with step-by-step progress display.
Creates a NEW sandbox to run the Claude Agent SDK task.
"""
from flask import Flask, render_template_string, jsonify, Response, make_response
import subprocess
import os
import json
import time
import traceback

app = Flask(__name__)


# Add CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


@app.errorhandler(Exception)
def handle_exception(e):
    return jsonify({
        'success': False,
        'error': str(e),
        'traceback': traceback.format_exc()
    }), 500


HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>E2B + Claude Agent SDK Demo</title>
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 900px;
            margin: 50px auto;
            padding: 20px;
            background: #f5f5f5;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }
        button {
            background: #5436DA;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        button:hover { background: #4328B8; }
        button:disabled { background: #ccc; cursor: not-allowed; }

        .steps {
            margin-top: 30px;
            border: 1px solid #e0e0e0;
            border-radius: 8px;
            overflow: hidden;
            display: none;
        }
        .step {
            padding: 15px 20px;
            border-bottom: 1px solid #e0e0e0;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .step:last-child { border-bottom: none; }
        .step-icon {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 14px;
            flex-shrink: 0;
        }
        .step.pending .step-icon { background: #e0e0e0; color: #999; }
        .step.running .step-icon { background: #fff3cd; color: #856404; animation: pulse 1s infinite; }
        .step.done .step-icon { background: #d4edda; color: #155724; }
        .step.error .step-icon { background: #f8d7da; color: #721c24; }
        @keyframes pulse { 0%, 100% { opacity: 1; } 50% { opacity: 0.5; } }

        .step-content { flex-grow: 1; }
        .step-title { font-weight: 600; color: #333; }
        .step-detail { font-size: 13px; color: #666; margin-top: 3px; }

        #output {
            margin-top: 20px;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 13px;
            white-space: pre-wrap;
            max-height: 400px;
            overflow-y: auto;
            display: none;
        }
        .final-status {
            margin-top: 15px;
            padding: 15px;
            border-radius: 5px;
            display: none;
            font-weight: 500;
        }
        .final-status.success { background: #d4edda; color: #155724; }
        .final-status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>E2B + Claude Agent SDK Demo</h1>
        <p class="subtitle">Click the button to run a Claude agent that analyzes a sample document in a new sandbox</p>

        <button id="runBtn" onclick="runAgent()">Run Claude Agent</button>

        <div class="steps" id="steps">
            <div class="step pending" id="step1">
                <div class="step-icon">1</div>
                <div class="step-content">
                    <div class="step-title">Create Agent Sandbox</div>
                    <div class="step-detail">Spinning up isolated E2B sandbox environment</div>
                </div>
            </div>
            <div class="step pending" id="step2">
                <div class="step-icon">2</div>
                <div class="step-content">
                    <div class="step-title">Upload Agent Script</div>
                    <div class="step-detail">Uploading Claude Agent SDK script to sandbox</div>
                </div>
            </div>
            <div class="step pending" id="step3">
                <div class="step-icon">3</div>
                <div class="step-content">
                    <div class="step-title">Upload Test File</div>
                    <div class="step-detail">Uploading document for analysis</div>
                </div>
            </div>
            <div class="step pending" id="step4">
                <div class="step-icon">4</div>
                <div class="step-content">
                    <div class="step-title">Run Agent Analysis</div>
                    <div class="step-detail">Claude Agent SDK analyzing the document</div>
                </div>
            </div>
            <div class="step pending" id="step5">
                <div class="step-icon">5</div>
                <div class="step-content">
                    <div class="step-title">Save Results</div>
                    <div class="step-detail">Writing analysis results to sandbox</div>
                </div>
            </div>
            <div class="step pending" id="step6">
                <div class="step-icon">6</div>
                <div class="step-content">
                    <div class="step-title">Retrieve Results</div>
                    <div class="step-detail">Fetching results from sandbox</div>
                </div>
            </div>
        </div>

        <div class="final-status" id="finalStatus"></div>
        <div id="output"></div>
    </div>

    <script>
        function updateStep(stepNum, status, detail) {
            const step = document.getElementById('step' + stepNum);
            step.className = 'step ' + status;
            if (detail) {
                step.querySelector('.step-detail').textContent = detail;
            }
            const icon = step.querySelector('.step-icon');
            if (status === 'done') icon.textContent = '✓';
            else if (status === 'error') icon.textContent = '✗';
            else if (status === 'running') icon.textContent = '⋯';
        }

        function resetSteps() {
            for (let i = 1; i <= 6; i++) {
                const step = document.getElementById('step' + i);
                step.className = 'step pending';
                step.querySelector('.step-icon').textContent = i;
            }
        }

        async function runAgent() {
            const btn = document.getElementById('runBtn');
            const steps = document.getElementById('steps');
            const output = document.getElementById('output');
            const finalStatus = document.getElementById('finalStatus');

            btn.disabled = true;
            steps.style.display = 'block';
            output.style.display = 'none';
            finalStatus.style.display = 'none';
            resetSteps();

            try {
                const response = await fetch('/run-agent-steps', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                const reader = response.body.getReader();
                const decoder = new TextDecoder();
                let buffer = '';

                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    buffer += decoder.decode(value, { stream: true });
                    const lines = buffer.split('\\n');
                    buffer = lines.pop();

                    for (const line of lines) {
                        if (line.startsWith('data: ')) {
                            try {
                                const data = JSON.parse(line.slice(6));
                                if (data.step) {
                                    updateStep(data.step, data.status, data.detail);
                                }
                                if (data.result) {
                                    output.style.display = 'block';
                                    output.textContent = data.result;
                                }
                                if (data.final) {
                                    finalStatus.style.display = 'block';
                                    finalStatus.className = 'final-status ' + (data.success ? 'success' : 'error');
                                    finalStatus.textContent = data.message;
                                }
                            } catch (e) {}
                        }
                    }
                }
            } catch (err) {
                finalStatus.style.display = 'block';
                finalStatus.className = 'final-status error';
                finalStatus.textContent = 'Error: ' + err.message;
            }

            btn.disabled = false;
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


def generate_steps():
    """Generator that yields SSE events for each step."""
    import sys
    sys.path.insert(0, '/home/user')

    def send_event(data):
        return f"data: {json.dumps(data)}\n\n"

    sandbox_id = None

    try:
        # Step 1: Create sandbox
        yield send_event({'step': 1, 'status': 'running', 'detail': 'Creating E2B sandbox...'})

        from e2b_code_interpreter import Sandbox
        sandbox = Sandbox.create(timeout=300)
        sandbox_id = sandbox.get_info().sandbox_id

        yield send_event({'step': 1, 'status': 'done', 'detail': f'Sandbox created: {sandbox_id[:12]}...'})

        # Step 2: Upload agent script
        yield send_event({'step': 2, 'status': 'running', 'detail': 'Reading and uploading agent script...'})

        with open('/home/user/agent_task.py', 'r') as f:
            agent_code = f.read()
        sandbox.files.write('/home/user/agent_task.py', agent_code)

        yield send_event({'step': 2, 'status': 'done', 'detail': 'Agent script uploaded successfully'})

        # Step 3: Upload test file
        yield send_event({'step': 3, 'status': 'running', 'detail': 'Uploading test document...'})

        with open('/home/user/test_file.txt', 'r') as f:
            test_content = f.read()
        sandbox.files.write('/home/user/test_file.txt', test_content)

        yield send_event({'step': 3, 'status': 'done', 'detail': f'Test file uploaded ({len(test_content)} bytes)'})

        # Step 4: Run agent
        yield send_event({'step': 4, 'status': 'running', 'detail': 'Installing dependencies and running Claude Agent...'})

        # Install claude-agent-sdk
        sandbox.commands.run('pip install -q claude-agent-sdk', timeout=60)

        # Run the agent with API key
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        result = sandbox.commands.run(
            f'ANTHROPIC_API_KEY={api_key} python /home/user/agent_task.py 2>&1',
            timeout=120
        )
        agent_output = result.stdout

        yield send_event({'step': 4, 'status': 'done', 'detail': 'Agent analysis completed'})

        # Step 5: Save results
        yield send_event({'step': 5, 'status': 'running', 'detail': 'Saving analysis results...'})

        sandbox.files.write('/home/user/results.txt', agent_output)

        yield send_event({'step': 5, 'status': 'done', 'detail': 'Results saved to /home/user/results.txt'})

        # Step 6: Retrieve results
        yield send_event({'step': 6, 'status': 'running', 'detail': 'Fetching results from sandbox...'})

        final_results = sandbox.files.read('/home/user/results.txt')

        yield send_event({'step': 6, 'status': 'done', 'detail': 'Results retrieved successfully'})

        # Send final results
        yield send_event({'result': final_results})
        yield send_event({'final': True, 'success': True, 'message': 'Agent completed successfully!'})

        # Cleanup
        sandbox.kill()

    except Exception as e:
        error_msg = f"{str(e)}\n\n{traceback.format_exc()}"
        yield send_event({'result': error_msg})
        yield send_event({'final': True, 'success': False, 'message': f'Error: {str(e)}'})


@app.route('/run-agent-steps', methods=['POST'])
def run_agent_steps():
    """SSE endpoint for step-by-step agent execution."""
    return Response(
        generate_steps(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False, threaded=True)
