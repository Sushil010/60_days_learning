import time

class TokenBucket:
    def __init__(self,max_tokens,token_rate,):
        self.max_tokens=max_tokens
        self.token_rate=token_rate
        self.last_time=time.time()


    def refill(self):
        now=time.time()
        passed_time=now - self.last_time
        new_token=passed_time * self.token_rate

        if self.max_tokens > 0:
            self.max_tokens=min(self.max_tokens,self.max_tokens+new_token)
            self.last_time=now
    

    def consume(self):
        self.refill()
        if self.max_tokens>1:
            self.max_tokens-=1
            return True
        else:
            return False


if __name__=="__main__":
    tb=TokenBucket(max_tokens=5,token_rate=1)
    for i in range(7):
        if tb.consume():
            print(f" Request {i+1}: Allowed")
        else:
            print(f" Request {i+1}: Blocked, Rate limit Reached")
        time.sleep(0.2)

        
        
    