import os, hashlib,time
from groq import Groq
from dotenv import load_dotenv


load_dotenv()

api_key=os.getenv("api")

if not api_key:
    raise ValueError("Missing API key\n")

else:
    print("API key has been loaded\n")

client=Groq(api_key=api_key)
model="llama-3.3-70b-versatile"

def prompt_hash(prompt:str):
    return hashlib.sha256(prompt.encode("utf-8")).hexdigest()[:12]

def llm_version_call(prompt:str,user_query:str):
    start_time=time.time()
    hased_prompt=prompt_hash(prompt)
    response=client.chat.completions.create(
        model=model,
        messages=[
            {
                "role":"system",
                "content":prompt
            },
            {
                "role":"user",
                "content":user_query
            }
        ]
    )
    return {
        "prompt_hash":hased_prompt,
        "status":"success",
        "tokens":response.usage.total_tokens,
        "latency_ms":round((time.time()-start_time)*1000,2)
    }

def run_multi_version():
    question="Explain machine learning"
    prompt1 = "Act as a concise assistant. Answer in 1 sentence."
    prompt2 = "Act as a detailed assistant. Explain step-by-step with examples."
    results = []
    
    print(f"{'Hash':<14} | {'Tokens':<8} | {'Latency (ms)':<12}")
    print("-" * 40)
    
    # Test V1
    for _ in range(10):
        r = llm_version_call(prompt1,question )
        results.append(r)
        print(f"{r['prompt_hash']:<14} | {r['tokens']:<8} | {r['latency_ms']:<12}")
        
    print("-" * 40)
    # Test V2
    for _ in range(10):
        r = llm_version_call(prompt2, question)
        results.append(r)
        print(f"{r['prompt_hash']:<14} | {r['tokens']:<8} | {r['latency_ms']:<12}")

if __name__=="__main__":
    run_multi_version()