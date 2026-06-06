import uuid,os,time,json
from datetime import datetime
from day5_main import prompt_hash

def event_log(trace_id,status,details,method):
    log_entry={
        "timestamp":datetime.now().isoformat(),
        "status":status,
        "details":details,
        "method":method,
        "trace_id":trace_id
    }
    print(json.dumps(log_entry))
    with open ("event_log.jsonl","a") as f:
        f.write(json.dumps(log_entry)+'\n')

def prompt_call(user_prompt):
    trace_id=str(uuid.uuid4())[:8]

    event_log(trace_id,"received",{"user_prompt":user_prompt},"simple_call")

    h=prompt_hash(user_prompt)
    event_log(trace_id,"received",{"hashed_prompt":h},"hashed_call")

    event_log(trace_id,"error",{"attempt1":"failure"},"api_timeout")
    time.sleep(0.2)
    event_log(trace_id,"success",{"attempt2":"success"},"api_loaded")

    event_log(trace_id,"success",{"token":50,"cost_usd":0.0002},"cost and token loaded")


if __name__=="__main__":

    if os.path.exists("event_log.jsonl"):
        os.remove("event_log.jsonl")

    prompt_call("Explain deep learning")