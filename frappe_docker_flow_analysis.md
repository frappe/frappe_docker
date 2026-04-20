# Phân tích luồng hoạt động của frappe_docker

## Mục đích chung
`frappe_docker` không chứa mã nguồn Frappe/ERPNext. Nó là một repository định nghĩa:

- Docker Compose cho các dịch vụ Frappe
- Docker image / Dockerfile build
- các tập tin cấu hình và script hỗ trợ
- tài liệu hướng dẫn deploy và phát triển

Nhiệm vụ chính của repo là "bọc" Frappe và Bench trong Docker, rồi điều phối các container.

---

## Thành phần chính

### 1. `compose.yaml`

Đây là file Docker Compose chính, định nghĩa các service:

- `configurator`
  - chạy trước
  - cấu hình các tham số của Bench dựa trên biến môi trường
  - thiết lập `db_host`, `db_port`, `redis_cache`, `redis_queue`, `redis_socketio`, `socketio_port`

- `backend`
  - container chạy Frappe backend
  - sử dụng image tùy chỉnh chứa mã Frappe và app

- `frontend`
  - container chạy Nginx làm reverse proxy
  - phục vụ HTTP/HTTPS và chuyển đến `backend:8000`

- `websocket`
  - container chạy `node /home/frappe/frappe-bench/apps/frappe/socketio.js`
  - xử lý realtime và WebSocket

- `queue-short`, `queue-long`, `scheduler`
  - chạy các lệnh `bench worker ...` và `bench schedule`
  - xử lý task queue và công việc nền

- `volumes`:
  - `sites` dùng chung giữa nhiều container, chứa thư mục `frappe-bench/sites`

---

## Tại sao các chức năng Frappe được kích hoạt

Các chức năng như tạo site, cài app, chạy web, queue, realtime đều xuất phát từ Frappe/bench:

- `bench` là công cụ chính của Frappe để tạo bench, tạo site và cài app
- `docker compose` khởi động container và cung cấp môi trường mạng, volume, biến môi trường
- `configurator` đặt cấu hình Bench đúng với tên service Docker
- `backend`, `frontend`, `websocket`, `queue-*`, `scheduler` là các service thực thi lệnh cụ thể của Frappe

Nói cách khác: repo này không tự viết logic Frappe, mà tạo môi trường để `bench` và Frappe thực thi.

---

## `development/installer.py`

Đây là script hỗ trợ cho môi trường phát triển. Luồng hoạt động chính:

1. phân tích tham số dòng lệnh:
   - `--apps-json`
   - `--bench-name`
   - `--site-name`
   - `--frappe-repo`
   - `--frappe-branch`
   - `--py-version`
   - `--node-version`
   - `--admin-password`
   - `--db-type`

2. nếu bench chưa tồn tại:
   - chạy `bench init` với `--frappe-path`, `--frappe-branch`, `--apps_path`
   - cấu hình Bench:
     - `bench set-config -g db_type ...`
     - `bench set-config -g redis_cache redis://redis-cache:6379`
     - `bench set-config -g redis_queue redis://redis-queue:6379`
     - `bench set-config -g redis_socketio redis://redis-queue:6379`
     - `bench set-config -gp developer_mode 1`

3. tạo site mới:
   - dùng `bench new-site`
   - chọn host DB là `mariadb` hoặc `postgresql`
   - thiết lập `db_root_password`, `admin_password`
   - cài đặt các app trong thư mục `bench/apps` (ngoại trừ `frappe`)

Điểm quan trọng: script này chỉ gọi `bench` qua `subprocess.call()`, và không thực hiện logic Frappe trực tiếp.

---

## Kết luận

- `frappe_docker` là lớp cấu hình và trình điều phối Docker cho Frappe.
- Các chức năng thực sự chạy nhờ Frappe/ERPNext và Bench bên trong container.
- `compose.yaml` thiết lập các dịch vụ cần thiết và mối liên kết giữa chúng.
- `development/installer.py` tự động hoá việc tạo bench và site trong môi trường dev.

Nếu muốn mở rộng thêm, có thể xem thêm `pwd.yml` cho bản demo nhanh và `docs/05-development/01-development.md` để biết chi tiết dùng `installer.py`.