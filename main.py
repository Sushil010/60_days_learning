import os, json, time, csv
from groq import Groq
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("api")
if not api_key: raise ValueError("Missing API key")

client = Groq(api_key=api_key)
model = "llama-3.3-70b-versatile"


INPUT_PRICE_PER_MILLION = 0.59 
OUTPUT_PRICE_PER_MILLION = 0.79

class Tester():
    
    def llm_call(self, user_input: str):
        start_time = time.time()
        
        try:
            response = client.chat.completions.create(
                model=model,
                messages=[
                    {"role": "system", "content": "Act as a Q&A bot. Be concise."},
                    {"role": "user", "content": user_input}
                ]
            )
                       
            latency_ms = round((time.time() - start_time) * 1000, 2)
            
            usage = response.usage
            prompt_tokens = usage.prompt_tokens
            completion_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens
            
            cost_usd = (
                (prompt_tokens / 1_000_000) * INPUT_PRICE_PER_MILLION +
                (completion_tokens / 1_000_000) * OUTPUT_PRICE_PER_MILLION
            )
            
            
            return {
                "status": "success",
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": total_tokens,
                "cost_usd": round(cost_usd, 6),
                "latency_ms": latency_ms,
                "content_snippet": response.choices[0].message.content[:50] 
            }

        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
                "cost_usd": 0,
                "latency_ms": round((time.time() - start_time) * 1000, 2)
            }

    def run_benchmark(self):
        prompts = [
            "Generate a profile for a senior Python engineer",  
            "Create a junior data analyst profile",             
            "Profile a DevOps specialist" 
        ]
        
        results = []
        total_cost = 0
        total_tokens = 0
        
        print(f"{'Call':<5} | {'Tokens':<8} | {'Cost ($)':<10} | {'Latency (ms)':<12}")
        

        for i in range(30): 
            prompt = prompts[i % len(prompts)]
            result = self.llm_call(prompt)
            
            if result['status'] == 'success':
                results.append(result)
                total_cost += result['cost_usd']
                total_tokens += result['total_tokens']
                
                print(f"{i+1:<5}  {result['total_tokens']:<8}  ${result['cost_usd']:<9.6f}  {result['latency_ms']:<12}")
        
        # Summary
        avg_cost = total_cost / len(results) if results else 0
        avg_tokens = total_tokens / len(results) if results else 0
        
        print("-" * 45)
        print(f"TOTAL COST: ${total_cost:.6f}")
        print(f"AVG TOKENS/CALL: {avg_tokens:.0f}")
        print(f"AVG COST/CALL: ${avg_cost:.6f}")

if __name__=="__main__":
    tester = Tester()
    tester.run_benchmark()