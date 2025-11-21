"""
Simple Flask UI server - runs inside E2B sandbox
Provides a button to trigger Claude Agent SDK task in another sandbox
"""
from flask import Flask, render_template_string, jsonify, request, make_response
import subprocess
import os
import traceback

app = Flask(__name__)


# Add CORS headers to all responses
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# Handle OPTIONS preflight requests
@app.route('/run-agent', methods=['OPTIONS'])
def options_run_agent():
    response = make_response()
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response


# Global error handler to always return JSON
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
            max-width: 800px;
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
        h1 {
            color: #333;
            margin-bottom: 10px;
        }
        .subtitle {
            color: #666;
            margin-bottom: 30px;
        }
        button {
            background: #5436DA;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
            transition: background 0.2s;
        }
        button:hover {
            background: #4328B8;
        }
        button:disabled {
            background: #ccc;
            cursor: not-allowed;
        }
        #output {
            margin-top: 30px;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            display: none;
            max-height: 400px;
            overflow-y: auto;
        }
        .loading {
            display: none;
            margin-left: 10px;
            color: #666;
        }
        .status {
            margin-top: 15px;
            padding: 10px;
            border-radius: 5px;
            display: none;
        }
        .status.success { background: #d4edda; color: #155724; }
        .status.error { background: #f8d7da; color: #721c24; }
    </style>
</head>
<body>
    <div class="container">
        <h1>E2B + Claude Agent SDK Demo</h1>
        <p class="subtitle">Click the button to run a Claude agent that analyzes a sample document</p>

        <button id="runBtn" onclick="runAgent()">
            Run Claude Agent
        </button>
        <span class="loading" id="loading">Running agent...</span>

        <div class="status" id="status"></div>

        <div id="output"></div>
    </div>

    <script>
        async function runAgent() {
            const btn = document.getElementById('runBtn');
            const loading = document.getElementById('loading');
            const output = document.getElementById('output');
            const status = document.getElementById('status');

            btn.disabled = true;
            loading.style.display = 'inline';
            output.style.display = 'none';
            status.style.display = 'none';

            try {
                const response = await fetch('/run-agent', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                const data = await response.json();

                output.style.display = 'block';
                output.textContent = data.output || data.error;

                status.style.display = 'block';
                if (data.success) {
                    status.className = 'status success';
                    status.textContent = 'Agent completed successfully!';
                } else {
                    status.className = 'status error';
                    status.textContent = 'Agent encountered an error';
                }
            } catch (err) {
                output.style.display = 'block';
                output.textContent = 'Error: ' + err.message;
                status.style.display = 'block';
                status.className = 'status error';
                status.textContent = 'Request failed';
            }

            btn.disabled = false;
            loading.style.display = 'none';
        }
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/run-agent', methods=['POST'])
def run_agent():
    """Endpoint to trigger the agent task."""
    try:
        # Run the agent task script
        result = subprocess.run(
            ['python', '/home/user/agent_task.py'],
            capture_output=True,
            text=True,
            timeout=120,
            env={**os.environ}
        )

        output = result.stdout
        if result.stderr:
            output += "\n\nSTDERR:\n" + result.stderr

        return jsonify({
            'success': result.returncode == 0,
            'output': output,
            'return_code': result.returncode
        })

    except subprocess.TimeoutExpired:
        return jsonify({
            'success': False,
            'error': 'Agent task timed out after 120 seconds'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        })


@app.route('/health')
def health():
    return jsonify({'status': 'ok'})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=False)
