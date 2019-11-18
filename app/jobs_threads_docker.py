import uuid
import os

from time import sleep

from app import utils_hub_update, utils_db, utils_file_loads


def check_docker_status(app_logger, uuidcode, app_urls, app_database, servername, escapedusername, jhubtoken):
    uuidcode2 = uuid.uuid4().hex
    path1 = '{}/{}'.format(app_urls.get('docker', {}).get('check_folder'), uuidcode2)
    path2 = '{}/{}'.format(app_urls.get('docker', {}).get('check_results_folder'), uuidcode2)
    # We create a file in a mounted directory.
    # An inotifywait process is looking for new files in this directory (running on the VM for User-Containers)
    app_logger.debug("{} - Create File {}".format(uuidcode, path1))
    s_email, s_servername = servername.split(':')
    s_output = "{};{}".format(s_email.replace('@', '_at_'), s_servername)
    with open(path1, 'w') as f:
        f.write(s_output)
    # now we wait for an answer of this inotifywait process. It will 'answer' with a new file in the second directory.
    sleeping = [0.5, 0.5, 1, 2, 2, 4, 5, 10, 20, 30]
    for i in range(0, 10):
        sleep(sleeping[i])
        app_logger.debug("{} - Looking for file {}".format(uuidcode, path2))
        if os.path.isfile(path2):
            # The file exists (so the check from the script outside of this container is finished)
            try:
                with open(path2, 'r') as f:
                    result = f.read()
                os.remove(path2) # delete the file, we don't need it anymore
                app_logger.debug("{} - Input of file {}: {}".format(uuidcode, path2, result))
                if result.lower().strip() == 'true':
                    # Inform JupyterHub that the JupyterLab is still running
                    utils_hub_update.status(app_logger,
                                            uuidcode,
                                            app_urls.get('hub', {}).get('url_proxy_route'),
                                            app_urls.get('hub', {}).get('url_status'),
                                            jhubtoken,
                                            'running',
                                            escapedusername,
                                            servername)
                    return
                else:
                    # Input is not true, so the Docker Container has stopped
                    utils_hub_update.status(app_logger,
                                            uuidcode,
                                            app_urls.get('hub', {}).get('url_proxy_route'),
                                            app_urls.get('hub', {}).get('url_status'),
                                            jhubtoken,
                                            'stopped',
                                            escapedusername,
                                            servername)
                    utils_db.remove_entrys(app_logger,
                                           uuidcode,
                                           servername,
                                           app_database)
                    return
            except:
                # The read failed, maybe the script is still writing into the file at this exact moment? Try again in the next run
                app_logger.exception("{} - Tried to read input of file {}. Failed".format(uuidcode, path2))
                continue
    # We tried for so long, we got no answer, so we see it as failed
    utils_hub_update.status(app_logger,
                            uuidcode,
                            app_urls.get('hub', {}).get('url_proxy_route'),
                            app_urls.get('hub', {}).get('url_status'),
                            jhubtoken,
                            'stopped',
                            escapedusername,
                            servername)
    utils_db.remove_entrys(app_logger,
                           uuidcode,
                           servername,
                           app_database)

