# Images

target "bench-build" {
    tags = ["frappe/bench:latest"]
    dockerfile = "build/bench/Dockerfile"
    target = "build"
}

target "bench-test" {
    inherits = ["bench-build"]
    target = "test"
}

target "frappe-nginx" {
    dockerfile = "build/frappe-nginx/Dockerfile"
}

target "frappe-worker" {
    dockerfile = "build/frappe-worker/Dockerfile"
}

target "frappe-socketio" {
    dockerfile = "build/frappe-socketio/Dockerfile"
}

target "erpnext-nginx" {
    dockerfile = "build/erpnext-nginx/Dockerfile"
}

target "erpnext-worker" {
    dockerfile = "build/erpnext-worker/Dockerfile"
}


# Helpers

target "develop-args" {
    args = {
        GIT_BRANCH = "develop"
        IMAGE_TAG = "develop"
    }
}

variable "GIT_TAG" {}
variable "GIT_BRANCH" {}
variable "VERSION" {}

target "stable-args" {
    args = {
        GIT_BRANCH = "${GIT_BRANCH}"
        IMAGE_TAG = "${GIT_BRANCH}"
        PYTHON_VERSION = "${VERSION}" == "12" ? "3.7" : "3.9"
    }
}

function "set_develop_tags" {
    params = [repo]
    result = ["${repo}:latest", "${repo}:edge", "${repo}:develop"]
}

function "set_stable_tags" {
    params = [repo]
    result = ["${repo}:${GIT_TAG}", "${repo}:v${VERSION}", "${repo}:${GIT_BRANCH}"]
}

function "set_test_tags" {
    params = [repo]
    result = ["${repo}:test"]
}


# Develop

target "frappe-nginx-develop" {
    inherits = ["frappe-nginx", "develop-args"]
    tags = set_develop_tags("frappe/frappe-nginx")
}

target "frappe-worker-develop" {
    inherits = ["frappe-worker", "develop-args"]
    tags = set_develop_tags("frappe/frappe-worker")
}

target "frappe-socketio-develop" {
    inherits = ["frappe-socketio", "develop-args"]
    tags = set_develop_tags("frappe/frappe-socketio")
}

target "erpnext-nginx-develop" {
    inherits = ["erpnext-nginx", "develop-args"]
    tags = set_develop_tags("frappe/erpnext-nginx")
}

target "erpnext-worker-develop" {
    inherits = ["erpnext-worker", "develop-args"]
    tags = set_develop_tags("frappe/erpnext-worker")
}

group "frappe-develop" {
    targets = ["frappe-nginx-develop", "frappe-worker-develop", "frappe-socketio-develop"]
}

group "erpnext-develop" {
    targets = ["erpnext-nginx-develop", "erpnext-worker-develop"]
}

# Develop test

target "frappe-nginx-develop-test" {
    inherits = ["frappe-nginx-develop"]
    tags = set_test_tags("frappe/frappe-nginx")
}

target "frappe-worker-develop-test" {
    inherits = ["frappe-worker-develop"]
    tags = set_test_tags("frappe/frappe-worker")
}

target "frappe-socketio-develop-test" {
    inherits = ["frappe-socketio-develop"]
    tags = set_test_tags("frappe/frappe-socketio")
}

target "erpnext-nginx-develop-test" {
    inherits = ["erpnext-nginx-develop"]
    tags = set_test_tags("frappe/erpnext-nginx")
}

target "erpnext-worker-develop-test" {
    inherits = ["erpnext-worker-develop"]
    tags = set_test_tags("frappe/erpnext-worker")
}

group "frappe-develop-test" {
    targets = ["frappe-nginx-develop-test", "frappe-worker-develop-test", "frappe-socketio-develop-test"]
}

group "erpnext-develop-test" {
    targets = ["erpnext-nginx-develop-test", "erpnext-worker-develop-test"]
}


# Stable

target "frappe-nginx-stable" {
    inherits = ["frappe-nginx", "stable-args"]
    tags = set_stable_tags("frappe/frappe-nginx")
}

target "frappe-worker-stable" {
    inherits = ["frappe-worker", "stable-args"]
    tags = set_stable_tags("frappe/frappe-worker")
}

target "frappe-socketio-stable" {
    inherits = ["frappe-socketio", "stable-args"]
    tags = set_stable_tags("frappe/frappe-socketio")
}

target "erpnext-nginx-stable" {
    inherits = ["erpnext-nginx", "stable-args"]
    tags = set_stable_tags("frappe/erpnext-nginx")
}

target "erpnext-worker-stable" {
    inherits = ["erpnext-worker", "stable-args"]
    tags = set_stable_tags("frappe/erpnext-worker")
}

group "frappe-stable" {
    targets = ["frappe-nginx-stable", "frappe-worker-stable", "frappe-socketio-stable"]
}

group "erpnext-stable" {
    targets = ["erpnext-nginx-stable", "erpnext-worker-stable"]
}

# Stable test
target "frappe-nginx-stable-test" {
    inherits = ["frappe-nginx-stable"]
    tags = set_test_tags("frappe/frappe-nginx")
}

target "frappe-worker-stable-test" {
    inherits = ["frappe-worker-stable"]
    tags = set_test_tags("frappe/frappe-worker")
}

target "frappe-socketio-stable-test" {
    inherits = ["frappe-socketio-stable"]
    tags = set_test_tags("frappe/frappe-socketio")
}

target "erpnext-nginx-stable-test" {
    inherits = ["erpnext-nginx-stable"]
    tags = set_test_tags("frappe/erpnext-nginx")
}

target "erpnext-worker-stable-test" {
    inherits = ["erpnext-worker-stable"]
    tags = set_test_tags("frappe/erpnext-worker")
}

group "frappe-stable-test" {
    targets = ["frappe-nginx-stable-test", "frappe-worker-stable-test", "frappe-socketio-stable-test"]
}

group "erpnext-stable-test" {
    targets = ["erpnext-nginx-stable-test", "erpnext-worker-stable-test"]
}
