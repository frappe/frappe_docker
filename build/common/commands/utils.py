import subprocess


def run_command(command, stdout=None, stdin=None, stderr=None):
    stdout = stdout or subprocess.PIPE
    stderr = stderr or subprocess.PIPE
    process = subprocess.Popen(command, stdout=stdout, stdin=stdin, stderr=stderr)
    out, error = process.communicate()
    if process.returncode:
        print("Something went wrong:")
        print(f"return code: {process.returncode}")
        print(f"stdout:\n{out}")
        print(f"\nstderr:\n{error}")
        exit(process.returncode)
