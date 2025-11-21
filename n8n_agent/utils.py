import json
from typing import Dict, List, Any, Optional
from pydantic import BaseModel

class N8nNode(BaseModel):
    id: str
    name: str
    type: str
    typeVersion: float = 1.0
    position: List[float]
    parameters: Dict[str, Any] = {}
    credentials: Dict[str, Any] = {}

class N8nConnection(BaseModel):
    node: str
    type: str
    index: int

class N8nWorkflow(BaseModel):
    nodes: List[N8nNode]
    connections: Dict[str, Dict[str, List[List[N8nConnection]]]]
    # connections structure: { "SourceNodeName": { "main": [ [ { "node": "TargetNodeName", "type": "main", "index": 0 } ] ] } }

def load_workflow(file_path: str) -> Dict[str, Any]:
    with open(file_path, 'r') as f:
        return json.load(f)

def parse_workflow(workflow_data: Dict[str, Any]) -> N8nWorkflow:
    """
    Parses raw n8n workflow JSON into a structured N8nWorkflow object.
    Handles both the 'nodes' list and 'connections' dictionary.
    """
    nodes = []
    for node_data in workflow_data.get("nodes", []):
        # Handle legacy vs new format if needed, but standard n8n export usually has these fields
        nodes.append(N8nNode(
            id=node_data.get("id", node_data.get("name")), # Fallback to name if ID missing
            name=node_data["name"],
            type=node_data["type"],
            typeVersion=node_data.get("typeVersion", 1.0),
            position=node_data.get("position", [0, 0]),
            parameters=node_data.get("parameters", {}),
            credentials=node_data.get("credentials", {})
        ))
    
    connections = workflow_data.get("connections", {})
    
    return N8nWorkflow(nodes=nodes, connections=connections)

def get_workflow_summary(workflow: N8nWorkflow) -> str:
    """
    Creates a textual summary of the workflow for the LLM.
    """
    summary = "Workflow Nodes:\n"
    for node in workflow.nodes:
        summary += f"- {node.name} (Type: {node.type})\n"
        summary += f"  Parameters: {json.dumps(node.parameters, indent=2)}\n"
    
    summary += "\nConnections:\n"
    for source_node, outputs in workflow.connections.items():
        for output_name, connections_list in outputs.items():
            for connection_group in connections_list:
                for conn in connection_group:
                    summary += f"- {source_node} -> {conn.node} (via {output_name})\n"
    
    return summary
