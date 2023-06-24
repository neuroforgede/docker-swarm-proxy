import docker
import dns.resolver
import os
import sys

PROXY_SERVICE_NAME = os.environ['PROXY_SERVICE_NAME']
CONTAINER_ID = os.environ['CONTAINER_ID']
NODE_ID_RUNNING_TASK = os.environ['NODE_ID_RUNNING_TASK']

USER_FLAG = os.getenv('USER_FLAG', '')
IS_TTY = os.getenv('IS_TTY', '')
IS_INTERACTIVE = os.getenv('IS_INTERACTIVE')

FLAGS = []

if USER_FLAG != '':
    FLAGS.append('-u')
    FLAGS.append(USER_FLAG)

if IS_TTY != '':
    FLAGS.append('-t')

if IS_INTERACTIVE != '':
    FLAGS.append('-i')

print(sys.argv)

answer = dns.resolver.resolve(f'tasks.{PROXY_SERVICE_NAME}', 'A')
for rdata in answer:    
    client = docker.DockerClient(base_url=f'tcp://{rdata.address}:2375')
    info = client.info()

    node_id = info["Swarm"]["NodeID"]
    if node_id == NODE_ID_RUNNING_TASK:
        os.execvpe('/usr/local/bin/docker', ['/usr/local/bin/docker', 'exec', *FLAGS, CONTAINER_ID, *sys.argv[1:]], env={
            'DOCKER_HOST': 'tcp://' + str(rdata.address) + ':2375'
        })

print("did not find node " + NODE_ID_RUNNING_TASK, file=sys.stderr)
exit(1)