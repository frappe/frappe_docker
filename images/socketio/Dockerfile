FROM alpine/git as builder

ARG FRAPPE_VERSION
ARG FRAPPE_REPO=https://github.com/frappe/frappe
RUN apk add -U jq
RUN git clone --depth 1 -b ${FRAPPE_VERSION} ${FRAPPE_REPO} /opt/frappe
RUN jq --argjson dependencies "$(jq '.dependencies | INDEX( "express", "redis", "socket.io", "superagent" ) as $keep | \
    del( \
    . | objects | \
    .[ \
        keys_unsorted[] | \
        select( $keep[ . ] | not ) \
    ] \
    )' /opt/frappe/package.json)" '.dependencies = $dependencies | del(.scripts.prepare)' /opt/frappe/package.json > /opt/frappe/dependencies.json && \
    mv /opt/frappe/dependencies.json /opt/frappe/package.json

# NodeJS LTS
FROM node:18-alpine

RUN addgroup -S frappe \
    && adduser -S frappe -G frappe
USER frappe

WORKDIR /home/frappe/frappe-bench
RUN mkdir -p sites apps/frappe

COPY --chown=frappe:frappe --from=builder /opt/frappe/package.json /opt/frappe/socketio.js /opt/frappe/node_utils.js apps/frappe/

RUN cd apps/frappe \
    && npm install --omit=dev

WORKDIR /home/frappe/frappe-bench/sites

CMD [ "node", "/home/frappe/frappe-bench/apps/frappe/socketio.js" ]
