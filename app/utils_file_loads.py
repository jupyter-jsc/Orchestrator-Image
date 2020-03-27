'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

import json

def image_name_to_image(imagename):
    with open('/etc/j4j/j4j_mount/j4j_orchestrator/image_name_to_image.json', 'r') as f:
        images = json.load(f)
    return images.get(imagename, imagename)

def get_j4j_orchestrator_token():
    with open('/etc/j4j/j4j_mount/j4j_token/orchestrator.token', 'r') as f:
        token = f.read().rstrip()
    return token

def get_j4j_tunnel_token():
    with open('/etc/j4j/j4j_mount/j4j_token/tunnel.token') as f:
        token = f.read().rstrip()
    return token

def get_j4j_worker_token():
    with open('/etc/j4j/j4j_mount/j4j_token/worker.token', 'r') as f:
        token = f.read().rstrip()
    return token

def get_jhubtoken():
    with open('/etc/j4j/j4j_mount/j4j_token/jhub.token', 'r') as f:
        token = f.read().rstrip()
    return token

def get_unity():
    with open('/etc/j4j/j4j_mount/j4j_common/unity.json', 'r') as f:
        unity = json.load(f)
    return unity

def get_unicore():
    with open('/etc/j4j/j4j_mount/j4j_common/unicore.json', 'r') as f:
        unicore_file = json.load(f)
    return unicore_file

def get_urls():
    with open('/etc/j4j/j4j_mount/j4j_common/urls.json', 'r') as f:
        urls = json.load(f)
    return urls

def get_resources():
    with open('/etc/j4j/j4j_mount/j4j_common/resources.json', 'r') as f:
        resources = json.load(f)
    return resources

def get_cron_info():
    with open('/etc/j4j/j4j_mount/j4j_common/cronjob.json', 'r') as f:
        cron = json.load(f)
    return cron

def get_hdfcloud():
    with open('/etc/j4j/j4j_mount/j4j_common/hdf_cloud.json', 'r') as f:
        ret = json.load(f)
    return ret

def get_docker_master_token():
    with open('/etc/j4j/j4j_mount/j4j_token/dockermaster.token', 'r') as f:
        token = f.read().rstrip()
    return token


