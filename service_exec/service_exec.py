import docker
import dns.resolver
import os
import sys

from_env = docker.from_env()
for service in from_env.services.list():
    print(service.tasks())

TARGET_HOST = os.environ['TARGET_HOST']

answer = dns.resolver.resolve('tasks.docker_swarm_proxy', 'A')
for rdata in answer:    
    client = docker.DockerClient(base_url=f'tcp://{rdata.address}:2375')
    info = client.info()

    if info['Name'] == TARGET_HOST:
        new_argv = [*sys.argv]
        new_argv[0] = '/usr/local/bin/docker'
        os.execvpe('/usr/local/bin/docker', sys.argv, {
            'DOCKER_HOST': f'tcp://{rdata.address}:2375'
        })
