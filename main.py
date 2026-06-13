import os, time, asyncio
from groq import AsyncGroq
from dotenv import load_dotenv

load_dotenv()
client = AsyncGroq(api_key=os.getenv("api"))

async def ask_question(question: str):
    response = await client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": question}]
    )
    return response.choices[0].message.content

async def main():
    questions = [
        "Define Machine Learning",
        "Biasness in a model",
        "Overfitting concept"
    ]
    
    print("Starting Async Requests")
    start_time = time.time()
    
   
    tasks = [ask_question(q) for q in questions]
    answers = await asyncio.gather(*tasks)
    
    end_time = time.time()
    print(f"Finished in {end_time - start_time:.2f} seconds!")
    for ans in answers:
        print(f"- {ans}")

if __name__ == "__main__":
    asyncio.run(main())