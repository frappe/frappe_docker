---
title: Advanced Setups
---

# Introduction

This document describes some advanced setups that may add additional features, performance improvements, or security
properties that are not present in the default setup. It is beyond the scope of this project to provide support for any
of these setups, and users are advised to ensure they fully understand the implications of using the following
suggestions in their deployment.

## Using Unix Sockets

A [Unix domain socket](https://wikipedia.org/wiki/Unix_domain_socket) can be used as the transport between your public
proxy and the frontend container. This can provide the following benefits:

1. The socket file can be configured with standard Unix file permissions, and additional ACL rules.
2. SELinux can be used to further restrict access to the socket file with custom policies.
3. Unix sockets have slightly lower overhead than a local TCP connection.

The value of the [`NGINX_LISTEN_PORT`](../02-setup/04-env-variables.md#frontend-nginx-configuration-inside-the-frontend-container)
environment variable is directly substituted into the internal Nginx server's [listen](https://nginx.org/en/docs/http/ngx_http_core_module.html#listen)
directive, which allows passing a `unix:/path/to/socket` value instead of a port value. Note that this may break some
compose overrides that strictly expect a port value here.

This can be combined with [systemd socket activation](https://www.freedesktop.org/software/systemd/man/latest/systemd.socket.html)
and [Podman Quadlets](https://docs.podman.io/en/latest/markdown/podman-systemd.unit.5.html). Refer to this [guide](https://github.com/eriksjolund/podman-nginx-socket-activation)
by Erik Sjölund to see how Nginx can be made to work with socket activation. Note that Nginx does not officially support
socket activation, and this setup relies on undocumented functionality in Nginx.
