# docker-swarm-proxy

## Installation

Install into the swarm

```bash
docker stack deploy -c docker_swarm_proxy.yml docker_swarm_proxy
```

## Usage

Select any manager node in the swarm to connect to via SSH:

```bash
export DOCKER_HOST=<...>
```

Run any docker command, e.g. `docker ps`:

```bash
docker run --network docker_swarm_proxy --env TARGET_HOST=<target_hostname> --rm -it ghcr.io/neuroforgede/docker-swarm-proxy:master ps
```
