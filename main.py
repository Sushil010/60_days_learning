import os,json
from groq import Groq
from dotenv import load_dotenv

load_dotenv()



tools=[
    {
        "type":"function",
        "function":{
            "name":"delete_database",
            "description":"Delete the entire database from the server",
            "parameters":{
                "type":"object",
                "properties":{
                    "dbname":{
                        "type":"string",
                        "description":"The name of the database that needs to be deleted, e.g 'customer','employee_db'"
                    }
                },
                "required":["dbname"]
            }
        }
    },
    
    {
        "type":"function",
        "function":{
            "name":"send_email",
            "description":"send email to the designated mail address",
            "parameters":{
                "type":"object",
                "properties":{
                    "email_address":{
                        "type":"string",
                        "description":"The name of the email address that users want to send, e.g 'john@gmail.com','adam@gmail.com'"
                    }
                },
                "required":["email_address"]
            }
        }
    },
]

SENSETIVE_TOOLS=["delete_database","send_email"]
class HumanInLoop:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))


    def delete_database(self,dbname):
        return (f"Database {dbname} has been successfully deleted")

    def send_email(self,email_address):
        return (f"Email has been sent to {email_address}")


    def human_loop(self,user_query):    
        messages=[
            {
                "role":"user",
                "content":user_query
            }
        ]

        while True:
            response=self.client.chat.completions.create(
                messages=messages,
                model="llama-3.3-70b-versatile",
                tools=tools,
                tool_choice="auto"
            )

            assistant_message=response.choices[0].message
            messages.append(assistant_message)
            
            if not assistant_message.tool_calls:
                return assistant_message.content
            
            for tool_call in assistant_message.tool_calls:
                tool_name=tool_call.function.name

                try:
                    tool_args=json.loads(tool_call.function.arguments)
                except:
                    tool_args={}

                print(f"\nAGENT REQUEST: {tool_name} with arguments: {tool_args}")


                if tool_name in SENSETIVE_TOOLS:
                    approval=input("Do you approve this action? (y/n): ")
                    if approval.lower()!='y':
                        tool_result="Action blocked by user"
                        print("Action blocked")
                    else:
                        print(" Action approved. Executing...")
                        if tool_name == "delete_database":
                            tool_result = self.delete_database(**tool_args)
                        elif tool_name == "send_email":
                            tool_result = self.send_email(**tool_args)
                        else:
                            tool_result = "Unknown function"
                else:
                    tool_result = "Unknown function"

                messages.append(
                    {
                        "role":"tool",
                        "tool_call_id":tool_call.id,
                        "name":tool_name,
                        "content":str(tool_result)
                    }
                )
                

if __name__=="__main__":
    hl=HumanInLoop()
    result=hl.human_loop("send mail to this email row@gmail.com and delete the production database named teacher_db")
    print(result)