import os 
import json 
from dotenv import load_dotenv 
from groq import Groq 
from pydantic import BaseModel ,Field 
from typing import Literal ,List 
from collections import deque 
from datetime import datetime 
import uuid 
import chromadb 

load_dotenv ()




class RiskAssessment (BaseModel ):
    is_risky :bool =Field (description ="True if the action could cause damage")
    risk_level :Literal ["low","medium","high","critical"]=Field (description ="Severity level")
    reason :str =Field (description ="Why it's risky")
    suggested_options :List [str ]=Field (description ="Options for the user to choose from")




class RiskAssessor :
    def __init__ (self ):
        self .client =Groq (api_key =os .getenv ('api'))

    def assess_risk (self ,action_description :str ,context :str )->RiskAssessment :
        """Uses LLM to evaluate if an action is risky."""
        schema_str =json .dumps (RiskAssessment .model_json_schema (),indent =2 )

        messages =[
        {
        "role":"system",
        "content":f"""You are a risk assessment AI. Your job is to evaluate if a user's requested action is risky.

Consider these risk factors:
- Modifying code or configuration files
- Deleting or overwriting data
- Accessing sensitive information (passwords, API keys, database credentials)
- Sending emails or messages on behalf of the user
- Making irreversible changes

Return a JSON object matching this schema:
{schema_str }

If the action is safe (like explaining text, summarizing, or answering questions), set is_risky=False.
If the action could cause damage, set is_risky=True and provide clear options for the user."""
        },
        {
        "role":"user",
        "content":f"Action requested: {action_description }\n\nContext (highlighted text):\n{context }"
        }
        ]

        response =self .client .chat .completions .create (
        messages =messages ,
        model ="llama-3.3-70b-versatile",
        response_format ={"type":"json_object"}
        )

        raw_json =response .choices [0 ].message .content 
        return RiskAssessment .model_validate_json (raw_json )




class HumanInTheLoop :
    @staticmethod 
    def ask_confirmation (question :str ,options :List [str ])->str :
        """Pauses execution and asks user to choose from options."""
        print ("\n"+"="*60 )
        print ("⚠️  HUMAN INPUT REQUIRED")
        print ("="*60 )
        print (f"\n{question }\n")

        for i ,option in enumerate (options ,1 ):
            print (f"  {i }. {option }")

        print (f"\n  {len (options )+1 }. Cancel")

        while True :
            try :
                choice =input (f"\nYour choice (1-{len (options )+1 }): ").strip ()
                choice_num =int (choice )

                if 1 <=choice_num <=len (options ):
                    return options [choice_num -1 ]
                elif choice_num ==len (options )+1 :
                    return "Cancel"
                else :
                    print (f"❌ Invalid choice. Please enter 1-{len (options )+1 }")
            except ValueError :
                print ("❌ Please enter a number")
            except KeyboardInterrupt :
                print ("\n\n🛑 User cancelled operation")
                return "Cancel"

    @staticmethod 
    def ask_yes_no (question :str )->bool :
        """Simple yes/no confirmation."""
        print ("\n"+"="*60 )
        print ("⚠️  HUMAN INPUT REQUIRED")
        print ("="*60 )
        print (f"\n{question }\n")

        while True :
            try :
                choice =input ("Your answer (y/n): ").strip ().lower ()
                if choice in ['y','yes']:
                    return True 
                elif choice in ['n','no']:
                    return False 
                else :
                    print ("❌ Please enter 'y' or 'n'")
            except KeyboardInterrupt :
                print ("\n\n🛑 User cancelled operation")
                return False 




class HighlightItem (BaseModel ):
    id :str =Field (default_factory =lambda :str (uuid .uuid4 ()))
    text :str 
    app_name :str 
    timestamp :str =Field (default_factory =lambda :datetime .now ().isoformat ())

class PointerMemory :
    def __init__ (self ,stm_capacity :int =5 ):
        self .stm_capacity =stm_capacity 
        self .short_term_memory =deque (maxlen =stm_capacity )
        self .chroma_client =chromadb .Client ()
        self .long_term_collection =self .chroma_client .get_or_create_collection (
        name ="pointer_long_term_memory",
        metadata ={"hnsw:space":"cosine"}
        )

    def add_highlight (self ,text :str ,app_name :str ):
        new_item =HighlightItem (text =text ,app_name =app_name )

        if len (self .short_term_memory )==self .stm_capacity :
            oldest_item =self .short_term_memory [0 ]
            self ._save_to_long_term (oldest_item )

        self .short_term_memory .append (new_item )

    def _save_to_long_term (self ,item :HighlightItem ):
        self .long_term_collection .add (
        documents =[item .text ],
        metadatas =[{"app_name":item .app_name ,"timestamp":item .timestamp }],
        ids =[item .id ]
        )

    def get_recent_context (self )->str :
        """Returns formatted string of recent highlights."""
        if not self .short_term_memory :
            return "No recent highlights."

        context_lines =["Recent highlights:"]
        for item in self .short_term_memory :
            context_lines .append (f"- [{item .app_name }] {item .text [:50 ]}...")

        return "\n".join (context_lines )




