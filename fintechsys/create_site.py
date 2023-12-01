import subprocess

def run_docker_command(command):
    try:
        # Execute the command and capture the output
        process = subprocess.Popen(command, shell=True)
        process.wait()

        # Check the return code
        if process.returncode == 0:
            print("Docker Compose command executed successfully.")
        else:
            print("Docker Compose command failed.")
    except Exception as e:
        print("An error occurred:", str(e))

if __name__ == "__main__":

    docker_command = "docker compose --project-name erpnext-one exec backend \
  bench new-site --no-mariadb-socket --mariadb-root-password fintech2023 --install-app hrms --set-default \
           --install-app rule_management --install-app remittance_base --install-app remittance --install-app bulk_remittance --install-app remittance_stellar_integration \
           --install-app client_account_management  --install-app teller_for_erpnext --install-app teller_for_agent \
           --install-app remittance_agent_service --install-app payment_management --install-app bank_services --install-app remittance_customize \
           --install-app remittance_network_manager --install-app erpnext_theme --install-app remittance_website --admin-password fintech2023  agent.fintechsys.net"

    run_docker_command(docker_command)
