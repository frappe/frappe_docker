import subprocess


def run_command(command):
    process = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, error = process.communicate()
    if process.returncode:
        print("Something went wrong:")
        print(f"return code: {process.returncode}")
        print(f"stdout:\n{out}")
        print(f"\nstderr:\n{error}")
        exit(process.returncode)
