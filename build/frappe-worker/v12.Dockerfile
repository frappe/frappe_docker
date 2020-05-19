FROM bitnami/python:latest-prod

RUN useradd -ms /bin/bash frappe
WORKDIR /home/frappe/frappe-bench
RUN install_packages \
    git \
    wkhtmltopdf \
    mariadb-client \
    gettext-base \
    wget \
    # for PDF
    libssl-dev \
    fonts-cantarell \
    xfonts-75dpi \
    xfonts-base \
    # For psycopg2
    libpq-dev \
    build-essential

# Install wkhtmltox correctly
RUN wget https://github.com/wkhtmltopdf/wkhtmltopdf/releases/download/0.12.5/wkhtmltox_0.12.5-1.buster_amd64.deb
RUN dpkg -i wkhtmltox_0.12.5-1.buster_amd64.deb && rm wkhtmltox_0.12.5-1.buster_amd64.deb

RUN mkdir -p apps logs commands /home/frappe/backups

RUN virtualenv env \
    && . env/bin/activate \
    && cd apps \
    && git clone --depth 1 -o upstream https://github.com/frappe/frappe --branch version-12 \
    && pip3 install --no-cache-dir -e /home/frappe/frappe-bench/apps/frappe

COPY build/common/commands/* /home/frappe/frappe-bench/commands/
COPY build/common/common_site_config.json.template /opt/frappe/common_site_config.json.template

# Setup docker-entrypoint
COPY build/common/worker/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

COPY build/common/worker/install_app.sh /usr/local/bin/install_app

WORKDIR /home/frappe/frappe-bench/sites

RUN chown -R frappe:frappe /home/frappe/frappe-bench/sites /home/frappe/backups

VOLUME [ "/home/frappe/frappe-bench/sites", "/home/frappe/backups" ]

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
