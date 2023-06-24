import random
import string
import subprocess
import os
import docker

def get_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

random_str = get_random_string(32)

stack_name = f"docker_swarm_proxy_{random_str}"
network_name = stack_name
service_name = "srv"

cmd = '/bin/bash'

TEMPLATE = f"""
version: "3.8"

services:
  {service_name}:
    image: tecnativa/docker-socket-proxy
    volumes:
        - /var/run/docker.sock:/var/run/docker.sock
    networks:
      docker_swarm_proxy:
    environment:
      CONTAINERS: 1
      SERVICES: 1
      SWARM: 1
      NODES: 1
      NETWORKS: 1
      TASKS: 1
      VERSION: 1

      AUTH: 1
      SECRETS: 1
      POST: 1
      BUILD: 1
      COMMIT: 1
      CONFIGS: 1
      DISTRIBUTION: 1
      EXEC: 1
      GRPC: 1
      IMAGES: 1
      INFO: 1
      PLUGINS: 1
      SESSION: 1
      SYSTEM: 1
      VOLUMES: 1
    deploy:
      mode: global

networks:
  docker_swarm_proxy:
    driver: overlay
    attachable: true
    name: {network_name}
    driver_opts:
      encrypted: ""
      com.docker.network.driver.mtu: "1350"
"""


if os.path.isfile("/bin/docker"):
    docker_binary = "/bin/docker"
elif os.path.isfile("/usr/bin/docker"):
    docker_binary = "/usr/bin/docker"


try:
    subprocess.run(
        [docker_binary, "stack", "deploy", "-c", "-", stack_name],
        env={
            **os.environ,
        },
        cwd=os.getcwd(),
        input=TEMPLATE.encode('utf-8'),
        check=True
    )

    from_env = docker.from_env()
    target_service = 'vibrant_bell'
    services = from_env.services.list(filters={"name": target_service})
    if len(services) != 1:
        raise AssertionError(f'did not find exactly one service with name {target_service}')
    service = services[0]

    import time
    time.sleep(10)
    
    running_tasks = [
        task
        for task in service.tasks()
        if  "Spec" in task 
        and "DesiredState" in task
        and task["DesiredState"] == "running"
        and "Status" in task
        and "State" in task["Status"]
        and task["Status"]["State"] == "running"
    ]
    if len(running_tasks) == 0:
        raise AssertionError(f"didn't find running task for service {target_service}")
    
    running_task = running_tasks[0]
    node_id_running_task = running_task["NodeID"]
    container_id = running_task["Status"]["ContainerStatus"]["ContainerID"]

    subprocess.run(
        [docker_binary, "run", "--network", network_name, "--rm", "-it", "--entrypoint", "/bin/sh", "ghcr.io/neuroforgede/docker-swarm-proxy/docker:master", "-c", f"""
exec python3 <<EOF
import docker
import dns.resolver
import os
import sys
import subprocess

answer = dns.resolver.resolve('tasks.{service_name}', 'A')
for rdata in answer:    
    client = docker.DockerClient(base_url=f'tcp://{'{'}rdata.address{'}'}:2375')
    info = client.info()

    node_id = info["Swarm"]["NodeID"]
    if node_id == "{node_id_running_task}":
        subprocess.check_call(['/usr/local/bin/docker', 'exec', '-it', '{container_id}', '{cmd}'], env={'{'}
            'DOCKER_HOST': 'tcp://' + str(rdata.address) + ':2375'
        {'}'})
        exit(0)
EOF
        """],
        env={
            **os.environ,
        },
        cwd=os.getcwd(),
        check=True
    )
finally:
    subprocess.run(
        [docker_binary, "stack", "rm", stack_name],
        env={
            **os.environ,
        },
        cwd=os.getcwd(),
        check=True
    )
