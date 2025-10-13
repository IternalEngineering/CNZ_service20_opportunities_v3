# Funding Research Agent - Architecture

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Funding Research Agent                        │
│                                                                   │
│  Input: Project Description, Location, Sectors, Funding Types   │
│  Output: Structured Funder Metadata + Comprehensive Report      │
└─────────────────────────────────────────────────────────────────┘
```

## Workflow Diagram

```
                           START
                             |
                             v
                    ┌─────────────────┐
                    │   Initialize    │
                    │   Research      │
                    └────────┬────────┘
                             │
                             v
      ┌──────────────────────────────────────────────┐
      │          RESEARCH LEVEL LOOP                  │
      │  (Regional → National → Global)              │
      │                                               │
      │  ┌─────────────────────────────┐            │
      │  │  1. Generate Search Queries │            │
      │  │     (5-8 targeted queries)  │            │
      │  └────────────┬────────────────┘            │
      │               │                              │
      │               v                              │
      │  ┌─────────────────────────────┐            │
      │  │  2. Execute Web Searches    │            │
      │  │     (Parallel queries via   │            │
      │  │      Tavily/Exa/DuckDuckGo) │            │
      │  └────────────┬────────────────┘            │
      │               │                              │
      │               v                              │
      │  ┌─────────────────────────────┐            │
      │  │  3. Extract Funders         │            │
      │  │     (Parse & structure data │            │
      │  │      into FunderMetadata)   │            │
      │  └────────────┬────────────────┘            │
      │               │                              │
      │               v                              │
      │  ┌─────────────────────────────┐            │
      │  │  4. Advance Research Level  │            │
      │  │     (Regional → National    │            │
      │  │      → Global → Complete)   │            │
      │  └────────────┬────────────────┘            │
      │               │                              │
      └───────────────┼──────────────────────────────┘
                      │
                      v
              ┌───────────────┐
              │  All levels   │
              │  complete?    │
              └───┬───────┬───┘
                  │ No    │ Yes
                  │       │
                  └───┐   └──────┐
                      │          │
                      v          v
                   (Loop)   ┌─────────────────────┐
                            │ 5. Generate Final   │
                            │    Report           │
                            │    (Markdown with   │
                            │     all findings)   │
                            └──────────┬──────────┘
                                       │
                                       v
                                     END
```

## Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      User Interface                          │
│  (LangGraph Studio UI / Python API / CLI)                   │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                  Configuration Layer                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐     │
│  │ Environment  │  │   Config     │  │  LangGraph   │     │
│  │  Variables   │  │   Object     │  │  Studio UI   │     │
│  └──────────────┘  └──────────────┘  └──────────────┘     │
└────────────────────────┬────────────────────────────────────┘
                         │
                         v
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  Graph Nodes (Async Functions)                        │ │
│  │  • initialize_research                                 │ │
│  │  • generate_search_queries                            │ │
│  │  • execute_searches                                   │ │
│  │  • extract_funders                                    │ │
│  │  • advance_research_level                             │ │
│  │  • generate_final_report                              │ │
│  └───────────────────────────────────────────────────────┘ │
│  ┌───────────────────────────────────────────────────────┐ │
│  │  State Management (ResearchState)                     │ │
│  │  • Project details                                     │ │
│  │  • Current research level                             │ │
│  │  • Accumulated funders (regional/national/global)     │ │
│  │  • Search queries and results                         │ │
│  │  • Final report                                       │ │
│  └───────────────────────────────────────────────────────┘ │
└────────────────────────┬────────────────────────────────────┘
                         │
            ┌────────────┴────────────┐
            │                         │
            v                         v
┌──────────────────────┐  ┌──────────────────────┐
│   LLM Providers      │  │   Search APIs        │
│  ┌────────────────┐  │  │  ┌────────────────┐  │
│  │  OpenAI        │  │  │  │  Tavily        │  │
│  │  Anthropic     │  │  │  │  Exa           │  │
│  │  Google        │  │  │  │  DuckDuckGo    │  │
│  │  Groq          │  │  │  └────────────────┘  │
│  └────────────────┘  │  └──────────────────────┘
└──────────────────────┘
```

## Data Flow

