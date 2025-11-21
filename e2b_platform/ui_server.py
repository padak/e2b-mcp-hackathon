"""
Flask UI server with step-by-step progress display.
Creates a SLAVE sandbox to run the Claude Agent SDK task.
"""
from flask import Flask, render_template_string, jsonify, Response, request
import os
import sys
import json
import traceback

# Add current dir to path for config import
sys.path.insert(0, '/home/user')
import config

app = Flask(__name__)


# Add CORS headers
@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, DELETE, OPTIONS'
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
        * { box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            margin: 0;
            padding: 0;
            background: #f5f5f5;
            display: flex;
            min-height: 100vh;
        }

        /* Sidebar */
        .sidebar {
            width: 280px;
            background: #1a1a2e;
            color: #fff;
            padding: 20px;
            overflow-y: auto;
            flex-shrink: 0;
        }
        .sidebar h2 {
            font-size: 14px;
            text-transform: uppercase;
            color: #888;
            margin: 0 0 15px 0;
            display: flex;
            align-items: center;
            justify-content: space-between;
        }
        .sidebar h2 button {
            background: #333;
            border: none;
            color: #888;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .sidebar h2 button:hover { background: #444; color: #fff; }

        .sandbox-group {
            margin-bottom: 20px;
        }
        .sandbox-group-title {
            font-size: 12px;
            color: #5436DA;
            text-transform: uppercase;
            margin-bottom: 8px;
            padding-bottom: 5px;
            border-bottom: 1px solid #333;
        }
        .sandbox-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 10px;
            background: #252540;
            border-radius: 6px;
            margin-bottom: 8px;
            font-size: 13px;
        }
        .sandbox-item:hover { background: #303050; }
        .sandbox-info { flex-grow: 1; overflow: hidden; }
        .sandbox-id {
            font-family: monospace;
            color: #aaa;
            font-size: 11px;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
        }
        .sandbox-template {
            font-size: 11px;
            color: #666;
            margin-top: 2px;
        }
        .sandbox-status {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #28a745;
            margin-right: 10px;
            flex-shrink: 0;
        }
        .kill-btn {
            background: #dc3545;
            border: none;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 11px;
            flex-shrink: 0;
        }
        .kill-btn:hover { background: #c82333; }
        .kill-btn:disabled { background: #666; cursor: not-allowed; }

        .no-sandboxes {
            color: #666;
            font-size: 12px;
            text-align: center;
            padding: 20px;
        }

        /* Main content */
        .main-content {
            flex-grow: 1;
            padding: 30px;
            max-width: 900px;
            margin: 0 auto;
        }
        .container {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        h1 { color: #333; margin-bottom: 10px; }
        .subtitle { color: #666; margin-bottom: 30px; }

        .upload-section {
            margin-bottom: 25px;
            padding: 20px;
            border: 2px dashed #ddd;
            border-radius: 8px;
            text-align: center;
            transition: border-color 0.3s;
        }
        .upload-section:hover { border-color: #5436DA; }
        .upload-section.has-file { border-color: #28a745; background: #f8fff8; }

        .file-input { display: none; }
        .upload-label {
            cursor: pointer;
            color: #5436DA;
            font-weight: 500;
        }
        .file-name {
            margin-top: 10px;
            font-size: 14px;
            color: #666;
        }
        .file-preview {
            margin-top: 10px;
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            font-family: monospace;
            font-size: 12px;
            max-height: 100px;
            overflow-y: auto;
            text-align: left;
            white-space: pre-wrap;
        }

        .config-section {
            margin-bottom: 25px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .config-section summary {
            cursor: pointer;
            font-weight: 600;
            color: #333;
        }
        .config-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-top: 15px;
        }
        .config-item label {
            display: block;
            font-size: 13px;
            color: #666;
            margin-bottom: 5px;
        }
        .config-item input, .config-item select {
            width: 100%;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }

        button.primary {
            background: #5436DA;
            color: white;
            border: none;
            padding: 15px 30px;
            font-size: 16px;
            border-radius: 5px;
            cursor: pointer;
        }
        button.primary:hover { background: #4328B8; }
        button.primary:disabled { background: #ccc; cursor: not-allowed; }

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

        .result-section {
            margin-top: 20px;
            display: none;
        }
        .result-section h3 {
            font-size: 14px;
            color: #333;
            margin: 0 0 10px 0;
        }
        #cleanResult {
            padding: 20px;
            background: #f8fff8;
            border: 1px solid #d4edda;
            border-radius: 5px;
            font-size: 14px;
            line-height: 1.6;
            white-space: pre-wrap;
        }
        #output {
            margin-top: 20px;
            padding: 20px;
            background: #1e1e1e;
            color: #d4d4d4;
            border-radius: 5px;
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 12px;
            white-space: pre-wrap;
            max-height: 300px;
            overflow-y: auto;
            display: none;
        }
        .logs-toggle {
            margin-top: 15px;
            font-size: 13px;
            color: #666;
            cursor: pointer;
        }
        .logs-toggle:hover { color: #333; }
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
    <div class="sidebar">
        <h2>
            Sandboxes
            <button onclick="refreshSandboxes()">Refresh</button>
        </h2>
        <div id="sandboxList">
            <div class="no-sandboxes">Loading...</div>
        </div>
    </div>

    <div class="main-content">
        <div class="container">
            <h1>E2B + Claude Agent SDK Demo</h1>
            <p class="subtitle">Upload a document and run Claude agent analysis in an isolated sandbox</p>

            <div class="upload-section" id="uploadSection">
                <input type="file" id="fileInput" class="file-input" accept=".txt,.md,.json,.csv,.py,.js,.html,.xml,.yaml,.yml">
                <label for="fileInput" class="upload-label">Click to upload a file or drag & drop</label>
                <div class="file-name" id="fileName">Supported: .txt, .md, .json, .csv, .py, .js, .html, .xml, .yaml</div>
                <div class="file-preview" id="filePreview" style="display: none;"></div>
            </div>

            <details class="config-section">
                <summary>Agent Configuration</summary>
                <div class="config-grid">
                    <div class="config-item">
                        <label>Model</label>
                        <select id="agentModel">
                            <option value="claude-sonnet-4-20250514" """ + ('selected' if config.AGENT_MODEL == 'claude-sonnet-4-20250514' else '') + """>Claude Sonnet 4</option>
                            <option value="claude-3-5-sonnet-20241022" """ + ('selected' if config.AGENT_MODEL == 'claude-3-5-sonnet-20241022' else '') + """>Claude 3.5 Sonnet</option>
                            <option value="claude-3-haiku-20240307" """ + ('selected' if config.AGENT_MODEL == 'claude-3-haiku-20240307' else '') + """>Claude 3 Haiku (fast)</option>
                        </select>
                    </div>
                    <div class="config-item">
                        <label>Max Tokens</label>
                        <input type="number" id="agentMaxTokens" value=\"""" + str(config.AGENT_MAX_TOKENS) + """\" min="100" max="200000">
                    </div>
                </div>
            </details>

            <button class="primary" id="runBtn" onclick="runAgent()">Run Claude Agent</button>

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
                        <div class="step-title">Upload Document</div>
                        <div class="step-detail">Uploading your document for analysis</div>
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

            <div class="result-section" id="resultSection">
                <h3>Analysis Result</h3>
                <div id="cleanResult"></div>
            </div>

            <div class="logs-toggle" id="logsToggle" onclick="toggleLogs()">Show Full Logs</div>
            <div id="output"></div>
        </div>
    </div>

    <script>
        let fileContent = null;
        let fileName = null;

        // File upload handling
        const fileInput = document.getElementById('fileInput');
        const uploadSection = document.getElementById('uploadSection');
        const fileNameDiv = document.getElementById('fileName');
        const filePreview = document.getElementById('filePreview');

        fileInput.addEventListener('change', handleFile);
        uploadSection.addEventListener('dragover', (e) => { e.preventDefault(); uploadSection.style.borderColor = '#5436DA'; });
        uploadSection.addEventListener('dragleave', () => { uploadSection.style.borderColor = fileContent ? '#28a745' : '#ddd'; });
        uploadSection.addEventListener('drop', (e) => {
            e.preventDefault();
            if (e.dataTransfer.files.length) {
                fileInput.files = e.dataTransfer.files;
                handleFile();
            }
        });

        function handleFile() {
            const file = fileInput.files[0];
            if (!file) return;

            fileName = file.name;
            const reader = new FileReader();
            reader.onload = (e) => {
                fileContent = e.target.result;
                uploadSection.classList.add('has-file');
                fileNameDiv.textContent = fileName + ' (' + formatBytes(file.size) + ')';
                filePreview.style.display = 'block';
                filePreview.textContent = fileContent.substring(0, 500) + (fileContent.length > 500 ? '...' : '');
            };
            reader.readAsText(file);
        }

        function formatBytes(bytes) {
            if (bytes < 1024) return bytes + ' B';
            if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
            return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
        }

        // Sandbox management
        async function refreshSandboxes() {
            const listDiv = document.getElementById('sandboxList');
            listDiv.innerHTML = '<div class="no-sandboxes">Loading...</div>';

            try {
                const response = await fetch('/api/sandboxes');
                const data = await response.json();

                if (!data.sandboxes || data.sandboxes.length === 0) {
                    listDiv.innerHTML = '<div class="no-sandboxes">No active sandboxes</div>';
                    return;
                }

                // Group sandboxes by template ID
                const groups = {};

                data.sandboxes.forEach(sb => {
                    const tpl = sb.template || 'default';
                    if (!groups[tpl]) groups[tpl] = [];
                    groups[tpl].push(sb);
                });

                let html = '';

                // Define friendly names for known templates
                const templateNames = {
                    'qsu53e2apwfbl6xlm595': 'Master (chocho-master)',
                    'gxstwqtr3rfg5exocc8v': 'Slave (chocho-claude-agent-py313)',
                    'bvbz75moc7ghm58svsam': 'Slave (chocho-claude-agent-py)',
                    'nlhz8vlwyupq845jsdg9': 'Code Interpreter'
                };

                for (const [tpl, sandboxes] of Object.entries(groups)) {
                    const friendlyName = templateNames[tpl] || tpl.substring(0, 12) + '...';
                    html += '<div class="sandbox-group"><div class="sandbox-group-title">' + friendlyName + '</div>';
                    sandboxes.forEach(sb => { html += renderSandbox(sb); });
                    html += '</div>';
                }

                listDiv.innerHTML = html;
            } catch (err) {
                listDiv.innerHTML = '<div class="no-sandboxes">Error loading sandboxes</div>';
            }
        }

        function renderSandbox(sb) {
            return `
                <div class="sandbox-item" id="sandbox-${sb.sandbox_id}">
                    <div class="sandbox-status"></div>
                    <div class="sandbox-info">
                        <div class="sandbox-id">${sb.sandbox_id}</div>
                        <div class="sandbox-template">${sb.template || 'default'}</div>
                    </div>
                    <button class="kill-btn" onclick="killSandbox('${sb.sandbox_id}')">Kill</button>
                </div>
            `;
        }

        async function killSandbox(sandboxId) {
            const btn = document.querySelector(`#sandbox-${sandboxId} .kill-btn`);
            if (btn) {
                btn.disabled = true;
                btn.textContent = '...';
            }

            try {
                const response = await fetch(`/api/sandboxes/${sandboxId}`, {
                    method: 'DELETE'
                });
                const data = await response.json();

                if (data.success) {
                    const item = document.getElementById(`sandbox-${sandboxId}`);
                    if (item) item.remove();
                } else {
                    alert('Failed to kill sandbox: ' + (data.error || 'Unknown error'));
                    if (btn) {
                        btn.disabled = false;
                        btn.textContent = 'Kill';
                    }
                }
            } catch (err) {
                alert('Error: ' + err.message);
                if (btn) {
                    btn.disabled = false;
                    btn.textContent = 'Kill';
                }
            }

            // Refresh after a short delay
            setTimeout(refreshSandboxes, 500);
        }

        // Step progress with accumulated details
        const stepDetails = {};

        function updateStep(stepNum, status, detail) {
            const step = document.getElementById('step' + stepNum);
            step.className = 'step ' + status;

            if (detail) {
                // Accumulate details for this step
                if (!stepDetails[stepNum]) stepDetails[stepNum] = [];
                stepDetails[stepNum].push(detail);

                // Show accumulated details (last 3)
                const details = stepDetails[stepNum];
                const shown = details.slice(-3).join(' → ');
                step.querySelector('.step-detail').textContent = shown;
            }

            const icon = step.querySelector('.step-icon');
            if (status === 'done') icon.textContent = '✓';
            else if (status === 'error') icon.textContent = '✗';
            else if (status === 'running') icon.textContent = '⋯';
        }

        function resetSteps() {
            // Clear accumulated details
            for (let i = 1; i <= 6; i++) {
                stepDetails[i] = [];
                const step = document.getElementById('step' + i);
                step.className = 'step pending';
                step.querySelector('.step-icon').textContent = i;
                step.querySelector('.step-detail').textContent = ['Spinning up isolated E2B sandbox environment', 'Uploading Claude Agent SDK script to sandbox', 'Uploading your document for analysis', 'Claude Agent SDK analyzing the document', 'Writing analysis results to sandbox', 'Fetching results from sandbox'][i-1];
            }
        }

        function toggleLogs() {
            const output = document.getElementById('output');
            const toggle = document.getElementById('logsToggle');
            if (output.style.display === 'none') {
                output.style.display = 'block';
                toggle.textContent = 'Hide Full Logs';
            } else {
                output.style.display = 'none';
                toggle.textContent = 'Show Full Logs';
            }
        }

        function extractCleanResult(fullOutput) {
            const lines = fullOutput.split('\\n');
            let inResult = false;
            let result = [];

            for (let i = 0; i < lines.length; i++) {
                const line = lines[i];

                // Check for result section markers (=== lines)
                if (line.match(/^={10,}$/)) {
                    // Check if next line is "ANALYSIS RESULT"
                    if (i + 1 < lines.length && lines[i + 1].includes('ANALYSIS RESULT')) {
                        inResult = true;
                        i++; // Skip the header
                        continue;
                    }
                    // If we're in result section, this is the end marker
                    if (inResult) {
                        break;
                    }
                    continue;
                }

                // Skip config/debug lines
                if (line.startsWith('Config:') || line.startsWith('Caching:') || line.startsWith('ANALYSIS RESULT')) {
                    continue;
                }

                // Collect result lines
                if (inResult) {
                    result.push(line);
                }
            }

            // Return cleaned result or fallback
            if (result.length > 0) {
                return result.join('\\n').trim();
            }

            // Fallback: filter out known debug lines
            return lines.filter(l =>
                !l.startsWith('Config:') &&
                !l.startsWith('Caching:') &&
                !l.match(/^={10,}$/) &&
                l !== 'ANALYSIS RESULT'
            ).join('\\n').trim();
        }

        async function runAgent() {
            if (!fileContent) {
                alert('Please upload a file first!');
                return;
            }

            const btn = document.getElementById('runBtn');
            const steps = document.getElementById('steps');
            const output = document.getElementById('output');
            const finalStatus = document.getElementById('finalStatus');
            const resultSection = document.getElementById('resultSection');
            const cleanResult = document.getElementById('cleanResult');
            const logsToggle = document.getElementById('logsToggle');

            btn.disabled = true;
            steps.style.display = 'block';
            output.style.display = 'none';
            finalStatus.style.display = 'none';
            resultSection.style.display = 'none';
            logsToggle.style.display = 'none';
            logsToggle.textContent = 'Show Full Logs';
            resetSteps();

            // Gather config
            const agentConfig = {
                model: document.getElementById('agentModel').value,
                max_tokens: parseInt(document.getElementById('agentMaxTokens').value),
                file_content: fileContent,
                file_name: fileName
            };

            try {
                const response = await fetch('/run-agent-steps', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(agentConfig)
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
                                    // Store full logs
                                    output.textContent = data.result;

                                    // Extract and show clean result
                                    const clean = extractCleanResult(data.result);
                                    cleanResult.textContent = clean;
                                    resultSection.style.display = 'block';
                                    logsToggle.style.display = 'block';
                                }
                                if (data.final) {
                                    finalStatus.style.display = 'block';
                                    finalStatus.className = 'final-status ' + (data.success ? 'success' : 'error');
                                    finalStatus.textContent = data.message;
                                    // Refresh sandbox list after agent completes
                                    refreshSandboxes();
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
            refreshSandboxes();
        }

        // Initial load
        refreshSandboxes();
        // Auto-refresh every 10 seconds
        setInterval(refreshSandboxes, 10000);
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/sandboxes', methods=['GET'])
def list_sandboxes():
    """List all running sandboxes."""
    try:
        from e2b_code_interpreter import Sandbox

        # Get paginator and fetch items
        paginator = Sandbox.list()
        sandboxes = paginator.next_items()

        sandbox_list = []
        for sb in sandboxes:
            sandbox_list.append({
                'sandbox_id': sb.sandbox_id,
                'template': sb.template_id or 'default',
                'started_at': sb.started_at.isoformat() if sb.started_at else None
            })

        return jsonify({'success': True, 'sandboxes': sandbox_list})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e), 'sandboxes': []})


@app.route('/api/sandboxes/<sandbox_id>', methods=['DELETE'])
def kill_sandbox(sandbox_id):
    """Kill a specific sandbox."""
    try:
        from e2b_code_interpreter import Sandbox
        sandbox = Sandbox.connect(sandbox_id)
        sandbox.kill()
        return jsonify({'success': True, 'message': f'Sandbox {sandbox_id} killed'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


def generate_steps(agent_config):
    """Generator that yields SSE events for each step."""

    def send_event(data):
        return f"data: {json.dumps(data)}\n\n"

    sandbox = None

    try:
        # Step 1: Create slave sandbox
        yield send_event({'step': 1, 'status': 'running', 'detail': f'Creating SLAVE sandbox (template: {config.SLAVE_TEMPLATE})...'})

        from e2b_code_interpreter import Sandbox
        try:
            sandbox = Sandbox.create(template=config.SLAVE_TEMPLATE, timeout=config.SLAVE_TIMEOUT)
        except Exception as e:
            if config.FALLBACK_TO_DEFAULT:
                yield send_event({'step': 1, 'status': 'running', 'detail': f'Template not found, using default...'})
                sandbox = Sandbox.create(timeout=config.SLAVE_TIMEOUT)
            else:
                raise

        sandbox_id = sandbox.get_info().sandbox_id

        yield send_event({'step': 1, 'status': 'done', 'detail': f'SLAVE sandbox created: {sandbox_id[:12]}...'})

        # Step 2: Upload agent script with config
        yield send_event({'step': 2, 'status': 'running', 'detail': 'Uploading agent script with config...'})

        with open(config.AGENT_SCRIPT_PATH, 'r') as f:
            agent_code = f.read()
        sandbox.files.write(config.AGENT_SCRIPT_PATH, agent_code)

        # Also upload config.py for agent to use
        with open('/home/user/config.py', 'r') as f:
            config_code = f.read()
        sandbox.files.write('/home/user/config.py', config_code)

        # Write runtime config as JSON for the agent
        runtime_config = {
            'model': agent_config.get('model', config.AGENT_MODEL),
            'max_tokens': agent_config.get('max_tokens', config.AGENT_MAX_TOKENS),
            'system_prompt': config.AGENT_SYSTEM_PROMPT,
            'analysis_prompt': config.AGENT_ANALYSIS_PROMPT
        }
        sandbox.files.write('/home/user/runtime_config.json', json.dumps(runtime_config))

        yield send_event({'step': 2, 'status': 'done', 'detail': f'Agent configured (model: {runtime_config["model"]})'})

        # Step 3: Upload user's file
        yield send_event({'step': 3, 'status': 'running', 'detail': f'Uploading {agent_config.get("file_name", "document")}...'})

        file_content = agent_config.get('file_content', '')
        sandbox.files.write(config.TEST_FILE_PATH, file_content)

        yield send_event({'step': 3, 'status': 'done', 'detail': f'Document uploaded ({len(file_content)} bytes)'})

        # Step 4: Run agent
        yield send_event({'step': 4, 'status': 'running', 'detail': f'Running Claude Agent SDK ({runtime_config["model"]})...'})

        # Run the agent with API key
        api_key = os.environ.get('ANTHROPIC_API_KEY', '')
        result = sandbox.commands.run(
            f'ANTHROPIC_API_KEY={api_key} python {config.AGENT_SCRIPT_PATH} 2>&1',
            timeout=config.AGENT_TASK_TIMEOUT
        )
        agent_output = result.stdout

        if result.exit_code != 0:
            yield send_event({'step': 4, 'status': 'error', 'detail': f'Agent failed with exit code {result.exit_code}'})
            yield send_event({'result': agent_output})
            yield send_event({'final': True, 'success': False, 'message': f'Agent failed with exit code {result.exit_code}'})
            sandbox.kill()
            return

        yield send_event({'step': 4, 'status': 'done', 'detail': 'Agent analysis completed'})

        # Step 5: Save results
        yield send_event({'step': 5, 'status': 'running', 'detail': 'Saving analysis results...'})

        sandbox.files.write(config.RESULTS_PATH, agent_output)

        yield send_event({'step': 5, 'status': 'done', 'detail': f'Results saved to {config.RESULTS_PATH}'})

        # Step 6: Retrieve results
        yield send_event({'step': 6, 'status': 'running', 'detail': 'Fetching results from sandbox...'})

        final_results = sandbox.files.read(config.RESULTS_PATH)

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
        if sandbox:
            try:
                sandbox.kill()
            except:
                pass


@app.route('/run-agent-steps', methods=['POST'])
def run_agent_steps():
    """SSE endpoint for step-by-step agent execution."""
    agent_config = request.get_json() or {}
    return Response(
        generate_steps(agent_config),
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
    app.run(host=config.FLASK_HOST, port=config.FLASK_PORT, debug=False, threaded=True)
