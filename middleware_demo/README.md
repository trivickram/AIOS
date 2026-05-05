# AIOS Middleware Agent Demo

This demo showcases an intelligent middleware agent built with the AIOS (AI Agent Operating System) framework and Cerebrum SDK. The agent acts as a smart data bridge between two systems with incompatible data formats.

## 📋 Overview

The demo consists of three main components:

1. **Mock Flask Servers** (`flask_servers.py`)
   - Source server with legacy customer data format
   - Destination server with modernized user data format

2. **AIOS Tools** (`aios_tools.py`)
   - `SourceDataFetcherTool`: Fetches data from the source server
   - `DestinationDataPusherTool`: Pushes transformed data to the destination server

3. **Middleware Agent** (`middleware_agent.py`)
   - Intelligent agent that coordinates the entire data flow
   - Uses LLM reasoning to understand and transform data structures

## 🏗️ Architecture

```
┌─────────────────┐         ┌──────────────────┐         ┌─────────────────┐
│  Source Server  │         │  AIOS Middleware │         │ Destination     │
│  (Flask)        │◄────────┤     Agent        ├────────►│ Server (Flask)  │
│                 │  Fetch  │                  │  Push   │                 │
│ Legacy Format:  │         │  Components:     │         │ Modern Format:  │
│ - first_name    │         │  • LLM Kernel    │         │ - fullName      │
│ - last_name     │         │  • Tool Manager  │         │ - phoneDetails  │
│ - contact_num   │         │  • Memory Layer  │         │ - emailAddress  │
│ - email_addr    │         │  • Storage Layer │         │ - accountStatus │
│ - status_code   │         │  • Scheduler     │         │                 │
└─────────────────┘         └──────────────────┘         └─────────────────┘
```

## 📦 Data Format Transformation

### Source Format (Legacy)
```json
{
  "customer_id": "CUST001",
  "first_name": "John",
  "last_name": "Doe",
  "contact_num": "555-0123",
  "email_addr": "john.doe@example.com",
  "join_date": "2020-01-15",
  "status_code": "A"
}
```

### Destination Format (Modern)
```json
{
  "userId": "CUST001",
  "fullName": "John Doe",
  "phoneDetails": {
    "number": "5550123",
    "formatted": "555-0123"
  },
  "emailAddress": "john.doe@example.com",
  "registrationDate": "2020-01-15",
  "accountStatus": "active"
}
```

## 🚀 Getting Started

### Prerequisites

1. **Python 3.11** (required by AIOS)
2. **AIOS Kernel** running at `http://localhost:8000`
3. **Flask** for mock servers
4. **API Keys** configured in `aios/config/config.yaml`

### Installation

```bash
# Navigate to the demo directory
cd middleware_demo

# Install Flask if not already installed
source ../venv/bin/activate
pip install flask requests
```

### Configuration

Make sure your `aios/config/config.yaml` has an LLM configured:

```yaml
api_keys:
  openai: "your-openai-key"  # or other provider

llms:
  models:
    - name: "gpt-4o-mini"
      backend: "openai"
```

## 🎯 Running the Demo

### Step 1: Start the AIOS Kernel

In a terminal:

```bash
cd /Users/baratamtrivickram/AIOS
source venv/bin/activate
python3.11 -m uvicorn runtime.launch:app --host 0.0.0.0 --port 8000
```

Wait for the kernel to start and show "AIOS is running..."

### Step 2: Start the Flask Servers

In a new terminal:

```bash
cd /Users/baratamtrivickram/AIOS/middleware_demo
source ../venv/bin/activate
python flask_servers.py
```

You should see:
```
🚀 Starting Source Server on port 5001
🚀 Starting Destination Server on port 5002
✅ Both servers are running!
```

### Step 3: Run the Middleware Agent

In a third terminal:

```bash
cd /Users/baratamtrivickram/AIOS/middleware_demo
source ../venv/bin/activate
python middleware_agent.py --llm-name gpt-4o-mini --llm-backend openai
```

### Alternative: Run Everything with One Script

```bash
cd /Users/baratamtrivickram/AIOS/middleware_demo
bash run_demo.sh
```

## 🧪 Testing Components Individually

### Test Flask Servers

```bash
# Test source server
curl http://localhost:5001/api/source

# Test destination server health
curl http://localhost:5002/health
```

### Test AIOS Tools

```bash
cd /Users/baratamtrivickram/AIOS/middleware_demo
source ../venv/bin/activate
python aios_tools.py
```

This will run standalone tests of both tools.

## 📊 Expected Output

When the agent runs successfully, you should see:

