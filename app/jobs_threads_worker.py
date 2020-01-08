import socket

from app import jobs_threads_worker_utils, utils_hub_update, utils_common, jobs_threads, utils_db,\
    utils_file_loads

def check_unicore_job_status(app_logger, uuidcode, app_urls, app_database, request_headers, escapedusername, servername, server_info):
    try:
        app_logger.trace("{} - Call Create_get_header with: {} {} {} {} {}".format(uuidcode, request_headers, app_urls.get('hub', {}).get('url_proxy_route'), app_urls.get('hub', {}).get('url_token'), escapedusername, servername))
        worker_header = jobs_threads_worker_utils.create_get_header(app_logger,
                                                                    uuidcode,
                                                                    request_headers,
                                                                    app_urls.get('hub', {}).get('url_proxy_route'),
                                                                    app_urls.get('hub', {}).get('url_token'),
                                                                    escapedusername,
                                                                    servername,
                                                                    app_database)
    except:
        app_logger.exception("{} - Could not create Header. Send Cancel to JupyterHub and stop function. {} {}".format(uuidcode, utils_common.remove_secret(request_headers), app_urls.get('hub', {}).get('url_token')))
        utils_db.set_skip(app_logger,
                          uuidcode,
                          request_headers.get('servername'),
                          app_database,
                          'False')
        if server_info.get('system', None):
            error_msg = "A mandatory backend service for {} had a problem. An administrator is informed".format(server_info.get('system'))
        else:
            error_msg = "A mandatory backend service had a problem. An administrator is informed"
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get("jhubtoken"),
                                error_msg,
                                escapedusername,
                                servername)
        return
    try:
        # call worker get (fire and forget)
        worker_header['kernelurl'] = server_info.get('kernelurl')
        worker_header['filedir'] = server_info.get('filedir')
        worker_header['system'] = server_info.get('system')
        worker_header['port'] = server_info.get('port')
        worker_header['account'] = server_info.get('account')
        worker_header['project'] = server_info.get('project')
        worker_header['jhubtoken'] = server_info.get('jhubtoken')
        worker_header['spawning'] = server_info.get('spawning')
    
        method = "GET"
        method_args = {"url": app_urls.get('worker', {}).get('url_jobs'),
                       "headers":worker_header,
                       "certificate": False,
                       "fire_and_forget": True}
        app_logger.info("{} - Get J4J_Worker. Kernel_url: {}".format(uuidcode, worker_header['kernelurl']))
        jobs_threads_worker_utils.communicate(app_logger,
                                              uuidcode,
                                              method,
                                              method_args)

    except:
        utils_db.set_skip(app_logger,
                          uuidcode,
                          request_headers.get('servername'),
                          app_database,
                          'False')
        app_logger.exception("{} - J4J_Worker communication failed. {} {}".format(uuidcode, method, utils_common.remove_secret(method_args)))


