import datetime

errorlog = "errorlog.txt"
datalog = "datalog.txt"

def log(text: str, level: str):
    timestring = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%I %p %Z")
    logtext = timestring + " " + text + "\n"
    if level == "data":
        with open(datalog, "a") as f:
            f.write("[DATA] " + logtext)
    elif level =="error":
        with open(errorlog, "a") as f:
            f.write("[ERROR] " + logtext)