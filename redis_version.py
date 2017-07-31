import subprocess
import re

command_out_string = subprocess.check_output('redis-cli -h redis -c INFO',shell=True)
#command_out_string = "cats \nare smarter than dogs"
#output = subprocess.check_output(('grep', 'redis_version'), stdin=version_string.stdout)

#print(command_out_string)
#output = command_out_string.split('\n')
#print(output)

try:
	version = re.match(r'(.*)redis_version(.+?)\n', command_out_string, re.M|re.I|re.DOTALL|re.S)
	print(version.group(2).strip(':'))
except:
	print("Version not found")
#version_string.wait()

#out,err = version_string.communicate()

#print(out, err)
