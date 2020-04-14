'''
Created on May 13, 2019

@author: Tim Kreuzer
'''

from app import jobs_threads_docker, jobs_threads_worker, utils_common
from app import utils_db
from app import utils_hub_update

def get(app_logger, uuidcode, request_headers, app_urls, app_database):
    try:
        app_logger.trace("uuidcode={} - Begin of get thread.".format(uuidcode))
        # Check if the server is still spawning.
        spawning = utils_db.get_spawning(app_logger,
                                         uuidcode,
                                         request_headers.get('servername', '<no_servername>'),
                                         app_database)
        if len(spawning) == 0 or spawning[0]:
            app_logger.debug("uuidcode={} - Do nothing. userserver={} is still spawning so we need no update".format(uuidcode, request_headers.get('servername', '<no_servername>')))
            return

        # Check if another get call is already running for this servername
        skip = utils_db.get_skip(app_logger,
                                 uuidcode,
                                 request_headers.get('servername', '<no_servername>'),
                                 app_database)
        if len(skip) == 0 or skip[0]:
            app_logger.debug("uuidcode={} - Do nothing. userserver={} is already checked. Skip it.".format(uuidcode, request_headers.get('servername', '<no_servername>')))
            return

        try:
            # Get OAuth tokens from JupyterHub
            request_headers['accesstoken'], request_headers['refreshtoken'], request_headers['expire'] = \
            utils_hub_update.get_tokens(app_logger,
                                        uuidcode,
                                        app_urls.get('hub', {}).get('url_proxy_route'),
                                        app_urls.get('hub', {}).get('url_token'),
                                        request_headers.get('jhubtoken', '<no_jhubtoken>'),
                                        request_headers.get('escapedusername'),
                                        request_headers.get('servername'))

        except:
            app_logger.error("uuidcode={} - Could not get token from JupyterHub".format(uuidcode))
            return

        # Get stored information for all server with this name (should be one) in database
        infos = utils_db.get_entry_infos(app_logger,
                                         uuidcode,
                                         request_headers.get('servername'),
                                         app_database)
        app_logger.trace("uuidcode={} - Result of get_entry_infos: {}".format(uuidcode, infos))

        if len(infos) == 0:
            # We don't know this server (yet). This usually happens when we're starting it right 
            # now and the cron job wants to check the status. So just do nothing
            app_logger.debug("uuidcode={} - Len(infos) == 0, but since this is the cronjob, we just do nothing".format(uuidcode))
            return

        if len(infos) > 1:
            # should not happen. Let's inform an admin via mail
            app_logger.error("uuidcode={} - Found multiple Server with the servername {}: {}".format(uuidcode, request_headers.get('servername'), infos))
            return

        info = infos[0]
        # Block this server for other calls (If a call takes more than 30 seconds, we would have multiple checks for the same server)
        utils_db.set_skip(app_logger,
                          uuidcode,
                          request_headers.get('servername'),
                          app_database,
                          'True')
        try:
            if info.get('system').lower() == "docker" or infos.get('system') == "HDF-Cloud":
                running = jobs_threads_docker.check_docker_status_new(app_logger,
                                                                      uuidcode,
                                                                      request_headers.get('servername'))
                if running:
                    # Inform JupyterHub that the JupyterLab is still running
                    utils_hub_update.status(app_logger,
                                            uuidcode,
                                            app_urls.get('hub', {}).get('url_proxy_route'),
                                            app_urls.get('hub', {}).get('url_status'),
                                            info.get('jhubtoken'),
                                            'running',
                                            request_headers.get('escapedusername'),
                                            request_headers.get('servername'))
                else:
                    # Input is not true, so the Docker Container has stopped
                    utils_hub_update.status(app_logger,
                                            uuidcode,
                                            app_urls.get('hub', {}).get('url_proxy_route'),
                                            app_urls.get('hub', {}).get('url_status'),
                                            info.get('jhubtoken'),
                                            'stopped',
                                            request_headers.get('escapedusername'),
                                            request_headers.get('servername'))
                    utils_db.remove_entrys(app_logger,
                                           uuidcode,
                                           request_headers.get('servername'),
                                           app_database)
                    
                # Unblock this server for other calls
                utils_db.set_skip(app_logger,
                                  uuidcode,
                                  request_headers.get('servername'),
                                  app_database,
                                  'False')
            else:
                # Let's J4J_Worker do the work. We just call it.
                jobs_threads_worker.check_unicore_job_status(app_logger,
                                                             uuidcode,
                                                             app_urls,
                                                             app_database,
                                                             request_headers,
                                                             request_headers.get('escapedusername'),
                                                             request_headers.get('servername'),
                                                             info)
        except:
            app_logger.exception("Could not check status")
            # Unblock this server for other calls
            utils_db.set_skip(app_logger,
                              uuidcode,
                              request_headers.get('servername'),
                              app_database,
                              'False')
        
    except:
        app_logger.exception("Unexpected error. Bugfix required")
    return

