FROM alpine/git

ARG GIT_REPO=https://github.com/frappe/frappe.git
ARG GIT_BRANCH=develop

RUN git clone ${GIT_REPO} /opt/frappe -b ${GIT_BRANCH} --depth 1

FROM node:buster-slim

# Add frappe user
RUN useradd -ms /bin/bash frappe

# Create bench directories and set ownership
RUN mkdir -p /home/frappe/frappe-bench/sites /home/frappe/frappe-bench/apps/frappe \
    && chown -R frappe:frappe /home/frappe

# Download socketio and purge curl package
COPY build/frappe-socketio/package.json /home/frappe/frappe-bench/apps/frappe
COPY --from=0 /opt/frappe/socketio.js /home/frappe/frappe-bench/apps/frappe/socketio.js
COPY --from=0 /opt/frappe/node_utils.js /home/frappe/frappe-bench/apps/frappe/node_utils.js

RUN cd /home/frappe/frappe-bench/apps/frappe \
    && npm install --only=production \
    && node --version \
    && npm --version

# Setup docker-entrypoint
COPY build/frappe-socketio/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
RUN ln -s /usr/local/bin/docker-entrypoint.sh / # backwards compat

USER frappe

WORKDIR /home/frappe/frappe-bench/sites

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
