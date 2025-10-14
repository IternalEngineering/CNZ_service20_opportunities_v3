# Open Deep Research Service - Complete Overview

## 🔬 What This Service Does

**Open Deep Research** is an advanced AI-powered deep research agent that conducts comprehensive, PhD-level research on any topic. It's a fully open-source system that:

1. **Accepts Research Queries**: Takes user questions and research topics
2. **Plans Research Strategy**: Creates a structured research approach
3. **Conducts Parallel Research**: Spawns multiple researcher agents to gather information simultaneously
4. **Synthesizes Findings**: Compresses and combines research from all sources
5. **Generates Reports**: Produces comprehensive, well-structured research reports
6. **Integrates with PostgreSQL**: Can access and query your UrbanZero database for investment opportunities, ESG data, and sustainability metrics
7. **Stores Results**: Automatically saves all research outputs to the `service20_investment_opportunities` table
8. **Traces Everything**: Full observability through Langfuse for monitoring and optimization

## 🏆 Performance

- **Ranked #6** on Deep Research Bench Leaderboard (0.4344 overall score)
- Evaluated on 100 PhD-level research tasks across 22 fields
- Comparable to commercial deep research agents like Perplexity and SearchGPT

---

## 🤖 Agent Architecture

The service uses a **multi-agent supervisor pattern** with 3 main graphs and 9 key agent nodes:

### Main Agent Graph (deep_researcher)

#### 1. **Clarification Agent** (`clarify_with_user`)
- **Purpose**: Analyzes user queries to determine if clarification is needed
- **Input**: User's initial research question
- **Output**: Either a clarifying question OR proceeds to research brief
- **Config**: Can be disabled with `allow_clarification=False`
- **Tools**: ClarifyWithUser structured output

#### 2. **Research Brief Writer** (`write_research_brief`)
- **Purpose**: Transforms user messages into a focused research brief
- **Input**: User question and context
- **Output**: Structured research brief with clear objectives
- **Model**: Research model (default: gpt-4.1)
- **Tools**: ResearchQuestion structured output

#### 3. **Research Supervisor Subgraph** (`supervisor_subgraph`)
Contains two specialized agents:

##### 3a. **Supervisor** (`supervisor`)
- **Purpose**: Lead researcher that plans research strategy and delegates tasks
- **Input**: Research brief
- **Output**: Research delegation commands
- **Model**: Research model (default: gpt-4.1)
- **Tools**:
  - `ConductResearch` - Delegates research to sub-agents
  - `ResearchComplete` - Signals research phase completion
  - `think_tool` - Strategic reflection and planning
- **Max Iterations**: Configurable (default: 6)

##### 3b. **Supervisor Tools** (`supervisor_tools`)
- **Purpose**: Executes supervisor's tool calls and manages researcher delegation
- **Input**: Supervisor's tool calls
- **Output**: Research findings from sub-agents OR completion signal
- **Concurrency**: Manages parallel execution of multiple researchers
- **Max Concurrent**: Configurable (default: 5 researchers)

#### 4. **Researcher Subgraph** (`researcher_subgraph`)
Contains three specialized agents:

##### 4a. **Researcher** (`researcher`)
- **Purpose**: Individual researcher conducting focused research on specific topics
- **Input**: Research topic from supervisor
- **Output**: Tool calls for information gathering
- **Model**: Research model (default: gpt-4.1)
- **Tools**:
  - `tavily_search` - Web search (default)
  - `openai_web_search` - OpenAI native search
  - `anthropic_web_search` - Anthropic native search
  - `search_opportunities` - Query UrbanZero investment database
  - `get_database_schema` - Explore database structure
  - `query_esg_metrics` - Query sustainability data
  - `execute_readonly_query` - Custom SQL queries
  - `get_opportunity_details` - Get specific investment details
  - `think_tool` - Strategic reflection
  - MCP tools (configurable)
- **Max Tool Calls**: Configurable (default: 10 iterations)

##### 4b. **Researcher Tools** (`researcher_tools`)
- **Purpose**: Executes researcher's tool calls safely
- **Input**: Tool calls from researcher
- **Output**: Tool execution results
- **Safety**: Handles errors gracefully with `execute_tool_safely`
- **Parallelization**: Executes multiple tool calls concurrently

##### 4c. **Research Compressor** (`compress_research`)
- **Purpose**: Synthesizes and compresses research findings into concise summaries
- **Input**: All researcher messages and tool outputs
- **Output**: Compressed research summary + raw notes
- **Model**: Compression model (default: gpt-4.1)
- **Retry Logic**: Handles token limit errors by removing older messages

#### 5. **Final Report Generator** (`final_report_generation`)
- **Purpose**: Creates comprehensive final research report from all findings
- **Input**: Research brief, all compressed research, user context
- **Output**: Final formatted research report
- **Model**: Final report model (default: gpt-4.1)
- **Max Tokens**: Configurable (default: 10,000)
- **Retry Logic**: Progressive truncation if token limits exceeded

---

## 🔧 Supporting Tools & Utilities

### PostgreSQL Database Tools (Custom Integration)
Located in: `src/open_deep_research/postgres_tools.py`

1. **search_opportunities** - Search investment opportunities by location, ROI, risk, ESG
2. **get_opportunity_details** - Get full details for a specific opportunity
3. **query_esg_metrics** - Query ESG and sustainability data
4. **get_database_schema** - Explore database tables and columns
5. **execute_readonly_query** - Execute custom SELECT queries safely

