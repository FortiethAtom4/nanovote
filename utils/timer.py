import datetime
# a simple timer for me to use.

class Timer:
    def __init__(self):
        self.cur_time: datetime.datetime = datetime.datetime.now() 
        self.end_time: datetime.datetime = datetime.datetime.now() 
        self.pause_time: datetime.datetime = None
        self.stopped = True

    def start(self,end_time: datetime.timedelta):
        if not self.stopped:
            return False
        self.end_time = datetime.datetime.now() + end_time
        self.stopped = False
        return True

    # returns true if time is up, else false
    def increment(self) -> bool | None:
        self.cur_time = datetime.datetime.now()
        if self.cur_time >= self.end_time:
            self.stopped = True
            self.pause_time = None
        
        return self.stopped

    # returns true if self.stopped is already true, else false
    def pause(self):
        if self.stopped:
            return True
        self.pause_time = datetime.datetime.now()
        self.stopped = True
        return False

    # returns false if self.stopped is already false, else true
    def unpause(self) -> bool:
        if not self.stopped:
            return False
        temp_unpause_delta: datetime.timedelta = self.end_time - self.pause_time
        self.end_time = datetime.datetime.now() + temp_unpause_delta
        self.stopped = False
        self.pause_time = None
        return True
    
    def toggle(self):
        if self.stopped:
            return self.unpause()
        return self.pause()
        
    
    def add_time(self,hours: int, minutes: int):
        time_added = datetime.timedelta(hours=hours,minutes=minutes)
        self.end_time += time_added
        self.increment() # updates self.stopped if subtracted time goes over time limit
        return time_added
    
    # returns 0 if stopped, 1 if paused, 2 if running
    def paused_or_stopped(self) -> 0 | 1 | 2:
        if self.stopped:
            if self.pause_time == None:
                return 0
            return 1
        return 2
    
    def print_timer(self):
        return datetime.timedelta(seconds=int((self.end_time - self.cur_time).total_seconds()))
