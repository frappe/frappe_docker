## Prerequisites

- [yq](https://mikefarah.gitbook.io/yq)
- [docker-compose](https://docs.docker.com/compose/)
- [docker swarm](https://docs.docker.com/engine/swarm/)

#### Generate setup for docker swarm

Generate the swarm compatible YAML,

```bash
docker-compose -f compose.yaml \
  -f overrides/compose.erpnext.yaml \
  -f overrides/compose.swarm.yaml \
  -f overrides/compose.https.yaml \
  config \
  | yq eval 'del(.services.*.depends_on) | del(.services.frontend.labels)' - \
  | yq eval '.services.proxy.command += "--providers.docker.swarmmode"' - > \
  ~/gitops/compose.yaml
```

In case you need to generate config for multiple benches. Install the proxy separately only once and generate stacks for each bench as follows:

```bash
# Setup Bench $BENCH_SUFFIX
export BENCH_SUFFIX=one
docker-compose -f compose.yaml \
  -f overrides/compose.erpnext.yaml \
  -f overrides/compose.swarm.yaml \
  config \
  | yq eval 'del(.services.*.depends_on) | del(.services.frontend.labels)' - \
  | sed "s|frontend|frontend-${BENCH_SUFFIX}|g" \
  | yq eval ".services.frontend-${BENCH_SUFFIX}.\"networks\"=[\"traefik-public\",\"default\"]" - \
  | yq eval ".\"networks\"={\"traefik-public\":{\"external\":true}}" - > \
  ~/gitops/compose-${BENCH_SUFFIX}.yaml
```

Commands explained:

- `docker-compose -f ... -f ... config`, this command generates the YAML based on the overrides
- `yq eval 'del(.services.*.depends_on) | del(.services.frontend.labels)'`, this command removes the `depends_on` from all services and `labels` from frontend generated from previous command.
- `yq eval '.services.proxy.command += "--providers.docker.swarmmode"'`, this command enables swarmmode for traefik proxy.
- `sed "s|frontend|frontend-${BENCH_SUFFIX}|g"`, this command replaces the service name `frontend` with `frontend-` and `BENCH_SUFFIX` provided.
- `yq eval ".services.frontend-${BENCH_SUFFIX}.\"networks\"=[\"traefik-public\",\"default\"]"`, this command attaches `traefik-public` and `default` network to frontend service.
- `yq eval ".\"networks\"={\"traefik-public\":{\"external\":true}}"`, this commands adds external network `traefik-public` to the stack

Notes:

- Set `BENCH_SUFFIX` to the stack name. the stack will be located at `~/gitops/compose-${BENCH_SUFFIX}.yaml`.
- `traefik-public` is assumed to be the network for traefik loadbalancer for swarm.
- Once the stack YAML is generated, you can edit it further for advance setup and commit it to your gitops

#### Site Operations

Refer [site operations documentation](./site-operations) to create new site, migrate site, drop site and perform other site operations.
