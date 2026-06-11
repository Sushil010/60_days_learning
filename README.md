### Day 1: Basic LLM Integration with Validation
**File:** `day_1main.py`

**Main Purpose:** Generate JSON profiles from LLM and validate them

**Key Code Parts:**
- `Validator` class: Pydantic model defining profile schema (name, role, experience, skills)
- `llm_call()`: Calls Groq API with system prompt that enforces JSON-only responses
- `json_validate()`: Parses JSON response and validates against schema
- `chat()`: Runs 50 test iterations with different profile prompts

**What It Does:** Makes LLM API calls to generate user profiles, validates the JSON structure, and tracks success/failure status

---

### Day 2: Error Handling & Retry Logic
**File:** `day_2main.py`

**Main Purpose:** Add robust error handling with exponential backoff retries

**Key Code Parts:**
- Imports error types: `RateLimitError`, `APITimeoutError`, `APIConnectionError`, `APIStatusError`
- `llm_call()` with retry loop: Implements exponential backoff (base_delay * 2^retry) + random jitter
- Distinguishes between transient errors (retryable) and permanent errors (not retryable)
- `max_retry` parameter: Default 3 attempts

**What It Does:** Same as Day 1 but with resilient error handling - automatically retries failed calls with increasing delays

---

### Day 3: A/B Testing (Strict vs Freeform)
**File:** `day_3main.py`

**Main Purpose:** Compare two JSON response strategies

**Key Code Parts:**
- `strict_call()`: Uses `response_format={"type": "json_object"}` to force LLM to return valid JSON
- `freeform_call()`: Allows freeform response, then cleans JSON manually with `clean_json_response()` (removes markdown blocks, extracts JSON)
- `run_ab_test()`: Runs 20 iterations comparing both methods, counts success rates

**What It Does:** Tests which approach (strict JSON mode vs manual cleanup) has higher success rate

---

### Day 4: Performance Benchmarking & Cost Analysis
**File:** `day4_main.py`

**Main Purpose:** Measure API performance and calculate costs

**Key Code Parts:**
- Token tracking: Captures `prompt_tokens`, `completion_tokens`, `total_tokens`
- Cost calculation: Uses API pricing (INPUT: $0.59/million, OUTPUT: $0.79/million)
- Latency tracking: Measures response time in milliseconds
- `run_benchmark()`: Runs 30 calls, generates summary table with tokens, cost, latency per call
- Summary stats: Total cost, average tokens per call, average cost per call

**What It Does:** Benchmarks API performance and provides cost analysis - useful for understanding API expenses and performance metrics

---

### Day 5: Multi-Version Prompt Comparison
**File:** `day5_main.py`

**Main Purpose:** Compare different prompt versions and their impact on token usage/latency

**Key Code Parts:**
- `prompt_hash()`: Creates 12-character hash of system prompts for easy identification
- `llm_version_call()`: Makes API call with a system prompt and user query, tracks performance metrics
- `run_multi_version()`: Compares two prompt versions (concise vs detailed) with 10 iterations each
- Tracks: Prompt hash, tokens used, latency per call

**What It Does:** Tests how different system prompts affect API response efficiency - shows token count and latency differences between concise vs detailed instruction sets

---

### Day 6: Event Logging & Tracing
**File:** `day_6main.py`

**Main Purpose:** Implement structured event logging for tracking API calls and pipeline execution

**Key Code Parts:**
- `event_log()`: Logs events to both stdout (JSON format) and `event_log.jsonl` file
- Logs include: `timestamp`, `status`, `details`, `method`, `trace_id`
- `prompt_call()`: Example function demonstrating trace ID generation and multi-step event logging
- Persistent logging: Events appended to JSONL file for later analysis

**What It Does:** Creates an audit trail of all API interactions - useful for debugging, monitoring, and analyzing API behavior patterns

---

### Day 9: Semantic Caching with ChromaDB
**File:** `day9_main.py`

**Main Purpose:** Implement semantic caching to avoid redundant API calls for similar queries