```
User Input                    LLM Processing                Search & Extract
───────────────────────────────────────────────────────────────────────────

┌─────────────────┐
│ Project Details │
│ • Description   │
│ • Location      │
│ • Sectors       │
│ • Funding Types │
└────────┬────────┘
         │
         v
┌────────────────────────┐
│  Generate Queries      │─────> LLM: "Create 5-8 targeted
│  (Per Level)           │       search queries for regional
└────────┬───────────────┘       funding in Scotland..."
         │
         │ ["regional sustainability grants Scotland",
         │  "Scottish green energy investment schemes",
         v  "local authority net zero funding", ...]
         │
┌────────────────────────┐
│  Execute Searches      │─────> Web APIs: Parallel searches
│  (Parallel)            │       Tavily/Exa/DuckDuckGo
└────────┬───────────────┘       Returns: URLs, titles, content
         │
         │ [Search Result 1, Result 2, Result 3, ...]
         v
         │
┌────────────────────────┐
│  Extract Funders       │─────> LLM: "Extract funding opportunities
│  (Structured)          │       from these results with complete
└────────┬───────────────┘       metadata: name, org, award..."
         │
         │ [FunderMetadata(name=..., org=..., award=...), ...]
         v
         │
┌────────────────────────┐
│  Store by Level        │
│  • Regional Funders    │
│  • National Funders    │
│  • Global Funders      │
└────────┬───────────────┘
         │
         v (After all levels complete)
         │
┌────────────────────────┐
│  Generate Report       │─────> LLM: "Create comprehensive report
│  (Comprehensive)       │       with executive summary, funder
└────────┬───────────────┘       details, analysis, strategy..."
         │
         v
┌────────────────────────┐
│  Final Output          │
│  • Markdown Report     │
│  • Structured Data     │
│  • Funder Count        │
└────────────────────────┘
```

## State Management

```
ResearchState
├── messages: list[Message]              # Conversation history
├── project_description: str             # User's project details
├── project_location: str                # Geographic location
├── project_sectors: list[str]           # Relevant sectors
├── funding_types: list[str]             # Types of funding sought
│
├── current_level: str                   # "regional"|"national"|"global"
│   └─> Controls workflow progression
│
├── regional_funders: list[FunderMetadata]
├── national_funders: list[FunderMetadata]
├── global_funders: list[FunderMetadata]
│   └─> Accumulated results by level
│
├── search_queries: list[str]            # Current level queries
├── search_results: list[dict]           # Current level results
│   └─> Temporary per-level storage
│
├── final_report: str                    # Generated markdown report
└── total_funders_found: int            # Total across all levels
```

## Module Dependencies

```
graph.py
├── imports: state, configuration, prompts, utils.search
├── defines: workflow nodes and edges
└── exports: compiled graph

state.py
├── imports: pydantic, langgraph
├── defines: ResearchState, FunderMetadata
└── exports: type definitions

configuration.py
├── imports: pydantic, langchain providers
├── defines: Configuration, SearchAPI enum
└── exports: configuration class with model factory

prompts.py
├── defines: all LLM prompt templates
└── exports: prompt strings

utils/search.py
├── imports: tavily, duckduckgo, exa, asyncio
├── defines: search functions for each API
└── exports: async search functions
```

## Execution Flow Example

For a solar farm project in Scotland:

```
1. INITIALIZE
   └─> Set current_level = "regional"

2. REGIONAL RESEARCH
   ├─> Generate queries [
   │     "Scottish Enterprise renewable energy funding",
   │     "Scotland regional development fund solar",
   │     "local authority green investment Scotland",
   │     ... (5-8 total)
   │   ]
   ├─> Execute searches (parallel)
   │   └─> Returns ~50-80 search results
   ├─> Extract funders
   │   └─> Finds 8 regional opportunities
   └─> Advance to "national"

3. NATIONAL RESEARCH
   ├─> Generate queries [
   │     "UK government solar farm grants",
   │     "Innovate UK renewable energy funding",
   │     "British Business Bank green finance",
   │     ... (5-8 total)
   │   ]
   ├─> Execute searches (parallel)
   │   └─> Returns ~50-80 search results
   ├─> Extract funders
   │   └─> Finds 10 national opportunities
   └─> Advance to "global"

4. GLOBAL RESEARCH
   ├─> Generate queries [
   │     "European Union renewable energy grants",
   │     "World Bank climate finance solar",
   │     "international green climate fund",
   │     ... (5-8 total)
   │   ]
   ├─> Execute searches (parallel)
   │   └─> Returns ~50-80 search results
   ├─> Extract funders
   │   └─> Finds 5 global opportunities
   └─> Advance to "completed"

5. GENERATE REPORT
   ├─> Compile all funders (8 + 10 + 5 = 23)
   ├─> Create sections:
   │   • Executive summary
   │   • Regional opportunities (detailed)
   │   • National opportunities (detailed)
   │   • Global opportunities (detailed)
   │   • Sector analysis
   │   • Funding type analysis
   │   • Application strategy
   │   • Quick reference table
   └─> Return markdown report

6. OUTPUT
   └─> {
         "total_funders_found": 23,
         "regional_funders": [...],
         "national_funders": [...],
         "global_funders": [...],
         "final_report": "# Funding Research Report\n..."
       }
```

