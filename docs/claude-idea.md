# Inteligentní n8n-to-Python Agent s e2b Integration

## Executive Summary

Návrh inteligentního agenta, který automaticky převádí n8n workflows na samostatné Python skripty s využitím e2b sandboxu pro iterativní testování a vylepšování. Agent kombinuje statickou analýzu, dynamické testování a LLM-based opravy pro dosažení funkčního kódu.

## Problém a Řešení

### Současný stav (n8n-to-python-transpiler)

**Omezení existujícího řešení:**
- Nepodporuje workflow connections (edges mezi nody)
- Ignoruje závislosti a pořadí execution
- Nemá data flow mezi nody
- Chybí podpora n8n expressions (`{{$json.field}}`)
- Žádné error handling
- Hardcoded credentials
- Podporuje pouze 19 z 350+ n8n node typů

### Navrhované řešení

Třífázový inteligentní systém:
1. **Enhanced Transpiler** - Kompletní parsování n8n struktury
2. **E2B Executor** - Bezpečné testování v cloudu
3. **AI Improver** - Automatické opravy pomocí LLM

## Architektura

```
┌─────────────────────────────────────────────────────┐
│                   User Interface                     │
│         (Upload n8n workflow → Get Python code)      │
└──────────────────┬──────────────────────────────────┘
                   │
┌──────────────────▼──────────────────────────────────┐
│              Orchestration Agent                     │
│   - Workflow analysis and dependency resolution      │
│   - Execution planning and optimization              │
│   - Error recovery and retry logic                   │
└──────────┬───────────────────────┬──────────────────┘
           │                       │
┌──────────▼──────────┐  ┌────────▼──────────────────┐
│  Transpiler Agent   │  │   Execution Agent         │
│ - Parse n8n JSON    │  │ - e2b sandbox management  │
│ - Build DAG         │  │ - Dependency installation │
│ - Generate Python   │  │ - Code execution          │
│ - Handle expressions│  │ - Result collection       │
└──────────┬──────────┘  └────────┬──────────────────┘
           │                       │
┌──────────▼───────────────────────▼──────────────────┐
│              Improvement Agent                       │
│   - Analyze execution results and errors             │
│   - Generate fixes using Claude/GPT-4                │
│   - Validate corrections                             │
│   - Iterative refinement (max 5 iterations)         │
└──────────────────────────────────────────────────────┘
```

## Komponenty

### 1. Enhanced Transpiler

```python
class N8nWorkflowTranspiler:
    """
    Kompletní transpiler podporující všechny n8n features
    """
    def __init__(self, workflow_json):
        self.workflow = workflow_json
        self.nodes = self._parse_nodes()
        self.connections = self._parse_connections()
        self.dag = self._build_dependency_graph()

    def _parse_nodes(self):
        """Parse all nodes with their parameters and credentials"""
        nodes = {}
        for node in self.workflow['nodes']:
            nodes[node['name']] = {
                'type': node['type'],
                'parameters': node.get('parameters', {}),
                'credentials': node.get('credentials', {}),
                'position': node.get('position', [0, 0]),
                'disabled': node.get('disabled', False)
            }
        return nodes

    def _parse_connections(self):
        """Build connection map from workflow edges"""
        connections = defaultdict(list)
        for conn in self.workflow.get('connections', {}).values():
            for edge in conn.get('main', [[]]):
                for connection in edge:
                    source = connection['node']
                    target = connection['index']
                    connections[source].append(target)
        return connections

    def _build_dependency_graph(self):
        """Create DAG for execution order"""
        return TopologicalSorter(self.connections)

    def generate_python_code(self):
        """Generate complete Python workflow"""
        code = self._generate_imports()
        code += self._generate_workflow_class()
        code += self._generate_main_function()
        return code
```

### 2. E2B Execution Agent