```
🤖 AIOS MIDDLEWARE AGENT
======================================================================
LLM: gpt-4o-mini (openai)
AIOS Kernel: http://localhost:8000
Source Server: http://localhost:5001
Destination Server: http://localhost:5002
======================================================================

🔧 Initializing AIOS client...
✅ AIOS client initialized successfully

🔧 Registering middleware tools...
✅ Tools registered successfully

🚀 EXECUTING MIDDLEWARE TASK
======================================================================

📥 Step 1: Fetching data from source server...
✅ Successfully fetched 3 customer records

🔄 Step 2: Transforming data structure...
✅ Transformed 3 records

📤 Step 3: Pushing data to destination server...
✅ Successfully pushed data to destination server

✅ MIDDLEWARE TASK COMPLETED SUCCESSFULLY
```

## 🔧 Command-Line Options

```bash
python middleware_agent.py [OPTIONS]

Options:
  --llm-name TEXT           LLM model name (default: gpt-4o-mini)
  --llm-backend TEXT        LLM backend (openai|anthropic|gemini|groq|ollama|vllm)
  --aios-kernel-url TEXT    AIOS kernel URL (default: http://localhost:8000)
  --source-url TEXT         Source server URL (default: http://localhost:5001)
  --destination-url TEXT    Destination server URL (default: http://localhost:5002)
```

### Examples

Using OpenAI GPT-4:
```bash
python middleware_agent.py --llm-name gpt-4o --llm-backend openai
```

Using Anthropic Claude:
```bash
python middleware_agent.py --llm-name claude-3-5-sonnet-20241022 --llm-backend anthropic
```

Using Ollama (local):
```bash
# Make sure ollama is running: ollama serve
# And model is pulled: ollama pull qwen2.5:7b
python middleware_agent.py --llm-name qwen2.5:7b --llm-backend ollama
```

## 🎓 Key Concepts Demonstrated

### 1. AIOS Tool System
- Custom tools inheriting from BaseTool pattern
- OpenAI function calling format
- Tool registration with the AIOS kernel

### 2. LLM-Powered Data Transformation
- Natural language system prompts for complex tasks
- Structured reasoning about data mappings
- Error handling and validation

### 3. AIOS Layers
- **LLM Layer**: Manages language model interactions
- **Tool Layer**: Provides external capabilities
- **Memory Layer**: Maintains context and state
- **Storage Layer**: Persists agent data
- **Scheduler**: Coordinates concurrent operations

### 4. Agent Architecture
- Separation of concerns (tools vs. agent logic)
- Configurable and extensible design
- Production-ready error handling

## 🔍 Troubleshooting

### AIOS Kernel Not Running
```
Error: Failed to connect to AIOS kernel
```
**Solution**: Make sure the AIOS kernel is running on port 8000.

### Flask Servers Not Accessible
```
Error: Failed to fetch data from source server
```
**Solution**: Check that both Flask servers are running on ports 5001 and 5002.

### API Key Issues
```
Error: Invalid API key
```
**Solution**: Verify your API keys in `aios/config/config.yaml`.

### Import Errors
```
ModuleNotFoundError: No module named 'cerebrum'
```
**Solution**: Make sure you've activated the virtual environment with Cerebrum installed.

## 📁 Project Structure

```
middleware_demo/
├── README.md                 # This file
├── flask_servers.py          # Mock source and destination servers
├── aios_tools.py            # AIOS tools for data fetching and pushing
├── middleware_agent.py      # Main agent implementation
├── run_demo.sh              # Convenience script to run everything
└── requirements.txt         # Additional dependencies (Flask)
```

## 🚀 Next Steps

### Extend the Demo

1. **Add More Transformations**: Implement complex data validation and enrichment
2. **Error Recovery**: Add retry logic and fallback strategies
3. **Monitoring**: Integrate logging and metrics collection
4. **Multiple Sources**: Extend to handle data from multiple source systems
5. **Streaming**: Implement real-time data streaming instead of batch processing

### Production Deployment

For production use:
1. Use proper authentication for Flask servers
2. Add rate limiting and request validation
3. Implement comprehensive error handling
4. Set up monitoring and alerting
5. Use environment variables for configuration
6. Deploy AIOS kernel with proper resource allocation

## 📚 Resources

- [AIOS Documentation](https://docs.aios.foundation/)
- [AIOS GitHub Repository](https://github.com/agiresearch/AIOS)
- [Cerebrum SDK Repository](https://github.com/agiresearch/Cerebrum)
- [AIOS Paper](https://arxiv.org/abs/2403.16971)

## 🤝 Contributing

This is a demo project for learning purposes. Feel free to:
- Extend the functionality
- Add new transformation patterns
- Improve error handling
- Share your implementations

## 📄 License

This demo follows the AIOS project license. See the main AIOS repository for details.

---

**Built with ❤️ using AIOS and Cerebrum SDK**
