import mouse,os,json, base64
import time
import mss
from PIL import Image
from groq import Groq
from dotenv import load_dotenv
from pydantic import BaseModel,Field
from typing import List
from duckduckgo_search import DDGS


FRAME_SIZE =   750
TRIPLE_CLICK_WINDOW = 0.5  
click_times = []  

load_dotenv()
class MouseEvent:
    def __init__(self):
        self.last_captured_image = None

    def is_triple_click(self):
        now = time.time()
        
        click_times[:] = [t for t in click_times if now - t < TRIPLE_CLICK_WINDOW]
        
        if len(click_times) >= 3:
            click_times.clear()  
            return True
        return False

    def on_click(self):
        now = time.time()
        click_times.append(now)
        
        if self.is_triple_click():
            print("\nTriple-click detected!")
            self.capture_frame()

    def capture_frame(self):
        x, y = mouse.get_position()
        print(f"📍 Cursor at: ({x}, {y})")
        
        left = max(0, x - FRAME_SIZE // 2)
        top = max(0, y - FRAME_SIZE // 2)
        
        monitor = {
            "left": left,
            "top": top,
            "width": FRAME_SIZE,
            "height": FRAME_SIZE
        }
        
        with mss.MSS() as sct:
            screenshot = sct.grab(monitor)
            
            img = Image.frombytes("RGB", screenshot.size, screenshot.bgra, "raw", "BGRX")
            
            filename = f"capture_{int(time.time())}.png"
            img.save(filename)
            self.last_captured_image = filename
            print(f"Saved as: {filename}")
            return filename
            



tools=[
    {
        "type":"function",
        "function":{
            "name":"search_web",
            "description":"Search the web for information about the image content",
            "parameters":{
                "type":"object",
                "properties":{
                    "query":{
                        "type":"string",
                        "description":"The search query to look up on the web"
                    }
                },
                "required":["query"]
            }
        }

    }
]

def search_web(query):
        print(f"Tool is searching for the query: {query}")
        try:
            with DDGS() as ddgs:
                results=ddgs.text(query,max_results=5)
                output=[]
                for index, value in enumerate(results):
                    output.append(f"[{index+1}] Title: {value['title']}\nURL:{value['href']}\nBody: {value['body']}\n ")
                return "\n".join(output)
        except Exception as e:
            return f"Search failed: {e}"


class ImageAnalysis(BaseModel):
    description: str = Field(description="Detailed description of what's in the image (2-3 sentences)")
    content_type: str = Field(description="Type of content: 'text', 'image', 'chart', 'code', 'ui_element', 'mixed'")
    key_elements: List[str] = Field(description="List of important elements visible in the image")


class VisionModel:
    def __init__(self):
        self.client=Groq(api_key=os.getenv('api'))
    

    
    def visioncall(self,image_path:str,user_query:str):
        schema_str=json.dumps(ImageAnalysis.model_json_schema(),indent=2)
        base64_image = self.image_to_base64(image_path)
        messages=[
            {
                "role": "system",
                "content": f"""You are an image analysis AI. Analyze the provided image and return only a JSON object matching this schema:

{schema_str}

Do not include any extra text, markdown, or commentary. Be detailed and accurate."""
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": f"User's question: {user_query}"
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/png;base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        while True:
            completions=self.client.chat.completions.create(
                messages=messages,
                model="meta-llama/llama-4-scout-17b-16e-instruct",
                response_format={"type": "json_object"},
                max_tokens=1000,
                temperature=0.2
            )

            reply=completions.choices[0].message
            messages.append(reply)

            content = reply.content or "{}"
            try:
                return ImageAnalysis.model_validate_json(content)
            except Exception as e:
                print(f"Could not parse response as ImageAnalysis: {e}")
                return ImageAnalysis(
                    description=str(content),
                    content_type="image",
                    key_elements=[]
                )
    
    def image_to_base64(self, image_path: str) -> str:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode('utf-8')
    


class VisionAgent:
    def __init__(self):
        self.mouse_event = MouseEvent()
        self.vision_model = VisionModel()
        self.current_image = None  
    
    def start(self):
        mouse.on_click(self.mouse_event.on_click)
        
        try:
            while True:
                time.sleep(0.1)
                
                if self.mouse_event.last_captured_image:
                    self.current_image = self.mouse_event.last_captured_image
                    self.mouse_event.last_captured_image = None  
                    
                    self.analyze_and_interact()
                    
        except KeyboardInterrupt:
            print("\n\nStopped")
    
    def analyze_and_interact(self):
        """Analyze the captured image and start interactive Q&A"""
        if not self.current_image:
            return
        
        print(f"\nAnalyzing captured image: {self.current_image}")
        
        initial_question = "What's in this image? Provide a detailed description."
        analysis = self.vision_model.visioncall(self.current_image, initial_question)
        
        print("\n" + "="*60)
        print("INITIAL ANALYSIS")
        print("="*60)
        print(f"Description: {analysis.description}")
        print(f"Content Type: {analysis.content_type}")
        print(f"Key Elements: {', '.join(analysis.key_elements)}")
        print("="*60)
        
        self.interactive_loop()
    
    def interactive_loop(self):

        print("\nYou can now ask follow-up questions about this image.")
        print("   Type 'exit' to stop, or triple-click to capture a new image.\n")
        
        while True:
            try:
                user_question = input("You: ").strip()
                
                if user_question.lower() in ['exit', 'quit', 'q']:
                    print("Exiting interactive mode.")
                    break
                
                if not user_question:
                    continue
                
                print("\nThinking...")
                analysis = self.vision_model.visioncall(self.current_image, user_question)
                
                # Show the answer
                print(f"\nAnswer: {analysis.description}")
                if analysis.key_elements:
                    print(f"Key Points: {', '.join(analysis.key_elements)}")
                print()
                
            except KeyboardInterrupt:
                print("\n\nExiting interactive mode.")
                break

if __name__ == "__main__":
    agent = VisionAgent()
    agent.start()