def post(app_logger, uuidcode, request_headers, request_json, app_urls, app_database):
    try:
        app_logger.trace("uuidcode={} - Begin of post thread.".format(uuidcode))
        if request_json.get('system').lower() == 'docker' or request_json.get('system') == "HDF-Cloud":
            running = jobs_threads_docker.start_docker_new(app_logger,
                                                           uuidcode,
                                                           app_database,
                                                           request_headers.get('servername'),
                                                           request_json.get('port'),
                                                           request_json.get('service'),
                                                           request_json.get('dashboard'),
                                                           request_headers.get('account'),
                                                           request_json.get('Environment', {}),
                                                           request_headers.get('jhubtoken'),
                                                           app_urls.get('tunnel', {}).get('url_tunnel'),
                                                           app_urls.get('tunnel', {}).get('url_remote'))
            if running:
                utils_hub_update.status(app_logger,
                                        uuidcode,
                                        app_urls.get('hub', {}).get('url_proxy_route'),
                                        app_urls.get('hub', {}).get('url_status'),
                                        request_headers.get('jhubtoken'),
                                        'running',
                                        request_headers.get('escapedusername'),
                                        request_headers.get('servername'))
            else:
                utils_hub_update.cancel(app_logger,
                                        uuidcode,
                                        app_urls.get('hub', {}).get('url_proxy_route'),
                                        app_urls.get('hub', {}).get('url_cancel'),
                                        request_headers.get('jhubtoken'),
                                        "Could not start. An Administrator is informed.",
                                        request_headers.get('escapedusername'),
                                        request_headers.get('servername'))
            # set spawning to False (it will be set True when it's created)
            utils_db.set_spawning(app_logger,
                                  uuidcode,
                                  request_headers.get('servername'),
                                  app_database,
                                  'False')
        else:
            jobs_threads_worker.start_unicore_job(app_logger,
                                                  uuidcode,
                                                  request_headers,
                                                  request_json,
                                                  app_urls,
                                                  app_database)
    except:
        app_logger.exception("Jobs_Threads failed: Bugfix required")
    return

def delete(app_logger, uuidcode, request_headers, app_urls, app_database):
    app_logger.trace("uuidcode={} - Begin of delete thread.".format(uuidcode))
    if not request_headers.get('servername'):
        app_logger.warning("uuidcode={} - No servername. Headers: {}".format(uuidcode, utils_common.remove_secret(request_headers)))
        return

    servers = utils_db.get_entry_servername(app_logger,
                                            uuidcode,
                                            request_headers.get('servername'),
                                            app_database)
    # nothing to delete
    if len(servers) == 0:
        return {}

    # remove entrys
    utils_db.remove_entrys(app_logger,
                           uuidcode,
                           request_headers.get('servername'),
                           app_database)

    headers = {}
    delete_header = {}
    for server in servers:
        docker = False
        try:
            system, kernelurl, filedir, port, account, project = server
            if system.lower() == "docker" or system == "HDF-Cloud":
                jobs_threads_docker.delete_docker_new(app_logger,
                                                      uuidcode,
                                                      request_headers.get('servername'),
                                                      app_urls)
                continue
            else:
                headers, delete_header = jobs_threads_worker.delete_job(app_logger,
                                                                        uuidcode,
                                                                        request_headers,
                                                                        delete_header,
                                                                        app_urls,
                                                                        system,
                                                                        kernelurl,
                                                                        filedir,
                                                                        port,
                                                                        account,
                                                                        project)
        except:
            if docker:
                app_logger.exception("uuidcode={} - Could not delete docker container".format(uuidcode))
            else:
                app_logger.exception("uuidcode={} - J4J_Worker communication failed. {}".format(uuidcode, server))

    return headers
