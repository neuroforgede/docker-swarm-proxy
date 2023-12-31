# docker-swarm-proxy

What if you wanted a docker exec, but for Docker swarm?

A problem with Docker Swarm and automation with it has been that you can't directly exec into any service from the command line. There exist some workarounds to achieve this behaviour, but in the end you want something similar and as convenient as `docker exec` but for services.

![grafik](https://github.com/neuroforgede/docker-swarm-proxy/assets/719760/e40aae96-1b0f-4193-8f7e-1054b5db6a6e)

## Installation

### Prerequisites

Install docker-py and click:

```bash
pip3 install docker
pip3 install click
```

Install the plugin your docker cli (from github)

```bash
rm ~/.docker/cli-plugins/docker-swarmproxy
curl -L https://raw.githubusercontent.com/neuroforgede/docker-swarm-proxy/master/docker_swarm_proxy.py -o ~/.docker/cli-plugins/docker-swarmproxy
chmod +x ~/.docker/cli-plugins/docker-swarmproxy
```

Or copy from a local copy of this repo:

```bash
cp docker_swarm_proxy.py ~/.docker/cli-plugins/docker-swarmproxy
chmod +x ~/.docker/cli-plugins/docker-swarmproxy
```

## Usage

NOTE: For remote clusters, only usage of the DOCKER_HOST environment variable is supported. Usage of Docker Contexts for switching environments is not supported. For remote clusters we strongly advise against exposing the TCP socket directly. Instead use the SSH tunneling support of docker cli as described [here](https://docs.docker.com/engine/security/protect-access/).

### Exec into a running service

```bash
docker swarmproxy service exec -it vibrant_bell bash
```

See all available options:

```bash
docker swarmproxy service exec --help
```

### Use `-` in the command

Since swarmproxy uses click under the hood for argument parsing, you have to use `--` before any exec command.

This will not work:

```bash
docker swarmproxy service exec -it vibrant_bell bash -c 'echo hello'
```

This will work:

```bash
docker swarmproxy service exec -it vibrant_bell -- bash -c 'echo hello'
```
