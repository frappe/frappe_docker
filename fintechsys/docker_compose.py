import subprocess
import requests

subprocess.check_call(['sudo', 'apt-get', 'update'])

# 1. install a few prerequisite packages which let apt use packages over HTTPS:
def  install_few_prerequisite_packages(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "sudo apt install apt-transport-https ca-certificates curl software-properties-common"
install_few_prerequisite_packages(command)

# 2.Then add the GPG key for the official Docker repository to your system:
def add_the_GPG (command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -"
add_the_GPG(command)

# 3.Add the Docker repository to APT sources:
def add_dockere_repo(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "sudo add-apt-repository 'deb [arch=amd64] https://download.docker.com/linux/ubuntu focal stable'"
add_dockere_repo(command)

# 4.Make sure you are about to install from the Docker repo instead of the default Ubuntu repo:
def make_sure(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")

        # Print the output
        if stdout:
            print(stdout.decode())
        if stderr:
            print(stderr.decode())
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "apt-cache policy docker-ce"
make_sure(command)

# 5.Finally, install Docker:
def install_docker(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "sudo apt install docker-ce"
install_docker(command)

# 6.To check whether you can access and download images from Docker Hub, type:
def check_access_and_download_images(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Command executed successfully.")
        else:
            print("Command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

# Call the function with your desired command
command = "docker run hello-world"
check_access_and_download_images(command)

# -------------------------------------------------------------------------------

def install_docker_compose():
    try:

        subprocess.check_call(['sudo', 'curl', '-SL', '-o', '/usr/local/bin/docker-compose', 'https://github.com/docker/compose/releases/download/v2.20.3/docker-compose-Linux-x86_64'])
        subprocess.check_call(['sudo', 'chmod', '+x', '/usr/local/bin/docker-compose'])
        print('Docker Compose installed successfully.')
    except subprocess.CalledProcessError:
        print('Installation of Docker Compose failed.')

install_docker_compose()



# def run_shell_command(command):
#     try:
#         # Execute the command and capture the output
        
#         process = subprocess.Popen(command, shell=True)
#         process.wait()

#         # Check the return code
#         if process.returncode == 0:
#             print("Command executed successfully.")
#         else:
#             print("Command failed.")
#     except Exception as e:
#         print("An error occurred:", str(e))

# # Call the function with your desired command
# command = "sudo wget -O /usr/local/bin/docker-compose https://github.com/docker/compose/releases/download/1.29.2/docker-compose-$(uname -s)-$(uname -m)"
# run_shell_command(command)
