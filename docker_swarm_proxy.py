#!/bin/python3
import random
import string
import subprocess
import os
import docker
import time
import sys
import click
from typing import List

if len(sys.argv) >= 2:
    if sys.argv[1] == 'docker-cli-plugin-metadata':
      print("""
{
    "SchemaVersion": "0.1.0",
    "Vendor": "Martin Braun",
    "Version": "0.0.1",
    "ShortDescription": "Docker Swarm Proxy"
}
      """)
      exit(0)

if 'swarmproxy' in sys.argv:
  # we need to strip the first agument for click to work
  # if we run as a docker cli plugin
  sys.argv = sys.argv[:1]

def get_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for i in range(length))

random_str = get_random_string(32)

stack_name = f"docker_swarm_proxy_{random_str}"
network_name = stack_name
proxy_service_name = "srv"
proxy_shell_container_name = f"proxy_shell_{random_str}"

TEMPLATE = f"""
version: "3.8"

services:
  {proxy_service_name}:
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

@click.group()
def cli() -> None:
    pass

@click.group()
def service() -> None:
    """
    Docker Swarm Service Utilities
    """
    pass

@service.command('exec')
@click.option('-i', '--interactive', is_flag=True, show_default=True, default=False, help='Keep STDIN open even if not attached')
@click.option('-t', '--tty', is_flag=True, show_default=True, default=False, help='Allocate a pseudo-TTY')
@click.option('-u', '--user', help='Username or UID (format: "<name|uid>[:<group|gid>]")')
@click.argument('service')
@click.argument('command')
@click.argument('arg', nargs=-1)
def service_exec(
    interactive: bool,
    tty: bool,
    user: string,
    service: string,
    command: string,
    arg: List[str]
):
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

    service = get_service(service)
    
    running_tasks = get_running_tasks(service)
    if len(running_tasks) == 0:
        raise AssertionError(f"didn't find running task for service {service}")
    
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
      service = get_service(f'{stack_name}_{proxy_service_name}')
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
        
    interactive_str = '-i' if interactive else ''
    tty_str = '-t' if tty else ''
    user_str = user or ''

    docker_flags = [elem for elem in [interactive_str, tty_str] if elem != '']

    subprocess.run(
      [
        docker_binary, 
        "run", 
        "--env", f"PROXY_SERVICE_NAME={proxy_service_name}",
        "--env", f"CONTAINER_ID={container_id}",
        "--env", f"USER_FLAG={user_str}",
        "--env", f"IS_TTY={tty_str}",
        "--env", f"IS_INTERACTIVE={interactive_str}",
        "--env", f"NODE_ID_RUNNING_TASK={node_id_running_task}",
        "--name", proxy_shell_container_name,
        "--network", network_name,
        "--pull", "always",
        "--rm",
        "--entrypoint", "python3",
        *docker_flags,
        "ghcr.io/neuroforgede/docker-swarm-proxy/service-exec:master",
        "service_exec.py",
        command,
        *arg
      ],
      env={
        **os.environ,
      },
      cwd=os.getcwd(),
      check=True
    )
  finally:
    if needs_cleanup:
      # hack, ensure that the proxy container is dead and removed
      subprocess.run(
        [docker_binary, "kill", proxy_shell_container_name],
        env={
          **os.environ,
        },
        cwd=os.getcwd(),
        stdout=None,
        stderr=None,
        check=False,
        capture_output=True
      )
      # hack, ensure that the proxy container is dead and removed
      subprocess.run(
        [docker_binary, "rm", proxy_shell_container_name],
        env={
          **os.environ,
        },
        cwd=os.getcwd(),
        stdout=None,
        stderr=None,
        check=False,
        capture_output=True
      )

      # do the proper cleanup of the stack
      subprocess.run(
        [docker_binary, "stack", "rm", stack_name],
        env={
          **os.environ,
        },
        cwd=os.getcwd(),
        check=True
      )


cli.add_command(service)
if __name__ == '__main__':
  cli()