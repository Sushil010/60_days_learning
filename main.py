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

    def clean_json_response(self, raw_text: str) -> str:
        cleaned = raw_text.replace("```json", "").replace("```", "")
        start = cleaned.find('{')
        end = cleaned.rfind('}')
        if start != -1 and end != -1:
            return cleaned[start:end+1]
        return cleaned.strip()


    def json_validate(self,value:str):
        try:
            json_parser=json.loads(value)
            validator=Validator.model_validate(json_parser)
            return {"status":"success","data":validator.model_dump()}
        except json.JSONDecodeError as e:
            return {"status":"json_error","error":str(e)}
        except Exception as e:
            return {"status" :"schema_error", "error": str(e)}

    def strict_call(self,user_input:str):
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
            ],
            response_format={"type": "json_object"}
        )
        response=response.choices[0].message.content
        print(response)
        return self.json_validate(response)
    
    def freeform_call(self,user_input:str):
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
        response=self.clean_json_response(response)
        print(response)
        return self.json_validate(response)


     
    def run_ab_test(self):
        prompts = [
            "Senior Python Engineer",
            "Junior Data Analyst",
            "DevOps Specialist"
        ]
        # val=self.freeform_call(prompts[0])
        # print(val['status'])

        # print(30*"*")

        # valer=self.strict_call(prompts[0])
        # print(valer['status'])

        
        strict_success = 0
        free_success = 0
        
        for i in range(20):
            prompt = prompts[i % 3]
            
            s_res = self.strict_call(prompt)
            if s_res['status'] == 'success': strict_success += 1
            
            f_res = self.freeform_call(prompt)
            if f_res['status'] == 'success': free_success += 1
            
            print(f"{i+1}: Strict={s_res['status']} | Free={f_res['status']}")

        print(f"\nFinal Score: Strict {strict_success}/20 vs Free {free_success}/20")
            
            


if __name__=="__main__":
    tester=Tester()
    tester.run_ab_test()

            

