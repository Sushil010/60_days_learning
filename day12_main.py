import os,json,uuid
from pydantic import BaseModel
from groq import Groq
from dotenv import load_dotenv

GENERAL_PROMPT = """
You are an expert data extractor. 
Read the messy text provided by the user and extract the following information into a JSON object:
- name (string)
- role (string)
- experience_years (integer, just the number)
- skills (list of strings)

Return ONLY the JSON object. Do not add any conversational text.
"""

load_dotenv()

api_key=os.getenv("api")

if not api_key:
    raise ValueError("Missing API key\n")

else:
    print("API key has been loaded\n")

client=Groq(api_key=api_key)
model="llama-3.3-70b-versatile"

class StreamDate():
    def __init__(self,stream:bool=False):
        self.stream_flow=stream
        
    
    def extract_data(self,user_query):
        trace_id = str(uuid.uuid4())[:8]
        response={
            "model":model,
            "messages":[
                { "role":"system",
                    "content":GENERAL_PROMPT
                },
                {
                    "role":"user",
                    "content":user_query
                }
            ],
        "stream":self.stream_flow
        }

        response = client.chat.completions.create(**response)

        if not self.stream_flow:
            return {
                "id":trace_id,
                "token":response.usage.total_tokens,
                "content":response.choices[0].message.content
            }
        else:
            full_content=""
            token=0
            for chunk in response:

                if chunk.usage:
                    token=chunk.usage.total_tokens

                text=chunk.choices[0].delta.content or ""
                
                full_content+=text
            
                yield text

            
            yield {
                "id":trace_id,
                "token":token,
                "content":full_content
            }



if __name__=="__main__":
    
    sd=StreamDate(stream=True)
    
    messy_resume = "Hi, I'm John Doe. I have been working as a Senior Data Scientist for about 7 years. I love Python, SQL, and AWS."

    print("AI Extracting: ", end="", flush=True)

    for piece in sd.extract_data(messy_resume):
        if isinstance(piece,str):
            print(piece, end="", flush=True)
        else:
            print(f"\n\nDone! Trace ID: {piece['id']} | Tokens: {piece['token']}")





# def get_joke():
#     stream=client.chat.completions.create(
#         model=model,
#         messages=[
#             {
#                 "role":"user",
#                 "content":"Tell me a 2-sentence joke."
#             }
#         ],
#         stream=True
#     )

#     for pieces in stream:
#         text=pieces.choices[0].delta.content or ""
#         print(text,end="",flush=True)

# print("Getting joke")
# get_joke()
# print("done")