## Performance Characteristics

```
┌─────────────────────────────────────────────────────┐
│ Performance Metrics (Typical)                        │
├─────────────────────────────────────────────────────┤
│ Total Execution Time:     6-15 minutes              │
│   • Per level:            2-5 minutes               │
│   • 3 levels total                                  │
│                                                      │
│ Search Operations:        15-24 queries             │
│   • Per level:            5-8 queries               │
│   • Executed in parallel  (max_concurrent: 3)      │
│                                                      │
│ LLM Calls:                4 per level + 1 final     │
│   • Query generation:     1 call per level          │
│   • Extraction:           1 call per level          │
│   • Report generation:    1 final call              │
│                                                      │
│ Results:                  15-30 funders typical     │
│   • Regional:             5-10 funders              │
│   • National:             8-15 funders              │
│   • Global:               2-8 funders               │
└─────────────────────────────────────────────────────┘
```

## Error Handling

```
Each node includes error handling:

┌─────────────────────────────────┐
│ Search Failed                    │
├─────────────────────────────────┤
│ • Try alternate search API      │
│ • Return empty results          │
│ • Continue workflow             │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ LLM Parsing Failed              │
├─────────────────────────────────┤
│ • Log error                     │
│ • Use fallback queries/data     │
│ • Continue with partial results │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│ No Results Found                │
├─────────────────────────────────┤
│ • Note in state                 │
│ • Continue to next level        │
│ • Mention in final report       │
└─────────────────────────────────┘
```

## Extensibility Points

```
1. New Search API
   └─> Add function to utils/search.py
   └─> Update SearchAPI enum
   └─> Add conditional in execute_searches()

2. Additional Metadata
   └─> Update FunderMetadata in state.py
   └─> Update extraction prompt
   └─> Update report generation

3. Custom Research Levels
   └─> Add level to state type
   └─> Add funder list to state
   └─> Update workflow conditions

4. Post-Processing
   └─> Add node after extract_funders
   └─> Filter, rank, or score funders
   └─> Update state with processed data

5. External Integration
   └─> Add node for database storage
   └─> Add node for API calls
   └─> Add node for notifications
```

## Deployment Architecture

```
┌────────────────────────────────────────────────┐
│          Production Deployment                  │
├────────────────────────────────────────────────┤
│                                                 │
│  ┌─────────────────────────────────────┐      │
│  │  LangGraph Cloud / Self-Hosted      │      │
│  │  • Manages workflow execution       │      │
│  │  • Provides REST API                │      │
│  │  • Handles state persistence        │      │
│  └──────────────┬──────────────────────┘      │
│                 │                               │
│  ┌──────────────v──────────────────────┐      │
│  │  Application Layer                   │      │
│  │  • FastAPI / Flask                   │      │
│  │  • Authentication                    │      │
│  │  • Rate limiting                     │      │
│  │  • Caching                           │      │
│  └──────────────┬──────────────────────┘      │
│                 │                               │
│  ┌──────────────v──────────────────────┐      │
│  │  Frontend                            │      │
│  │  • React / Vue / Svelte              │      │
│  │  • Real-time updates                 │      │
│  │  • Result visualization              │      │
│  └──────────────────────────────────────┘      │
│                                                 │
└────────────────────────────────────────────────┘
```

---

This architecture enables:
- **Scalability**: Parallel searches and async operations
- **Flexibility**: Multi-provider, multi-API support
- **Reliability**: Error handling and fallbacks
- **Extensibility**: Modular design for enhancements
- **Maintainability**: Clear separation of concerns
