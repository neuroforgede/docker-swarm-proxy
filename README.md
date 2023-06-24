# docker-swarm-proxy

What if you wanted a docker exec, but for Docker swarm?

This project allows you to control any docker engine in the swarm from a manager (or your local computer if you use SSH proxying).

![grafik](https://github.com/neuroforgede/docker-swarm-proxy/assets/719760/33294423-a874-47ac-86c9-529c39b5f78b)

## Installation

Install to your docker cli

```bash
curl https://raw.githubusercontent.com/neuroforgede/docker-swarm-proxy/master/docker_swarm_proxy.py -o ~/.docker/cli-plugins/docker-swarmproxy
chmod +x ~/.docker/cli-plugins/docker-swarmproxy
```