### Search Tools (Configurable)
- **Tavily API** (default) - Web search
- **OpenAI Native Search** - GPT-4 with web search
- **Anthropic Native Search** - Claude with web search
- **MCP Tools** - Model Context Protocol integrations
- **DuckDuckGo** - Alternative search
- **Exa** - Semantic search

### Observability & Monitoring
- **Langfuse Integration** - Full trace tracking
- **LangSmith** - Alternative tracing (disabled by default)
- **Database Storage** - All results saved to PostgreSQL

---

## 📊 Agent Workflow Visualization

```
User Query
    ↓
[Clarification Agent] ─→ Needs clarification? ─→ Ask user ─→ END
    ↓ No clarification needed
[Research Brief Writer] ─→ Create structured research brief
    ↓
[Supervisor] ─→ Plan research strategy
    ↓
[Supervisor Tools] ─→ Delegate to N researchers in parallel
    ↓
┌─────────────────────────────────────────┐
│ Researcher 1  Researcher 2  Researcher 3│ (Parallel execution)
│      ↓              ↓              ↓    │
│ [Researcher]   [Researcher]   [Researcher]│
│      ↓              ↓              ↓    │
│ [Tools]        [Tools]        [Tools]   │
│   - Web         - Database     - MCP    │
│   - Search      - SQL          - Custom │
│      ↓              ↓              ↓    │
│ [Compress]     [Compress]     [Compress]│
└─────────────────────────────────────────┘
    ↓                ↓                ↓
[Supervisor] ─→ Review findings ─→ Need more research?
    │                                  ↓ Yes
    │                           Delegate more tasks
    │                                  ↓ No
    ↓                                  ↓
[Final Report Generator] ←─────────────┘
    ↓
Final Research Report
    ↓
[Save to Database] service20_investment_opportunities
    ↓
[Langfuse Trace] Complete
```

---

## 🎯 Key Features

### 1. Multi-Model Support
- OpenAI (GPT-4.1, GPT-5)
- Anthropic (Claude Sonnet 4)
- Google (Gemini)
- Groq
- DeepSeek
- Local models via Ollama

### 2. Database Integration
- Direct PostgreSQL access via asyncpg
- 5 specialized database tools
- Read-only safety controls
- Connection pooling
- SSL/TLS encryption

### 3. Parallel Research
- Configurable concurrency (default: 5 parallel researchers)
- Automatic load balancing
- Error handling and retry logic

### 4. Cost Optimization
- Multiple model tiers (nano, mini, standard)
- Token limit management
- Progressive compression
- Configurable iteration limits

### 5. Observability
- Full Langfuse tracing
- Tool usage tracking (database vs web)
- Performance metrics
- Cost tracking

### 6. Persistence
- Automatic database storage
- Query history
- Report versioning
- Metadata tracking (JSONB)

---

## 📁 File Structure

```
open-deep-research/
├── src/open_deep_research/
│   ├── deep_researcher.py      # Main agent graph (9 nodes)
│   ├── configuration.py        # Config management
│   ├── state.py               # State definitions
│   ├── prompts.py             # System prompts
│   ├── utils.py               # Helper functions
│   └── postgres_tools.py      # Database tools (5 tools)
├── tests/
│   ├── run_evaluate.py        # Evaluation script
│   └── evaluators.py          # Evaluation metrics
├── test_researcher_with_langfuse.py  # Test with tracing
├── create_research_table.py   # Database setup
├── view_research_results.py   # Results viewer
├── DATABASE_INTEGRATION.md    # Integration docs
├── .env                       # Environment config
└── README.md                  # Project overview
```

---

## 🚀 Usage Examples

### Basic Research
```bash
python test_researcher_with_langfuse.py "What are the best low-risk investments in London?"
```

### Database-Specific Research
```bash
python test_researcher_with_langfuse.py "What investment opportunities do we have in our database with ESG scores above 80?"
```

### View Saved Results
```bash
python view_research_results.py
```

---

## 🔗 Integration Points

### Inputs
- User queries (text)
- Configuration parameters
- Database credentials
- API keys (OpenAI, Tavily, etc.)

### Outputs
- Comprehensive research reports (Markdown)
- Database records (`service20_investment_opportunities`)
- Langfuse traces
- Tool usage statistics

### External Systems
- **PostgreSQL**: UrbanZero database (urbanzero-db)
- **Langfuse**: Observability platform (cloud.langfuse.com)
- **Tavily**: Web search API
- **OpenAI**: LLM provider
- **LangGraph Studio**: Development UI (optional)

---

## 💰 Cost Estimates

Based on Deep Research Bench evaluation:

| Configuration | Cost per 100 queries | Tokens | RACE Score |
|--------------|---------------------|---------|-----------|
| GPT-5 | ~$200+ | 204M | 0.4943 |
| GPT-4.1 (default) | $45-90 | 58-207M | 0.4309-0.4344 |
| Claude Sonnet 4 | ~$187 | 138M | 0.4401 |

Single query costs: **$0.45 - $2.00** depending on complexity and model selection.

---

## 🎓 Summary

**Open Deep Research** is a production-ready, multi-agent deep research system that combines:
- **9 specialized agent nodes** working in coordinated workflows
- **Direct PostgreSQL integration** for accessing your investment database
- **Parallel execution** of up to 5 concurrent researchers
- **Full observability** through Langfuse tracing
- **Automatic persistence** to PostgreSQL
- **PhD-level research quality** (ranked #6 on Deep Research Bench)

The system is fully configured for your UrbanZero database and ready to conduct research on investment opportunities, ESG metrics, and sustainability data!
