FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONUNBUFFERED=1 \
    PATH="/home/frappe/.local/bin:${PATH}"

RUN apt-get update && apt-get install -y \
    build-essential \
    python3-dev \
    python3-pip \
    python3-setuptools \
    python3-wheel \
    mariadb-client \
    redis-server \
    git \
    curl \
    nginx \
    supervisor \
    python3-venv \
    libssl-dev \
    libffi-dev \
    libmysqlclient-dev \
    pkg-config \
    g++ \
    nodejs \
    npm && \
    npm install -g yarn && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN useradd -m -s /bin/bash frappe
USER frappe
WORKDIR /home/frappe

RUN pip3 install --upgrade pip setuptools
RUN pip3 install frappe-bench

COPY apps.txt /home/frappe/frappe-bench/apps.txt
COPY entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh

EXPOSE 8000

ENTRYPOINT ["/usr/local/bin/entrypoint.sh"]
CMD ["bench", "start"]