class HITLAgent :
    def __init__ (self ):
        self .risk_assessor =RiskAssessor ()
        self .human_interface =HumanInTheLoop ()
        self .memory =PointerMemory (stm_capacity =3 )

    def execute_with_approval (self ,action_description :str ,highlighted_text :str ,app_name :str ):
        """Main method that assesses risk and asks for approval if needed."""


        print (f"\n📝 [Memory] Recording highlight from {app_name }...")
        self .memory .add_highlight (highlighted_text ,app_name )


        recent_context =self .memory .get_recent_context ()
        print (f"\n🧠 [Memory] Recent context:\n{recent_context }")


        print (f"\n🔍 [Risk Assessor] Evaluating risk of action: '{action_description }'...")
        risk_assessment =self .risk_assessor .assess_risk (action_description ,highlighted_text )

        print (f"\n📊 [Risk Assessment]")
        print (f"   Is Risky: {risk_assessment .is_risky }")
        print (f"   Risk Level: {risk_assessment .risk_level }")
        print (f"   Reason: {risk_assessment .reason }")


        if risk_assessment .is_risky :
            question =f"""⚠️  This action is {risk_assessment .risk_level .upper ()} RISK.

Reason: {risk_assessment .reason }

{recent_context }

What would you like me to do?"""

            user_choice =self .human_interface .ask_confirmation (
            question ,
            risk_assessment .suggested_options 
            )

            if user_choice =="Cancel":
                print ("\n🛑 Operation cancelled by user.")
                return None 

            print (f"\n✅ User chose: {user_choice }")
            return self ._execute_action (action_description ,user_choice )


        else :
            print (f"\n✅ Action is safe. Executing immediately...")
            return self ._execute_action (action_description ,"Execute")

    def _execute_action (self ,action_description :str ,user_choice :str ):
        """Simulates executing the action based on user's choice."""
        print (f"\n🤖 [Agent] Executing with choice: '{user_choice }'")
        print (f"   Action: {action_description }")


        if "show"in user_choice .lower ()or "explain"in user_choice .lower ():
            return {"status":"explanation_generated","action":action_description }
        elif "apply"in user_choice .lower ():
            return {"status":"action_applied","action":action_description }
        else :
            return {"status":"completed","action":action_description }




if __name__ =="__main__":
    agent =HITLAgent ()

    print ("="*60 )
    print ("🚀 AI POINTER - HUMAN-IN-THE-LOOP DEMO")
    print ("="*60 )


    print ("\n\n"+"🔵 SCENARIO 1: SAFE ACTION".center (60 ,"="))
    print ("\nUser highlights: 'The API returns a JSON object with user data'")
    print ("User asks: 'explain this'")

    result1 =agent .execute_with_approval (
    action_description ="explain this",
    highlighted_text ="The API returns a JSON object with user data",
    app_name ="VS Code"
    )
    print (f"\nResult: {result1 }")

    print ("\n\n"+"SCENARIO 2: RISKY ACTION".center (60 ,"="))
    print ("\nUser highlights: 'DATABASE_URL=postgres://admin:password123@prod-db:5432/myapp'")
    print ("User asks: 'fix this typo'")

    result2 =agent .execute_with_approval (
    action_description ="fix this typo",
    highlighted_text ="DATABASE_URL=postgres://admin:password123@prod-db:5432/myapp",
    app_name ="VS Code"
    )
    print (f"\nResult: {result2 }")


    print ("\n\n"+"🟡 SCENARIO 3: TESTING MEMORY CONTEXT".center (60 ,"="))
    print ("\nUser highlights: 'Error 500: Database connection timeout'")
    print ("User asks: 'help me debug this'")

    result3 =agent .execute_with_approval (
    action_description ="help me debug this",
    highlighted_text ="Error 500: Database connection timeout",
    app_name ="Terminal"
    )
    print (f"\nResult: {result3 }")

    print ("\n\n"+"="*60 )
    print ("✅ DEMO COMPLETE")
    print ("="*60 )