def start_unicore_job(app_logger, uuidcode, request_headers, request_json, app_urls, app_database):
    # Delete all server with this name (there should be none, but better safe than sorry)
    j4j_worker_response_header = jobs_threads.delete(app_logger,
                                                     uuidcode,
                                                     request_headers,
                                                     app_urls,
                                                     app_database)
    # All duplicated servers are deleted from the database and stopped
    app_logger.trace('{} - J4J_Worker_response_header: {}'.format(uuidcode, j4j_worker_response_header))
    try:
        j4j_worker_header = jobs_threads_worker_utils.create_header(app_logger,
                                                                    uuidcode,
                                                                    request_headers,
                                                                    app_urls.get('hub', {}).get('url_proxy_route'),
                                                                    app_urls.get('hub', {}).get('url_token'),
                                                                    request_headers.get('escapedusername'),
                                                                    request_headers.get('servername'),
                                                                    app_database)
    except:
        app_logger.exception("{} - Could not create Header. Send Cancel to JupyterHub and stop function. {} {}".format(uuidcode, utils_common.remove_secret(request_headers), app_urls.get('hub', {}).get('url_token')))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get("jhubtoken"),
                                "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system')),
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        return
    # update with Infos of j4j_worker delete
    if 'accesstoken' in j4j_worker_response_header:
        j4j_worker_header['accesstoken'] = j4j_worker_response_header['accesstoken']
        j4j_worker_header['expire'] = j4j_worker_response_header['expire']
        utils_hub_update.token(app_logger,
                               uuidcode,
                               app_urls.get('hub', {}).get('url_proxy_route'),
                               app_urls.get('hub', {}).get('url_token'),
                               request_headers['jhubtoken'],
                               j4j_worker_response_header['accesstoken'],
                               j4j_worker_response_header['expire'],
                               request_headers.get('escapedusername'),
                               request_headers.get('servername'))

    if 'session' in j4j_worker_response_header:
        j4j_worker_header['X-UNICORE-SecuritySession'] = j4j_worker_response_header['X-UNICORE-SecuritySession']
    app_logger.trace("{} - J4J_Worker_Header: {}".format(uuidcode, j4j_worker_header))

    j4j_worker_json = jobs_threads_worker_utils.create_json(app_logger,
                                                            uuidcode,
                                                            request_json)
    app_logger.trace("{} - J4J_Worker_Json: {}".format(uuidcode, j4j_worker_json))
    # Call worker post
    try:
        method = "POST"
        method_args = {"url": app_urls.get('worker', {}).get('url_jobs'),
                       "headers": j4j_worker_header,
                       "json": j4j_worker_json,
                       "certificate": False}
        app_logger.info("{} - Post J4J_Worker".format(uuidcode))
        text, status_code, headers = jobs_threads_worker_utils.communicate(app_logger,
                                                                           uuidcode,
                                                                           method,
                                                                           method_args)
        if status_code != 201:
            app_logger.warning("{} - J4J_Worker Post failed. J4J_Worker Response: {} {} {}".format(uuidcode, text, status_code, utils_common.remove_secret(headers)))
            raise Exception("{} - J4J_Worker Post failed. Throw exception because of wrong status_code: {}".format(uuidcode, status_code))
        else:
            app_logger.debug("{} - J4J_Worker communication successful: {} {}".format(uuidcode, text, status_code))
            app_logger.trace("{} - J4J_Worker communication successful: {}".format(uuidcode, headers))
            j4j_worker_header['kernelurl'] = headers['kernelurl']
            j4j_worker_header['filedir'] = headers['filedir']
            j4j_worker_header['X-UNICORE-SecuritySession'] = headers['X-UNICORE-SecuritySession']
    except:
        app_logger.exception("{} - J4J_Worker communication failed. {} {}".format(uuidcode, method, utils_common.remove_secret(method_args)))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get('jhubtoken'),
                                "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system')),
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        return

    # update database
    app_logger.debug("{} - Add '{}' to database".format(uuidcode, request_json.get('servername')))
    utils_db.create_entry(app_logger,
                          uuidcode,
                          request_headers,
                          request_json,
                          app_database,
                          j4j_worker_header['kernelurl'],
                          j4j_worker_header['filedir'])

    # call worker get (fire and forget)
    j4j_worker_header['servername'] = request_json.get('servername')
    j4j_worker_header['system'] = request_json.get('system')
    j4j_worker_header['port'] = str(request_json.get('port'))
    try:
        utils_hub_update.status(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_status'),
                                request_headers.get('jhubtoken'),
                                'waitforhostname',
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
    except:
        app_logger.warning("{} - Could not update status for JupyterHub".format(uuidcode))
    try:
        method = "GET"
        method_args = {"url": app_urls.get('worker', {}).get('url_jobs'),
                       "headers": j4j_worker_header,
                       "certificate": False,
                       "fire_and_forget": True}
        app_logger.info("{} - Get J4J_Worker".format(uuidcode))
        jobs_threads_worker_utils.communicate(app_logger,
                                              uuidcode,
                                              method,
                                              method_args)

    except:
        app_logger.exception("{} - J4J_Worker communication failed. Send errorcode 526 to JupyterHub.cancel. {} {}".format(uuidcode, method, utils_common.remove_secret(method_args)))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get('jhubtoken'),
                                "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system')),
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        try:
            request_headers['kernelurl'] = j4j_worker_header['kernelurl']
            request_headers['filedir'] = j4j_worker_header['filedir']
            request_headers['servername'] = request_json.get('servername')
            request_headers['system'] = request_json.get('system')
            request_headers['port'] = str(request_json.get('port'))
            jobs_threads.delete(app_logger,
                   uuidcode,
                   request_headers,
                   app_database,
                   app_urls.get('tunnel', {}).get('url_tunnel'),
                   app_urls.get('worker', {}).get('url_jobs'),
                   app_urls.get('docker', {}).get('delete_folder'),
                   app_urls.get('hub', {}).get('url_proxy_route'),
                   app_urls.get('hub', {}).get('url_token'))
        except:
            app_logger.exception("{} - Could not delete/destroy Job via J4J_Worker. {}".format(uuidcode, utils_common.remove_secret(request_headers)))


def delete_job(app_logger, uuidcode, request_headers, delete_header, app_urls, kernelurl, filedir, port, account, project):
    # Create Header to communicate with J4J_Worker
    if len(delete_header) == 0:
        # It's the first server with this name we want to delete. So we have to load the basic stuff
        for key, value in request_headers.items():
            delete_header[key] = value
        delete_header['Intern-Authorization'] = utils_file_loads.get_j4j_worker_token()
    delete_header['kernelurl'] = kernelurl
    delete_header['filedir'] = filedir
    delete_header['port'] = port
    delete_header['account'] = account
    delete_header['project'] = project
    delete_header["tokenurl"] = request_headers.get("tokenurl"),
    delete_header["authorizeurl"] = request_headers.get("authorizeurl"),

    # Send DELETE to J4J_Worker
    method = "DELETE"
    method_args = {"url": app_urls.get('worker', {}).get('url_jobs'),
                   "headers": delete_header,
                   "certificate": False}
    app_logger.info("{} - Delete J4J_Worker".format(uuidcode))
    text, status_code, headers = jobs_threads_worker_utils.communicate(app_logger,
                                                                       uuidcode,
                                                                       method,
                                                                       method_args)
    if status_code == 200:
        app_logger.debug("{} - J4J_Worker communication successful: {} {}".format(uuidcode, text, status_code))
        app_logger.trace("{} - J4J_Worker communication successful: {}".format(uuidcode, headers))
        delete_header['accesstoken'] = headers['accesstoken']
        delete_header['expire'] = headers['expire']
        delete_header['X-UNICORE-SecuritySession'] = headers['X-UNICORE-SecuritySession']
    else:
        app_logger.warning("{} - J4J_Worker communication not successful: {} {} {}".format(uuidcode, text, status_code, utils_common.remove_secret(headers)))
        raise Exception("{} - J4J_Worker communication not successful. Throw exception because of wrong status_code: {}".format(uuidcode, status_code))
    return headers, delete_header


def random_port(app_logger, uuidcode, database, database_tunnel):
    """Get a single random port."""
    count = 0
    b = True
    while b:
        sock = socket.socket()
        sock.bind(('', 0))
        port = sock.getsockname()[1]
        sock.close()
        if len(utils_db.get_entry_port(app_logger,
                                       uuidcode,
                                       port,
                                       database)) == 0 \
        and len(utils_db.get_tunneldb_port(app_logger,
                                           uuidcode,
                                           port,
                                           database_tunnel)) == 0:
            b = False
            break
        count += 1
        if count > 20:
            app_logger.error("{} - Could not find unused port in 20 trys. Return port 0. Last tried random port: {}".format(uuidcode, port))
            return 0
    return port
