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
