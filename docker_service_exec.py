import random
import string
import subprocess
import os
import docker
import time
import sys

if sys.argv[1] == 'docker-cli-plugin-metadata':
    print(f"""
{
     "SchemaVersion": "0.1.0",
     "Vendor": "Martin Braun",
     "Version": "0.0.1",
     "ShortDescription": "Docker Swarm Exec"
}         
""")
    exit(0)

target_service = 'vibrant_bell'
cmd = '/bin/bash'

def get_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

random_str = get_random_string(32)

stack_name = f"docker_swarm_proxy_{random_str}"
network_name = stack_name
service_name = "srv"

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

def get_running_tasks(service):
    return [
        task
        for task in service.tasks()
        if  "Spec" in task 
        and "DesiredState" in task
        and task["DesiredState"] == "running"
        and "Status" in task
        and "State" in task["Status"]
        and task["Status"]["State"] == "running"
    ]


def get_service(name):
    services = from_env.services.list(filters={"name": name})
    if len(services) != 1:
        raise AssertionError(f'did not find exactly one service with name {name}')
    return services[0]

needs_cleanup = False
try:
    from_env = docker.from_env()

    service = get_service(target_service)
    
    running_tasks = get_running_tasks(service)
    if len(running_tasks) == 0:
        raise AssertionError(f"didn't find running task for service {target_service}")
    
    running_task = running_tasks[0]
    node_id_running_task = running_task["NodeID"]
    container_id = running_task["Status"]["ContainerStatus"]["ContainerID"]

    # TODO: dont deploy the service to all nodes, but instead only
    # to the one we care about that is running the task
    needs_cleanup = True
    subprocess.run(
        [docker_binary, "stack", "deploy", "-c", "-", stack_name],
        env={
            **os.environ,
        },
        cwd=os.getcwd(),
        input=TEMPLATE.encode('utf-8'),
        check=True
    )

    while True:
        # wait for proxy service to be there
        service = get_service(f'{stack_name}_{service_name}')
        all_tasks = service.tasks()
        desired_running = [
            task
            for task in all_tasks
            if  "Spec" in task 
            and "DesiredState" in task
            and task["DesiredState"] == "running"
        ]
        actually_running = [
            task
            for task in desired_running
            if "Status" in task
            and "State" in task["Status"]
            and task["Status"]["State"] == "running"
        ]
        if len(desired_running) != len(actually_running):
            time.sleep(1)
        else:
            break

    subprocess.run(
        [docker_binary, "run", "--network", network_name, "--rm", "-it", "--entrypoint", "/bin/sh", "ghcr.io/neuroforgede/docker-swarm-proxy/docker:master", "-c", f"""
cat > script.py <<EOF
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
        os.execvpe('/usr/local/bin/docker', ['/usr/local/bin/docker', 'exec', '-it', '{container_id}', '{cmd}'], env={'{'}
            'DOCKER_HOST': 'tcp://' + str(rdata.address) + ':2375'
        {'}'})
EOF
exec python3 script.py
        """],
        env={
            **os.environ,
        },
        cwd=os.getcwd(),
        check=True
    )
finally:
    if needs_cleanup:
        subprocess.run(
            [docker_binary, "stack", "rm", stack_name],
            env={
                **os.environ,
            },
            cwd=os.getcwd(),
            check=True
        )
