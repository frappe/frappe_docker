import subprocess, requests, datetime, _thread, time, os, signal
start_time = datetime.datetime.now().time()
bench_start = 'docker exec -i frappe bash -c "bench start"'
process = subprocess.Popen(bench_start, stdout=subprocess.PIPE , shell=True)


def print_out(val,delay):
	while 1:
		time.sleep(delay)
		if val == 1:
			result,error = process.communicate()
			print(result)
		elif val == 2:
			try:
				global r
				r = requests.get("http://site1.local:8000")
				print(r)
			except requests.exceptions.ConnectionError as e:
				print(e)

_thread.start_new_thread(print_out, (1, 1))
#result, error = process.communicate()
_thread.start_new_thread(print_out, (2, 1))

time.sleep(30)

process.kill()

assert '<title> Login </title>' in str(r.content)
