import os,json,random,time
from pydantic import BaseModel
from groq import Groq, RateLimitError, APITimeoutError, APIConnectionError, APIStatusError
from dotenv import load_dotenv


load_dotenv()

api_key=os.getenv("api")

if not api_key:
    raise ValueError("Missing API key\n")

else:
    print("API key has been loaded\n")

client=Groq(api_key=api_key)
model="llama-3.3-70b-versatile"

class Validator(BaseModel):
    name:str
    role:str
    experience:int
    skills:list[str]

class Tester():
    def __init__(self):
        pass


    def json_validate(self,value:str):
        try:
            json_parser=json.loads(value)
            validator=Validator.model_validate(json_parser)
            return {"status":"success","data":validator.model_dump()}
        except json.JSONDecodeError as e:
            return {"status":"json_error","error":str(e)}
        except Exception as e:
            return {"status" :"schema_error", "error": str(e)}

    def llm_call(self, user_input: str, max_retry:int=3,base_delay:float=1.0):
        for retry in range(max_retry+1):
            try:
                response=client.chat.completions.create(
                    model=model,
                    messages=[
                        {
                            "role":"system",
                            "content":
                            "Return ONLY a JSON object with these exact fields:\n"
                            "- name: string\n"
                            "- role: string\n"
                            "- experience: integer\n"   
                            "- skills: array of strings\n"
                            "Example: {\"name\": \"Alice\", \"role\": \"Engineer\", \"experience\": 5, \"skills\": [\"Python\", \"AWS\"]}\n"
                            "DO NOT add any other text. ONLY JSON."
                        },
                        {
                            "role":"user",
                            "content":user_input
                        }
                    ]
                )
                response=response.choices[0].message.content
                print(response)
                return self.json_validate(response)
            
            except (RateLimitError, APITimeoutError, APIConnectionError) as e:
                error_type="transient error"
            except APIStatusError as e:
                if e.status_code>=500:
                    error_type="transient_server_error"
                else:
                    return {"status":"permanent error", "error":str(e)}
            if retry==max_retry:
                return {"status":"max_retry_reached","error":error_type}

            delay=base_delay*(2**retry)+random.uniform(0,1)
            print(f"Using specific delay of {delay} in attempt {retry+1}")
            time.sleep(delay)    


    def chat(self):
        prompts=[
            "Generate a profile for a senior Python engineer",  
            "Create a junior data analyst profile",             
            "Profile a DevOps specialist" 
        ]

        for i in range(50):
            prompt=prompts[i % len(prompts)]
            result=self.llm_call(prompt)
            print(f"{i+1}: {result['status']}")


if __name__=="__main__":
    tester=Tester()
    tester.chat()

            

