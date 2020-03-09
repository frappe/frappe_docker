FROM node:slim

# Install needed packages
RUN apt-get update && apt-get install -y curl && apt-get clean

RUN useradd -ms /bin/bash frappe

# Make bench directories
RUN mkdir -p /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/apps/frappe

COPY build/frappe-socketio/package.json /home/frappe/frappe-bench/apps/frappe


# get socketio
RUN cd /home/frappe/frappe-bench/apps/frappe \
    && curl https://raw.githubusercontent.com/frappe/frappe/version-11/socketio.js \
        --output /home/frappe/frappe-bench/apps/frappe/socketio.js \
    && curl https://raw.githubusercontent.com/frappe/frappe/version-11/node_utils.js \
        --output /home/frappe/frappe-bench/apps/frappe/node_utils.js

RUN cd /home/frappe/frappe-bench/apps/frappe \
    && npm install --only=production \
    && node --version \
    && npm --version

COPY build/frappe-socketio/health.js /home/frappe/frappe-bench/apps/frappe/health.js
RUN chown -R frappe:frappe /home/frappe

# Setup docker-entrypoint
COPY build/frappe-socketio/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

WORKDIR /home/frappe/frappe-bench/sites

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
