"""
AIOS Middleware Demo - UI Server (REAL AI ONLY)
Serves the web interface and triggers the REAL AIOS agent with LLM
NO FALLBACK - Requires API keys and AIOS kernel
"""

from flask import Flask, send_file, jsonify, request
import subprocess
import os
import sys
import yaml
import requests
from pathlib import Path

app = Flask(__name__)

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

# ONLY use the real AIOS agent - NO FALLBACK
AGENT_SCRIPT = PROJECT_ROOT / "middleware_demo" / "middleware_agent.py"
CONFIG_PATH = PROJECT_ROOT / "aios" / "config" / "config.yaml"


@app.route('/')
def index():
    """Serve the main UI page"""
    return send_file('web_ui.html')


def _is_non_placeholder(value: str | None) -> bool:
    if not value:
        return False
    trimmed = value.strip()
    if not trimmed:
        return False
    return trimmed.lower() not in {"your-api-key-here", "changeme", "<your-api-key>"}


def _has_valid_key(api_keys: dict, backend: str | None) -> bool:
    backend = (backend or "").lower()
    if backend in {"ollama", "vllm"}:
        return True
    if backend == "huggingface":
        key = (api_keys.get("huggingface") or {}).get("auth_token")
        return _is_non_placeholder(key)
    return _is_non_placeholder(api_keys.get(backend))


def _select_default_model(config: dict) -> dict | None:
    models = config.get("llms", {}).get("models", [])
    api_keys = config.get("api_keys", {})

    for model in models:
        backend = model.get("backend") or model.get("provider")
        if _has_valid_key(api_keys, backend):
            return model
    return models[0] if models else None


def check_prerequisites():
    """Check if all prerequisites are met for AIOS agent"""
    errors = []

    # Check 1: AIOS kernel running
    try:
        response = requests.get("http://localhost:8000/health", timeout=2)
        if not response.ok:
            errors.append("AIOS kernel is not responding properly on port 8000")
    except requests.exceptions.RequestException:
        errors.append("AIOS kernel is NOT running on port 8000. Start it with: python3.11 -m uvicorn runtime.launch:app --host 0.0.0.0 --port 8000")

    # Check 2: Config file exists
    if not CONFIG_PATH.exists():
        errors.append(f"Config file not found at {CONFIG_PATH}")
        return errors

    # Check 3: API keys configured
    try:
        with open(CONFIG_PATH, 'r') as f:
            config = yaml.safe_load(f)

        api_keys = config.get('api_keys', {})
        has_key = any(
            _has_valid_key(api_keys, backend)
            for backend in [
                "openai",
                "anthropic",
                "gemini",
                "groq",
                "huggingface",
                "ollama",
                "vllm",
            ]
        )

        if not has_key:
            errors.append("No valid API key found in config.yaml. Add your OpenAI, Anthropic, or Gemini API key.")

        # Check LLM configuration
        llms = config.get('llms', {}).get('models', [])
        if not llms:
            errors.append("No LLM models configured in config.yaml")

    except Exception as e:
        errors.append(f"Failed to read config file: {str(e)}")

    return errors


@app.route('/api/check-prerequisites', methods=['GET'])
def api_check_prerequisites():
    """API endpoint to check prerequisites"""
    errors = check_prerequisites()

    if errors:
        return jsonify({
            "ready": False,
            "errors": errors
        }), 400
    else:
        return jsonify({
            "ready": True,
            "message": "All prerequisites met. Ready to run AIOS agent."
        })


@app.route('/api/trigger-agent', methods=['POST'])
def trigger_agent():
    """Trigger the REAL AIOS middleware agent with LLM"""

    # First check prerequisites
    errors = check_prerequisites()
    if errors:
        return jsonify({
            "success": False,
            "message": "Prerequisites not met",
            "errors": errors,
            "type": "prerequisites"
        }), 400

    try:
        # Get LLM config from request or use defaults
        data = request.get_json(silent=True) or {}
        llm_name = data.get('llm_name')
        llm_backend = data.get('llm_backend')

        if not llm_name or not llm_backend:
            with open(CONFIG_PATH, 'r') as f:
                config = yaml.safe_load(f) or {}
            default_model = _select_default_model(config)
            if default_model:
                llm_name = llm_name or default_model.get('name')
                llm_backend = llm_backend or default_model.get('backend') or default_model.get('provider')

        if not llm_name or not llm_backend:
            raise ValueError("No LLM model configured. Update aios/config/config.yaml")

        # Get the virtual environment python
        venv_python = PROJECT_ROOT / "venv" / "bin" / "python"

        # Build command for REAL AIOS agent
        cmd = [
            str(venv_python), str(AGENT_SCRIPT),
            "--llm-name", llm_name,
            "--llm-backend", llm_backend,
            "--aios-kernel-url", "http://localhost:8000",
            "--source-url", "http://localhost:5001",
            "--destination-url", "http://localhost:5002"
        ]

        print(f"🚀 Executing REAL AIOS agent: {' '.join(cmd)}")

        # Run the agent
        result = subprocess.run(
            cmd,
            cwd=str(PROJECT_ROOT),
            capture_output=True,
            text=True,
            timeout=120  # 2 minutes for LLM call
        )

        if result.returncode == 0:
            return jsonify({
                "success": True,
                "message": "AIOS agent with LLM executed successfully",
                "output": result.stdout,
                "using_ai": True,
                "llm_used": f"{llm_backend}:{llm_name}"
            })
        else:
            # Parse error to give helpful message
            error_msg = result.stderr.strip()
            if not error_msg:
                error_msg = result.stdout.strip()

            if "API key" in error_msg or "authentication" in error_msg.lower():
                error_type = "api_key"
                friendly_msg = "Invalid or missing API key. Check your config.yaml"
            elif "connection" in error_msg.lower() or "refused" in error_msg.lower():
                error_type = "connection"
                friendly_msg = "Cannot connect to AIOS kernel. Make sure it's running on port 8000"
            else:
                error_type = "execution"
                friendly_msg = "Agent execution failed"

            return jsonify({
                "success": False,
                "message": friendly_msg,
                "error": error_msg,
                "type": error_type
            }), 500

    except subprocess.TimeoutExpired:
        return jsonify({
            "success": False,
            "message": "Agent execution timed out after 2 minutes",
            "error": "The LLM call took too long or the agent is stuck",
            "type": "timeout"
        }), 500

    except Exception as e:
        return jsonify({
            "success": False,
            "message": f"Unexpected error: {str(e)}",
            "type": "unknown"
        }), 500


@app.route('/health')
def health():
    """Health check endpoint"""
    return jsonify({
        "status": "healthy",
        "service": "ui_server"
    })


if __name__ == "__main__":
    print("=" * 70)
    print("🎨 AIOS Middleware Demo - Web UI Server")
    print("=" * 70)
    print()
    print("Starting UI server on http://localhost:3000")
    print()
    print("Open your browser and navigate to:")
    print("  👉 http://localhost:3000")
    print()
    print("=" * 70)
    print()

    # Enable CORS for local development
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'GET,POST,OPTIONS')
        return response

    app.run(host='0.0.0.0', port=3000, debug=False)