```python
class E2BWorkflowExecutor:
    """
    Manages e2b sandbox lifecycle and code execution
    """
    def __init__(self, mcp_config=None):
        self.mcp_config = mcp_config or {}
        self.sandbox = None

    async def setup_sandbox(self, requirements):
        """Create sandbox with necessary dependencies"""
        self.sandbox = Sandbox.create(
            timeout=300,
            mcp=self._map_mcp_integrations(),
            envs=self._extract_env_vars()
        )

        # Install Python dependencies
        deps = self._analyze_requirements(requirements)
        install_cmd = f"pip install {' '.join(deps)}"
        await self.sandbox.commands.run(install_cmd)

    def _map_mcp_integrations(self):
        """Map n8n nodes to e2b MCP servers"""
        mcp_mapping = {
            'Postgres': 'postgres',
            'MySQL': 'mysql',
            'MongoDB': 'mongodb',
            'Slack': 'slack',
            'GitHub': 'github',
            'OpenAI': 'openai',
            'Notion': 'notion'
        }
        return {
            mcp_mapping[node]: self.mcp_config.get(node, {})
            for node in self.detected_nodes
            if node in mcp_mapping
        }

    async def execute_code(self, python_code):
        """Execute generated Python code in sandbox"""
        # Upload code
        self.sandbox.files.write('/home/user/workflow.py', python_code)

        # Execute with monitoring
        execution = self.sandbox.run_code(
            'exec(open("/home/user/workflow.py").read())',
            on_stdout=self._capture_output,
            on_stderr=self._capture_errors
        )

        return WorkflowResult(
            success=execution.error is None,
            output=execution.text,
            errors=execution.error,
            metrics=self.sandbox.get_metrics()
        )
```

### 3. AI Improvement Agent

```python
class WorkflowImprover:
    """
    Uses LLM to fix errors and improve generated code
    """
    def __init__(self, llm_client):
        self.llm = llm_client

    async def analyze_and_fix(self, code, error_result):
        """Analyze errors and generate fixes"""
        prompt = f"""
        The following Python code generated from n8n workflow has errors:

        CODE:
        {code}

        ERRORS:
        {error_result.errors}

        OUTPUT:
        {error_result.output}

        Please fix the code to:
        1. Resolve all errors
        2. Ensure proper data flow between nodes
        3. Add proper error handling
        4. Validate inputs and outputs

        Return only the corrected Python code.
        """

        response = await self.llm.generate(prompt)
        return self._extract_code(response)

    def validate_improvements(self, original, improved, test_data=None):
        """Validate that improvements maintain functionality"""
        # Static analysis
        ast_original = ast.parse(original)
        ast_improved = ast.parse(improved)

        # Check that key functions still exist
        original_funcs = self._extract_functions(ast_original)
        improved_funcs = self._extract_functions(ast_improved)

        if not original_funcs.issubset(improved_funcs):
            raise ValueError("Improved code missing original functions")

        return True
```

## Implementační Strategie

### Fáze 1: MVP (Týden 1-2)

**Základní funkcionalita:**
- Parsování jednoduchých n8n workflows
- Podpora 10 nejběžnějších node typů
- Základní e2b execution
- Jednoduchý error reporting

**Podporované node types:**
1. HTTP Request
2. Set
3. IF
4. Code
5. Webhook
6. PostgreSQL
7. MySQL
8. OpenAI
9. Slack
10. Schedule Trigger

### Fáze 2: Enhanced Features (Týden 3-4)

**Pokročilé features:**
- Kompletní workflow dependency graph
- Expression evaluation (`{{$json}}`, `{{$node}}`)
- Credential management
- Error recovery s LLM
- MCP integrations (20+ services)

### Fáze 3: Production Ready (Týden 5-6)

**Enterprise features:**
- Podpora všech n8n node typů
- Optimalizace výkonu
- Caching a persistence
- Monitoring a logging
- REST API a Web UI

## Příklad Použití

### 1. Jednoduchý Workflow

```python
# n8n workflow: Webhook → Transform → PostgreSQL

from n8n_to_python_agent import WorkflowAgent

# Load n8n workflow
with open('webhook_to_db.json') as f:
    workflow = json.load(f)

# Create agent
agent = WorkflowAgent(
    e2b_api_key="e2b_xxx",
    openai_api_key="sk_xxx"
)

# Convert with auto-improvement
result = await agent.convert_workflow(
    workflow,
    max_iterations=5,
    test_data={'webhook_payload': {...}}
)

# Save standalone Python script
with open('workflow.py', 'w') as f:
    f.write(result.python_code)

print(f"Conversion successful after {result.iterations} iterations")
print(f"Execution time: {result.metrics.execution_time}ms")
```

### 2. Complex Workflow s MCP

```python
# n8n workflow: GitHub → OpenAI → Slack notification

agent = WorkflowAgent(
    e2b_api_key="e2b_xxx",
    mcp_config={
        'github': {'token': 'ghp_xxx'},
        'openai': {'api_key': 'sk_xxx'},
        'slack': {'bot_token': 'xoxb_xxx'}
    }
)

result = await agent.convert_workflow(
    workflow,
    use_mcp=True,  # Využít MCP integrace místo přímých API calls
    optimize=True   # Optimalizovat pro výkon
)
```

