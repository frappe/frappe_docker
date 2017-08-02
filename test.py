import subprocess,requests,time

time.sleep(45)

try:
    r = requests.get("site1.local:8000")
    assert '<title> Login </title>' in r.content, "Login page failed to load"
except Exception as e:
    traceback.print_exc(e)
    sys.exit(3)
