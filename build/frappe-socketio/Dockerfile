FROM node:buster-slim

# Add frappe user
RUN useradd -ms /bin/bash frappe

# Create bench directories and set ownership
RUN mkdir -p /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/apps/frappe \
    && chown -R frappe:frappe /home/frappe

# Download socketio and purge curl package
COPY build/frappe-socketio/package.json /home/frappe/frappe-bench/apps/frappe
ARG GIT_BRANCH=version-12
RUN apt-get update && apt-get install -y curl \
    && cd /home/frappe/frappe-bench/apps/frappe \
    && curl "https://raw.githubusercontent.com/GraficheAquilane2021/frappe/$GIT_BRANCH/socketio.js" \
        --output /home/frappe/frappe-bench/apps/frappe/socketio.js \
    && curl "https://raw.githubusercontent.com/GraficheAquilane2021/frappe/$GIT_BRANCH/node_utils.js" \
        --output /home/frappe/frappe-bench/apps/frappe/node_utils.js \
    && apt-get purge -y curl && apt-get autoremove -y \
    && rm -rf /var/lib/apt/lists/*

RUN cd /home/frappe/frappe-bench/apps/frappe \
    && npm install --only=production \
    && node --version \
    && npm --version

# Setup docker-entrypoint
COPY build/frappe-socketio/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

WORKDIR /home/frappe/frappe-bench/sites

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]