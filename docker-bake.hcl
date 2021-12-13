# Docker Buildx Bake build definition file
# Reference: https://github.com/docker/buildx/blob/master/docs/reference/buildx_bake.md

variable "USERNAME" {
    default = "frappe"
}

variable "FRAPPE_VERSION" {
    default = "develop"
}

variable "ERPNEXT_VERSION" {
    default = "develop"
}

# Bench image

target "bench" {
    tags = ["frappe/bench:latest"]
    dockerfile = "build/bench/Dockerfile"
    target = "build"
}

target "bench-test" {
    inherits = ["bench"]
    target = "test"
}

# Main images
# Base for all other targets

group "frappe" {
    targets = ["backend", "frontend", "socketio"]
}

group "erpnext" {
    targets = ["erpnext-backend", "erpnext-frontend"]
}

group "default" {
    targets = ["frappe", "erpnext"]
}

function "tag" {
    params = [repo, version]
    # If `version` parameter is develop (development build) then use tag `latest`
    result = ["${version}" == "develop" ? "${USERNAME}/${repo}:latest" : "${USERNAME}/${repo}:${version}"]
}

target "default-args" {
    args = {
        FRAPPE_VERSION = "${FRAPPE_VERSION}"
        ERPNEXT_VERSION = "${ERPNEXT_VERSION}"
        # If `ERPNEXT_VERSION` variable contains "v12" use Python 3.7. Else — 3.9.
        PYTHON_VERSION = can(regex("v12", "${ERPNEXT_VERSION}")) ? "3.7" : "3.9"
    }
}

target "frappe-worker" {
    inherits = ["default-args"]
    context = "build/frappe-worker"
    target = "frappe"
    tags = tag("frappe-worker", "${FRAPPE_VERSION}")
}

target "erpnext-worker" {
    inherits = ["default-args"]
    context = "build/frappe-worker"
    target = "erpnext"
    tags =  tag("erpnext-worker", "${ERPNEXT_VERSION}")
}

target "frappe-nginx" {
    inherits = ["default-args"]
    context = "build/frappe-nginx"
    target = "frappe"
    tags =  tag("frappe-nginx", "${FRAPPE_VERSION}")
}

target "erpnext-nginx" {
    inherits = ["default-args"]
    context = "build/frappe-nginx"
    target = "erpnext"
    tags =  tag("erpnext-nginx", "${ERPNEXT_VERSION}")
}

target "frappe-socketio" {
    inherits = ["default-args"]
    context = "build/frappe-socketio"
    tags =  tag("frappe-socketio", "${FRAPPE_VERSION}")
}
