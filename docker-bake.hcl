variable "REGISTRY_USER" {
    default = "zapal"
}

variable PYTHON_VERSION {
    default = "3.11.6"
}
variable NODE_VERSION {
    default = "18.18.2"
}

variable "FRAPPE_VERSION" {
    default = "version-15"
}

variable "ERPNEXT_VERSION" {
    default = "version-15"
}

variable "HRMS_VERSION" {
    default = "version-15"
}

variable "INSIGHTS_VERSION" {
    default = "version-3"
}

variable "FRAPPE_REPO" {
    default = "https://github.com/zapal-tech/erp-frappe"
}

variable "ERPNEXT_REPO" {
    default = "https://github.com/zapal-tech/erp-erpnext"
}

variable "HRMS_REPO" {
    default = "https://github.com/zapal-tech/erp-hrms"
}

variable "INSIGHTS_REPO" {
    default = "https://github.com/zapal-tech/erp-insights"
}

variable "BENCH_REPO" {
    default = "https://github.com/frappe/bench"
}

variable "LATEST_BENCH_RELEASE" {
    default = "latest"
}

# Bench image

target "bench" {
    args = {
        GIT_REPO = "${BENCH_REPO}"
    }
    context = "images/bench"
    target = "bench"
    tags = ["frappe/bench:${LATEST_BENCH_RELEASE}", "frappe/bench:latest"]
}

target "bench-test" {
    inherits = ["bench"]
    target = "bench-test"
}

# Main images
# Base for all other targets

group "default" {
    targets = ["erpnext", "base", "build"]
}

function "tag" {
    params = [repo, version]
    result = [
      # Push frappe or erpnext branch as tag
      "${REGISTRY_USER}/${repo}:${version}",
      # If `version` param is develop (development build) then use tag `latest`
      "${version}" == "develop" ? "${REGISTRY_USER}/${repo}:latest" : "${REGISTRY_USER}/${repo}:${version}",
      # Make short tag for major version if possible. For example, from v13.16.0 make v13.
      can(regex("(v[0-9]+)[.]", "${version}")) ? "${REGISTRY_USER}/${repo}:${regex("(v[0-9]+)[.]", "${version}")[0]}" : "",
      # Make short tag for major version if possible. For example, from v13.16.0 make version-13.
      can(regex("(v[0-9]+)[.]", "${version}")) ? "${REGISTRY_USER}/${repo}:version-${regex("([0-9]+)[.]", "${version}")[0]}" : "",
    ]
}

target "default-args" {
    args = {
        FRAPPE_PATH = "${FRAPPE_REPO}"
        ERPNEXT_REPO = "${ERPNEXT_REPO}"
        HRMS_REPO = "${HRMS_REPO}"
        INSIGHTS_REPO = "${INSIGHTS_REPO}"
        BENCH_REPO = "${BENCH_REPO}"
        FRAPPE_BRANCH = "${FRAPPE_VERSION}"
        ERPNEXT_BRANCH = "${ERPNEXT_VERSION}"
        HRMS_BRANCH = "${HRMS_VERSION}"
        INSIGHTS_BRANCH = "${INSIGHTS_VERSION}"
        PYTHON_VERSION = "${PYTHON_VERSION}"
        NODE_VERSION = "${NODE_VERSION}"
    }
}

target "erpnext" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "erpnext"
    tags = tag("erp", "${ERPNEXT_VERSION}")
}

target "base" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "base"
    tags = tag("base", "${FRAPPE_VERSION}")
}

target "build" {
    inherits = ["default-args"]
    context = "."
    dockerfile = "images/production/Containerfile"
    target = "build"
    tags = tag("build", "${ERPNEXT_VERSION}")
}
