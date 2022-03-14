APP_NAME="custom_app"

variable "FRAPPE_VERSION" {}

group "default" {
    targets = ["backend", "frontend"]
}

target "backend" {
    dockerfile = "backend.Dockerfile"
    tags = ["custom_app/worker:latest"]
    args = {
      "FRAPPE_VERSION" = FRAPPE_VERSION
      "APP_NAME" = APP_NAME
    }
}

target "frontend" {
    dockerfile = "frontend.Dockerfile"
    tags = ["custom_app/nginx:latest"]
    args = {
      "FRAPPE_VERSION" = FRAPPE_VERSION
      "APP_NAME" = APP_NAME
    }
}
