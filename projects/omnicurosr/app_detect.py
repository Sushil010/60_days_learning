import win32gui, win32process, psutil

def get_active_app():
    hwnd = win32gui.GetForegroundWindow()       
    title = win32gui.GetWindowText(hwnd)        
    _, pid = win32process.GetWindowThreadProcessId(hwnd)  
    name = psutil.Process(pid).name()            
    return {"name": name, "title": title}