def start_docker(app_logger, uuidcode, app_urls, app_database, servername, escapedusername, jhubtoken, port, account, environment):
    servername_at = servername.replace('@', '_at_')
    email = servername_at.split(':')[0]
    servername_short = servername_at.split(':')[1]
    name = servername_at.replace(':', '_')
    # map chosen image to actual image name
    dockerimage = utils_file_loads.image_name_to_image(account)
    # get hpc accounts of the user, so he can (eventually) use the hpc mount feature
    hpcaccounts = get_hpc_accounts(app_logger,
                                   uuidcode,
                                   environment.get('hpcaccounts', []))
    s_output = "{};{};{};{};{};{};{};{};{};{};{};{}".format(email,
                                                            name,
                                                            servername_short,
                                                            jhubtoken,
                                                            port,
                                                            dockerimage,
                                                            environment.get('JUPYTERHUB_CLIENT_ID'),
                                                            environment.get('JUPYTERHUB_SERVICE_PREFIX'),
                                                            environment.get('JUPYTERHUB_USER'),
                                                            environment.get('JUPYTERHUB_BASE_URL', '/'),
                                                            environment.get('JUPYTERHUB_API_URL', 'http://j4j_proxy:8000/hub/api'),
                                                            hpcaccounts)

    app_logger.debug("{} - Add server to database: {}".format(uuidcode, servername_at))
    utils_db.create_entry_docker(app_logger,
                                 uuidcode,
                                 app_database,
                                 servername,
                                 jhubtoken,
                                 port,
                                 dockerimage)

    app_logger.trace("{} - Write: {} to file {}/{}".format(uuidcode, s_output, app_urls.get('docker', {}).get('create_folder'), uuidcode))
    with open('{}/{}'.format(app_urls.get('docker', {}).get('create_folder'), uuidcode), 'w') as f:
        f.write(s_output)

    # We wait up to 30 seconds if the container is spawned correctly. If that is not the case, JupyterHub will give up anyway.
    for i in range(0,10):  # @UnusedVariable
        uuidcode2 = uuid.uuid4().hex
        path1 = '{}/{}'.format(app_urls.get('docker', {}).get('check_folder'), uuidcode2)
        path2 = '{}/{}'.format(app_urls.get('docker', {}).get('check_results_folder'), uuidcode2)
        # We create a file in a mounted directory.
        # An inotifywait process is looking for new files in this directory (running on the VM for User-Containers)
        app_logger.debug("{} - Create File {}".format(uuidcode, path1))
        s_email, s_servername = servername.split(':')
        s_output = "{};{}".format(s_email.replace('@', '_at_'), s_servername)
        with open(path1, 'w') as f:
            f.write(s_output)
        # now we wait for an answer of this inotifywait process. It will 'answer' with a new file in the second directory.
        sleeping = [0.5, 0.5, 1, 2, 2, 4, 5, 10, 20, 30]
        for j in range(0, 10):
            sleep(sleeping[j])
            app_logger.debug("{} - Looking for file {}".format(uuidcode, path2))
            if os.path.isfile(path2):
                # The file exists (so the check from the script outside of this container is finished)
                try:
                    with open(path2, 'r') as f:
                        result = f.read()
                    os.remove(path2) # delete the file, we don't need it anymore
                    app_logger.debug("{} - Input of file {}: {}".format(uuidcode, path2, result))
                    if result.lower().strip() == 'true':
                        utils_hub_update.status(app_logger,
                                                uuidcode,
                                                app_urls.get('hub', {}).get('url_proxy_route'),
                                                app_urls.get('hub', {}).get('url_status'),
                                                jhubtoken,
                                                'running',
                                                escapedusername,
                                                servername)
                        # set spawning to False (it will be set True when it's created)
                        utils_db.set_spawning(app_logger,
                                              uuidcode,
                                              servername,
                                              app_database,
                                              'False')
                        return
                    else:
                        # The container is not started yet. So let's check again
                        # We got out of the for j in range(0,10) loop, so we're back again in the for i in range(0,10) loop (j != i) 
                        break
                except:
                    # The read failed, maybe the script is still writing into the file at this exact moment? Try again in the next run
                    app_logger.exception("{} - Tried to read input of file {}. Failed".format(uuidcode, path2))
                    continue
        sleep(3)
    # We only reach this point, if the Container is not started properly (or our check failed). 
    # We set spawning to False anyway, so that the regular Check can decide what will happen with this Server
    # set spawning to False (it will be set True when it's created)
    utils_db.set_spawning(app_logger,
                          uuidcode,
                          servername,
                          app_database,
                          'False')
    return

def delete_docker(app_logger, uuidcode, servername, docker_delete_folder):
    app_logger.trace("{} - Try to delete docker container named: {}".format(uuidcode, servername))
    servername_at = servername.replace('@', '_at_')
    email = servername_at.split(':')[0]
    servername_short = servername_at.split(':')[1]
    name = servername_at.replace(':', '_')
    s_output = "{};{};{}".format(name, servername_short, email)
    with open('{}/{}.txt'.format(docker_delete_folder, name), 'w') as f:
        f.write(s_output)

def get_hpc_accounts(app_logger, uuidcode, hpcaccounts_list):
    ret = ""
    if hpcaccounts_list == None:
        app_logger.debug("{} - User has no HPC accounts".format(uuidcode))
        return ""
    app_logger.debug("{} - Try to rearrange hpc accounts: {}".format(uuidcode, hpcaccounts_list))
    user_accs = {}
    try:
        for line in hpcaccounts_list:
            account, system_partition, project, mail = line.split(',')  # @UnusedVariable
            system = system_partition.split('_')[0]
            if system.lower() not in user_accs.keys():
                user_accs[system.lower()] = []
            if account.lower() not in user_accs[system.lower()]:
                user_accs[system.lower()].append(account.lower())
        app_logger.debug("{} - user_accs: {}".format(uuidcode, user_accs))
        for system, names in user_accs.items():
            if ret != "":
                ret += "_"
            ret += "{}:{}".format(system.upper(), ','.join(names))
        app_logger.debug("{} - Return: {}".format(uuidcode, ret))
        return ret
    except:
        app_logger.exception("{} - Could not rearrange hpcaccounts".format(uuidcode))
        return ""
