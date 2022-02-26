FROM alpine/git as builder

ARG FRAPPE_VERSION
RUN git clone --depth 1 -b ${FRAPPE_VERSION} https://github.com/frappe/frappe /opt/frappe


FROM node:17-alpine

RUN addgroup -S frappe \
    && adduser -S frappe -G frappe
USER frappe

WORKDIR /home/frappe/frappe-bench
RUN mkdir -p sites apps/frappe

COPY --from=builder /opt/frappe/socketio.js /opt/frappe/node_utils.js apps/frappe/
COPY package.json apps/frappe/

RUN cd apps/frappe \
    && npm install

WORKDIR /home/frappe/frappe-bench/sites

CMD [ "node", "/home/frappe/frappe-bench/apps/frappe/socketio.js" ]
