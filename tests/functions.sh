#!/bin/bash

print_group() {
    echo ::endgroup::
    echo "::group::$*"
}

ping_site() {
    print_group "Ping site $SITE_NAME"

    echo Ping version
    ping_res=$(curl -sS "http://$SITE_NAME/api/method/version")
    echo "$ping_res"
    if [[ -z $(echo "$ping_res" | grep "message" || echo "") ]]; then
        echo "Ping failed"
        exit 1
    fi

    echo Check index
    index_res=$(curl -sS "http://$SITE_NAME")
    if [[ -n $(echo "$index_res" | grep "Internal Server Error" || echo "") ]]; then
        echo "Index check failed"
        echo "$index_res"
        exit 1
    fi
}

docker_compose_with_args() {
    # shellcheck disable=SC2068
    docker-compose \
        -p $project_name \
        -f installation/docker-compose-common.yml \
        -f installation/docker-compose-frappe.yml \
        -f installation/frappe-publish.yml \
        $@
}

check_migration_complete() {
    print_group Check migration

    container_id=$(docker_compose_with_args ps -q frappe-python)
    cmd="docker logs ${container_id} 2>&1 | grep 'Starting gunicorn' || echo ''"
    worker_log=$(eval "$cmd")
    INCREMENT=0

    while [[ ${worker_log} != *"Starting gunicorn"* && ${INCREMENT} -lt 120 ]]; do
        sleep 3
        ((INCREMENT = INCREMENT + 1))
        echo "Wait for migration to complete..."
        worker_log=$(eval "$cmd")
        if [[ ${worker_log} != *"Starting gunicorn"* && ${INCREMENT} -eq 120 ]]; then
            echo Migration timeout
            docker logs "${container_id}"
            exit 1
        fi
    done

    echo Migration Log
    docker logs "${container_id}"
}

check_health() {
    print_group Loop health check

    docker run --name frappe_doctor \
        -v "${project_name}_sites-vol:/home/frappe/frappe-bench/sites" \
        --network "${project_name}_default" \
        frappe/frappe-worker:edge doctor || true

    cmd='docker logs frappe_doctor | grep "Health check successful" || echo ""'
    doctor_log=$(eval "$cmd")
    INCREMENT=0

    while [[ -z "${doctor_log}" && ${INCREMENT} -lt 60 ]]; do
        sleep 1
        ((INCREMENT = INCREMENT + 1))
        container=$(docker start frappe_doctor)
        echo "Restarting ${container}..."
        doctor_log=$(eval "$cmd")

        if [[ ${INCREMENT} -eq 60 ]]; then
            docker logs "${container}"
            exit 1
        fi
    done
}
