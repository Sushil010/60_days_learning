import os, json, random, time, hashlib, uuid
from groq import Groq, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from dotenv import load_dotenv
from config import GENERAL_PROMPT, STRICT_PROMPT
from models import ProfileExtractor 

load_dotenv()
api_key = os.getenv("api")
if not api_key: raise ValueError("Missing API key")

client = Groq(api_key=api_key)
model = "llama-3.3-70b-versatile"

INPUT_PRICE = 0.59
OUTPUT_PRICE = 0.79

class TraceExtractEngine:
    def __init__(self, use_strict_mode: bool = False):
        self.use_strict_mode = use_strict_mode
        self.system_prompt = STRICT_PROMPT if use_strict_mode else GENERAL_PROMPT
        self.prompt_hash = self._get_prompt_hash(self.system_prompt)

    def _get_prompt_hash(self, prompt: str) -> str:
        return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]

    def _validate_schema(self, raw_text: str):
        try:
            clean_text = raw_text.replace("```json", "").replace("```", "").strip()
            json_dict = json.loads(clean_text)
            validated = ProfileExtractor.model_validate(json_dict)
            return {"status": "success", "data": validated.model_dump()}
        except json.JSONDecodeError as e:
            return {"status": "json_error", "error": str(e)[:50]}
        except Exception as e:
            return {"status": "schema_error", "error": str(e)[:50]}

    def _calculate_cost(self, response):
        usage = response.usage
        cost = (
            (usage.prompt_tokens / 1_000_000) * INPUT_PRICE +
            (usage.completion_tokens / 1_000_000) * OUTPUT_PRICE
        )
        return {
            "total_tokens": usage.total_tokens,
            "cost_usd": round(cost, 6)
        }

    def extract(self, messy_text: str, max_retries: int = 3):
        trace_id = str(uuid.uuid4())[:8]
        start_time = time.time()

        for attempt in range(max_retries):
            try:
                response = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": messy_text}
                    ],
                    response_format={"type": "json_object"} if self.use_strict_mode else None
                )
                
                raw_content = response.choices[0].message.content
                validation = self._validate_schema(raw_content)
                costs = self._calculate_cost(response)
                
                return {
                    "trace_id": trace_id,
                    "status": validation["status"],
                    "data": validation.get("data"),
                    "error": validation.get("error"),
                    "metrics": costs,
                    "prompt_hash": self.prompt_hash,
                    "latency_ms": round((time.time() - start_time) * 1000, 2)
                }

            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                error_type = "transient"
            except APIStatusError as e:
                if e.status_code >= 500:
                    error_type = "transient"
                else:
                    return {"trace_id": trace_id, "status": "permanent_error", "error": str(e)}
            except Exception as e:
                return {"trace_id": trace_id, "status": "unexpected_error", "error": str(e)}

            
            if attempt == max_retries - 1:
                return {"trace_id": trace_id, "status": "retry_exhausted", "error": error_type}
            
            delay = 0.5 * (2 ** attempt) + random.uniform(0, 0.5)
            print(f"Retry {attempt + 1}/{max_retries} in {delay:.2f}s")
            time.sleep(delay)

if __name__ == "__main__":
    messy_resume = """
    Hi, I'm John Doe. I have been working as a Senior Data Scientist for about 7 years. 
    I love Python, SQL, and AWS. I also know some Docker.
    """

    print("--- Testing Strict Mode ---")
    engine_strict = TraceExtractEngine(use_strict_mode=True)
    result_strict = engine_strict.extract(messy_resume)
    print(json.dumps(result_strict, indent=2))

    print("\n--- Testing General Mode ---")
    engine_general = TraceExtractEngine(use_strict_mode=False)
    result_general = engine_general.extract(messy_resume)
    print(json.dumps(result_general, indent=2))