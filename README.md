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

## Requirements
- Groq API key (stored in `.env` as `api`)
- Dependencies in `requirements.txt`