## Technické Detaily

### Mapování n8n → Python

| n8n Feature | Python Implementation |
|------------|----------------------|
| Nodes | Python functions/classes |
| Connections | Function calls with data passing |
| Expressions | Jinja2 templates or eval() |
| Credentials | Environment variables |
| Triggers | Async event loops or schedulers |
| Error workflows | Try-catch blocks |
| Split/Merge | Threading or asyncio |

### Dependency Resolution

```python
def resolve_dependencies(workflow):
    """Automatically detect and install required packages"""
    dependencies = set()

    node_to_package = {
        'Postgres': 'psycopg2-binary',
        'MySQL': 'mysql-connector-python',
        'MongoDB': 'pymongo',
        'OpenAI': 'openai',
        'Slack': 'slack-sdk',
        'SendGrid': 'sendgrid',
        'Telegram': 'python-telegram-bot'
    }

    for node in workflow['nodes']:
        if node['type'] in node_to_package:
            dependencies.add(node_to_package[node['type']])

    return list(dependencies)
```

### Expression Evaluation

```python
class ExpressionEvaluator:
    """Handle n8n expression syntax"""

    def __init__(self, context):
        self.context = context  # Current node data
        self.nodes = {}  # Previous nodes' outputs

    def evaluate(self, expression):
        """
        Evaluate n8n expressions:
        - {{$json.field}} → self.context['field']
        - {{$node["NodeName"].json.field}} → self.nodes['NodeName']['field']
        - {{$env.VAR_NAME}} → os.environ['VAR_NAME']
        """
        # Parse expression
        if expression.startswith('{{') and expression.endswith('}}'):
            expr = expression[2:-2].strip()

            if expr.startswith('$json'):
                return self._eval_json(expr)
            elif expr.startswith('$node'):
                return self._eval_node(expr)
            elif expr.startswith('$env'):
                return self._eval_env(expr)

        return expression  # Return as-is if not an expression
```

## Role e2b v Řešení

### 1. **Bezpečné Testovací Prostředí**
- Izolované spouštění netestovaného kódu
- Žádný dopad na lokální systém
- Paralelní testování více workflows

### 2. **Automatická Správa Dependencies**
- Dynamická instalace Python packages
- Verzování pro různé workflows
- Čisté prostředí pro každý běh

### 3. **MCP Gateway (200+ Integrací)**
- Jednotné API pro externí služby
- Automatická autentizace
- Rate limiting a error handling

### 4. **Monitoring a Debugging**
- Real-time execution logs
- Performance metrics
- Resource usage tracking
- Error stacktraces

### 5. **Persistence a Caching**
- Ukládání workflow states
- Resume failed executions
- Cache pro opakované běhy

## Výhody Řešení

### Pro Vývojáře
✅ **Standalone Python code** - běží kdekoli
✅ **Žádné vendor lock-in** - nezávislé na n8n
✅ **Version control friendly** - čistý Python kód
✅ **Customizable** - lze upravit generovaný kód

### Pro Business
✅ **Cost reduction** - není potřeba n8n instance
✅ **Better performance** - optimalizovaný Python
✅ **Flexibility** - integrace do existujících systémů
✅ **Reliability** - automatické testy a opravy

### Pro DevOps
✅ **Easy deployment** - standardní Python aplikace
✅ **No infrastructure** - e2b sandbox v cloudu
✅ **Scalability** - paralelní execution
✅ **Security** - izolované prostředí

## Metriky Úspěchu

| Metrika | Cíl | Měření |
|---------|-----|--------|
| Conversion success rate | >95% | Successful conversions / Total attempts |
| Average iterations to fix | <3 | Total iterations / Successful conversions |
| Execution time | <30s | Median conversion time |
| Node type coverage | >80% | Supported nodes / Total n8n nodes |
| Code quality | >8/10 | Pylint score |

## Závěr

Tento inteligentní agent představuje významný pokrok v automatizaci workflow konverze. Kombinací statické analýzy, dynamického testování v e2b a AI-powered oprav dosahuje vysoké úspěšnosti při zachování flexibility a nezávislosti generovaného kódu.

Klíčové inovace:
1. **Kompletní podpora n8n features** - ne jen subset
2. **Iterativní vylepšování** - garantuje funkčnost
3. **MCP integrace** - 200+ služeb out-of-the-box
4. **Production-ready output** - čistý, dokumentovaný Python kód

Řešení je ideální pro organizace, které chtějí migrovat z n8n na vlastní Python řešení nebo potřebují větší flexibilitu než n8n nabízí.