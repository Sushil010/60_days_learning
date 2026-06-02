import os,json
from pydantic import BaseModel
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

    def llm_call(self, user_input: str):
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



        # while True:
        #     user_input=input("You: ")
        #     if user_input.lower()=="quit":
        #         break
        #     assistant=self.llm_call(user_input)
        #     print(f"Assistant: {assistant}")


if __name__=="__main__":
    tester=Tester()
    tester.chat()

            