**Key Code Parts:**
- `chromadb.PersistentClient`: Initializes ChromaDB for persistent semantic cache storage
- `collection`: Get-or-create collection named "semantic_cache" to store query-answer pairs
- `THRESHOLD = 0.15`: Similarity distance threshold to determine cache hits (lower distance = more similar)
- `get_answer()`: Queries cached responses using semantic similarity; returns cached answer if distance < threshold, otherwise calls Groq API
- Cache storage: Stores query answer and metadata (original query) for future semantic matching

**What It Does:** Uses ChromaDB for semantic similarity search to cache LLM responses - detects similar queries and returns cached answers without API calls, reducing costs and latency while maintaining response quality

---

### Day 10: Rate Limiting with Token Bucket Algorithm
**File:** `day10_main.py`

**Main Purpose:** Implement rate limiting to prevent API throttling and resource exhaustion

**Key Code Parts:**
- `TokenBucket` class: Manages rate limiting using token bucket algorithm
  - `max_tokens`: Maximum tokens available (capacity)
  - `token_rate`: Rate at which tokens are refilled (tokens per second)
  - `refill()`: Calculates new tokens based on elapsed time
  - `consume()`: Checks if token available before allowing request
- Test loop: Simulates 7 requests with 0.2s intervals to demonstrate rate limiting behavior

**What It Does:** Implements token bucket algorithm for rate limiting - allows controlled request flow by refilling tokens at a fixed rate and consuming one per request, blocking requests when no tokens available

---

### Day 11: Input Validation & Security (InputGuard)
**File:** `day11_main.py`

**Main Purpose:** Sanitize and validate user inputs to prevent injection attacks and malicious prompts

**Key Code Parts:**
- `InputGuard` class: Implements multi-layer input validation
  - `max_length`: Maximum allowed input length (default 2000 chars)
  - `pattern`: List of regex patterns to detect malicious prompts:
    - "ignore previous instructions"
    - "ignore all previous"
    - "system prompt"
    - "dan mode"
    - "jailbreak"
  - `sanitize()`: Validates input against length and pattern rules
- Response object: Returns `{"status": "blocked"|"safe", "reason": "...", "cleaned_input": "..."}`
- Test cases: Demonstrates blocking of prompt injection attempts and oversized inputs

**What It Does:** Protects LLM applications from prompt injection attacks and malicious inputs - validates input length, detects jailbreak patterns, and blocks suspicious requests before they reach the API

---

## Projects

### Week 1: Advanced Profile Extraction Engine
**Directory:** `projects/week1/`

**Main Purpose:** Production-ready data extraction pipeline with schema validation, cost tracking, and error handling

**Files:**
- `main.py`: Main extraction engine with `TraceExtractEngine` class
- `config.py`: System prompts (GENERAL_PROMPT and STRICT_PROMPT)
- `models.py`: Pydantic schema for ProfileExtractor

**Key Features:**
- **TraceExtractEngine class**: 
  - Configurable strict/freeform modes
  - Automatic schema validation using Pydantic
  - Cost calculation per API call
  - Request hashing for prompt identification
  - Retry logic with transient/permanent error distinction
  
- **ProfileExtractor schema**: Validates extracted data with fields:
  - `name`: String
  - `role`: String  
  - `experience_years`: Integer
  - `skills`: List of strings

- **Response tracking**: Returns comprehensive result object with:
  - `trace_id`: Unique request identifier
  - `status`: success/json_error/schema_error/transient_error/permanent_error
  - `data`: Validated profile object
  - `error`: Error details if applicable
  - `metrics`: Token count and cost in USD
  - `prompt_hash`: 12-char hash of system prompt
  - `latency_ms`: Response time in milliseconds

**What It Does:** Takes messy text input, extracts structured profile data via Groq API, validates against schema, tracks costs and performance, and handles errors gracefully

---

## Requirements
- Groq API key (stored in `.env` as `api`)
- Dependencies in `requirements.txt`

## Key Dependencies
- `groq`: Groq API client
- `pydantic`: Schema validation
- `python-dotenv`: Environment variable management