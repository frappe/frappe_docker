FROM alpine/git as builder

ARG GIT_REPO=https://github.com/frappe/frappe.git
ARG GIT_BRANCH=develop

RUN git clone --depth 1 -b ${GIT_BRANCH} ${GIT_REPO} /opt/frappe 

FROM node:bullseye-slim

# Add frappe user
RUN useradd -ms /bin/bash frappe
WORKDIR /home/frappe/frappe-bench

# Create bench directories and set ownership
RUN mkdir -p sites apps/frappe \
    && chown -R frappe:frappe /home/frappe

# Download socketio
COPY build/frappe-socketio/package.json apps/frappe
COPY --from=builder /opt/frappe/socketio.js apps/frappe/socketio.js
COPY --from=builder /opt/frappe/node_utils.js apps/frappe/node_utils.js

RUN cd apps/frappe \
    && npm install --only=prod

# Setup docker-entrypoint
COPY build/frappe-socketio/docker-entrypoint.sh /usr/local/bin/docker-entrypoint.sh
# backwards compat
RUN ln -s /usr/local/bin/docker-entrypoint.sh /

USER frappe
WORKDIR /home/frappe/frappe-bench/sites

ENTRYPOINT ["docker-entrypoint.sh"]
CMD ["start"]
