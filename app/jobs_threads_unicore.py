import socket
import base64
import requests

from contextlib import closing

from app import jobs_threads_unicore_utils, utils_hub_update, utils_common, jobs_threads, utils_db,\
    utils_file_loads
from app.utils_common import SpawnException

def check_unicore_job_status(app_logger, uuidcode, app_urls, app_database, request_headers, escapedusername, servername, server_info):
    try:
        app_logger.trace("uuidcode={} - Call Create_get_header with: {} {} {} {} {}".format(uuidcode, request_headers, app_urls.get('hub', {}).get('url_proxy_route'), app_urls.get('hub', {}).get('url_token'), escapedusername, servername))
        unicore_header = jobs_threads_unicore_utils.create_get_header(app_logger,
                                                                      uuidcode,
                                                                      request_headers,
                                                                      app_urls.get('hub', {}).get('url_proxy_route'),
                                                                      app_urls.get('hub', {}).get('url_token'),
                                                                      escapedusername,
                                                                      servername,
                                                                      app_database)
    except:
        app_logger.exception("uuidcode={} - Could not create Header. Do nothing and return. {} {}".format(uuidcode, utils_common.remove_secret(request_headers), app_urls.get('hub', {}).get('url_token')))
        utils_db.set_skip(app_logger,
                          uuidcode,
                          request_headers.get('servername'),
                          app_database,
                          'False')
        return
    try:
        # call unicore get (fire and forget)
        unicore_header['kernelurl'] = server_info.get('kernelurl')
        unicore_header['filedir'] = server_info.get('filedir')
        unicore_header['system'] = server_info.get('system')
        unicore_header['port'] = server_info.get('port')
        unicore_header['account'] = server_info.get('account')
        unicore_header['project'] = server_info.get('project')
        unicore_header['jhubtoken'] = server_info.get('jhubtoken')
        unicore_header['spawning'] = server_info.get('spawning')
        unicore_header['pollspawner'] = request_headers.get('pollspawner', 'false')
    
        method = "GET"
        method_args = {"url": app_urls.get('unicore', {}).get('url_jobs'),
                       "headers":unicore_header,
                       "certificate": False,
                       "fire_and_forget": True}
        app_logger.info("uuidcode={} - Get J4J_UNICORE. Kernel_url: {}".format(uuidcode, unicore_header['kernelurl']))
        jobs_threads_unicore_utils.communicate(app_logger,
                                               uuidcode,
                                               method,
                                               method_args)

    except:
        utils_db.set_skip(app_logger,
                          uuidcode,
                          request_headers.get('servername'),
                          app_database,
                          'False')
        app_logger.exception("uuidcode={} - J4J_UNICORE communication failed. {} {}".format(uuidcode, method, utils_common.remove_secret(method_args)))


def start_unicore_job(app_logger, uuidcode, request_headers, request_json, app_urls, app_database):
    # Check if it's the cron test job
    try:
        cron_info = utils_file_loads.get_cron_info()
        user, servernameshort = request_json.get('servername', ':').split(':')  # @UnusedVariable
        if cron_info.get('systems', {}).get(request_json.get('system').upper(), {}).get('servername', '<undefined>') == servernameshort:
            if cron_info.get('systems', {}).get(request_json.get('system').upper(), {}).get('account', '<undefined>') == request_headers.get('account'):
                if cron_info.get('systems', {}).get(request_json.get('system').upper(), {}).get('project', '<undefined>') == request_headers.get('project'):
                    if cron_info.get('systems', {}).get(request_json.get('system').upper(), {}).get('partition', '<undefined>') == request_json.get('partition'):
                        # get refresh token
                        unity_file = utils_file_loads.get_unity()
                        refresh_token = unity_file.get(request_headers.get('tokenurl'), {}).get('immune_tokens', [''])[0]
                        # get access token
                        client_id = unity_file.get(request_headers.get('tokenurl'), {}).get('client_id', '')
                        client_secret = unity_file.get(request_headers.get('tokenurl'), {}).get('client_secret', '')
                        unity_cert = unity_file.get(request_headers.get('tokenurl'), {}).get('certificate', False)
                        scopes = unity_file.get(request_headers.get('authorizeurl'), {}).get('scope')
                        tokeninfo_url = unity_file.get(request_headers.get('tokenurl'), {}).get('links', {}).get('tokeninfo', '')
                        b64_key = base64.b64encode(bytes('{}:{}'.format(client_id, client_secret),'utf8')).decode('utf8')
                        headers = {
                                  'Accept': 'application/json',
                                  'Authorization': 'Basic {}'.format(b64_key)
                                  }
                        data = {
                               'refresh_token': refresh_token,
                               'grant_type': 'refresh_token',
                               'scope': ' '.join(scopes)
                               }
                        with closing(requests.post(request_headers.get('tokenurl'), headers=headers, data=data, verify=unity_cert)) as r:
                            if r.status_code != 200:
                                raise Exception("uuidcode={} Could not receive access_token: {} {}".format(uuidcode, r.status_code, r.text))
                            access_token = r.json().get('access_token')
                        # get expire
                        with closing(requests.get(tokeninfo_url,
                                                  headers = { 'Authorization': 'Bearer {}'.format(access_token) },
                                                  verify = unity_cert,
                                                  timeout = 1800)) as r:
                            expire = r.json().get('exp')
                        request_headers['accesstoken'] = access_token
                        request_headers['expire'] = '{}'.format(expire)
                        request_headers['refreshtoken'] = refresh_token
    except:
        app_logger.exception("uuidcode={}, Could not check if it's a cron job server".format(uuidcode))
    # Delete all server with this name (there should be none, but better safe than sorry)
    j4j_unicore_response_header = jobs_threads.delete(app_logger,
                                                      uuidcode,
                                                      request_headers,
                                                      app_urls,
                                                      app_database)
    # All duplicated servers are deleted from the database and stopped
    app_logger.trace('uuidcode={} - J4J_UNICORE_response_header: {}'.format(uuidcode, j4j_unicore_response_header))
    try:
        j4j_unicore_header = jobs_threads_unicore_utils.create_header(app_logger,
                                                                      uuidcode,
                                                                      request_headers,
                                                                      app_urls.get('hub', {}).get('url_proxy_route'),
                                                                      app_urls.get('hub', {}).get('url_token'),
                                                                      request_headers.get('escapedusername'),
                                                                      request_headers.get('servername'),
                                                                      app_database)
    except (SpawnException, Exception) as e:
        if type(e).__name__ == "SpawnException":
            error_msg = str(e)
        else:
            error_msg = "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system'))
        app_logger.exception("uuidcode={} - error_msg: {} -  Could not create Header. Send Cancel to JupyterHub and stop function. {} {}".format(uuidcode, error_msg, utils_common.remove_secret(request_headers), app_urls.get('hub', {}).get('url_token')))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get("jhubtoken"),
                                error_msg,
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        return
    # update with Infos of j4j_unicore delete
    if 'accesstoken' in j4j_unicore_response_header:
        j4j_unicore_header['accesstoken'] = j4j_unicore_response_header['accesstoken']
        j4j_unicore_header['expire'] = j4j_unicore_response_header['expire']
        utils_hub_update.token(app_logger,
                               uuidcode,
                               app_urls.get('hub', {}).get('url_proxy_route'),
                               app_urls.get('hub', {}).get('url_token'),
                               request_headers['jhubtoken'],
                               j4j_unicore_response_header['accesstoken'],
                               j4j_unicore_response_header['expire'],
                               request_headers.get('escapedusername'),
                               request_headers.get('servername'))

    if 'session' in j4j_unicore_response_header:
        j4j_unicore_header['X-UNICORE-SecuritySession'] = j4j_unicore_response_header['X-UNICORE-SecuritySession']
    app_logger.trace("uuidcode={} - J4J_UNICORE_Header: {}".format(uuidcode, j4j_unicore_header))

    j4j_unicore_json = jobs_threads_unicore_utils.create_json(app_logger,
                                                              uuidcode,
                                                              request_json)
    app_logger.trace("uuidcode={} - J4J_UNICORE_Json: {}".format(uuidcode, j4j_unicore_json))
    # Call UNICORE post
    try:
        method = "POST"
        if request_json.get('service', '').lower() == 'dashboard':
            url = app_urls.get('unicore', {}).get('url_dashboards')
        else:
            url = app_urls.get('unicore', {}).get('url_jobs')
        method_args = {"url": url,
                       "headers": j4j_unicore_header,
                       "json": j4j_unicore_json,
                       "certificate": False}
        app_logger.info("uuidcode={} - Post J4J_UNICORE".format(uuidcode))
        text, status_code, headers = jobs_threads_unicore_utils.communicate(app_logger,
                                                                            uuidcode,
                                                                            method,
                                                                            method_args)
        if status_code != 201:
            app_logger.warning("uuidcode={} - J4J_UNICORE Post failed. J4J_UNICORE Response: {} {} {}".format(uuidcode, text, status_code, utils_common.remove_secret(headers)))
            raise Exception("{} - J4J_UNICORE Post failed. Throw exception because of wrong status_code: {}".format(uuidcode, status_code))
        else:
            app_logger.debug("uuidcode={} - J4J_UNICORE communication successful: {} {}".format(uuidcode, text, status_code))
            app_logger.trace("uuidcode={} - J4J_UNICORE communication successful: {}".format(uuidcode, headers))
            j4j_unicore_header['kernelurl'] = headers['kernelurl']
            j4j_unicore_header['filedir'] = headers['filedir']
            j4j_unicore_header['X-UNICORE-SecuritySession'] = headers['X-UNICORE-SecuritySession']
    except (SpawnException, Exception) as e:
        if type(e).__name__ == "SpawnException":
            error_msg = str(e)
        else:
            error_msg = "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system'))
        app_logger.exception("uuidcode={} - error_msg: {} -  J4J_UNICORE communication failed. {} {}".format(uuidcode, error_msg, method, utils_common.remove_secret(method_args)))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get('jhubtoken'),
                                error_msg,
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        return

    # update database
    app_logger.debug("uuidcode={} - Add userserver={} to database".format(uuidcode, request_json.get('servername')))
    utils_db.create_entry(app_logger,
                          uuidcode,
                          request_headers,
                          request_json,
                          app_database,
                          j4j_unicore_header['kernelurl'],
                          j4j_unicore_header['filedir'])

    # call unicore get (fire and forget)
    j4j_unicore_header['servername'] = request_json.get('servername')
    j4j_unicore_header['system'] = request_json.get('system')
    j4j_unicore_header['port'] = str(request_json.get('port'))
    j4j_unicore_header['spawnget'] = "True"
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
        app_logger.warning("uuidcode={} - Could not update status for JupyterHub".format(uuidcode))
    try:
        method = "GET"
        method_args = {"url": app_urls.get('unicore', {}).get('url_jobs'),
                       "headers": j4j_unicore_header,
                       "certificate": False,
                       "fire_and_forget": True}
        app_logger.info("uuidcode={} - Get J4J_UNICORE".format(uuidcode))
        jobs_threads_unicore_utils.communicate(app_logger,
                                               uuidcode,
                                               method,
                                               method_args)
    except (SpawnException, Exception) as e:
        if type(e).__name__ == "SpawnException":
            error_msg = str(e)
        else:
            error_msg = "A mandatory backend service for {} had a problem. An administrator is informed".format(request_json.get('system'))
        app_logger.exception("uuidcode={} - error-msg: {} - J4J_UNICORE communication failed. Send errorcode 526 to JupyterHub.cancel. {} {}".format(uuidcode, error_msg, method, utils_common.remove_secret(method_args)))
        utils_hub_update.cancel(app_logger,
                                uuidcode,
                                app_urls.get('hub', {}).get('url_proxy_route'),
                                app_urls.get('hub', {}).get('url_cancel'),
                                request_headers.get('jhubtoken'),
                                error_msg,
                                request_headers.get('escapedusername'),
                                request_headers.get('servername'))
        try:
            request_headers['kernelurl'] = j4j_unicore_header['kernelurl']
            request_headers['filedir'] = j4j_unicore_header['filedir']
            request_headers['servername'] = request_json.get('servername')
            request_headers['system'] = request_json.get('system')
            request_headers['port'] = str(request_json.get('port'))
            jobs_threads.delete(app_logger,
                   uuidcode,
                   request_headers,
                   app_database,
                   app_urls.get('tunnel', {}).get('url_tunnel'),
                   app_urls.get('unicore', {}).get('url_jobs'),
                   app_urls.get('docker', {}).get('delete_folder'),
                   app_urls.get('hub', {}).get('url_proxy_route'),
                   app_urls.get('hub', {}).get('url_token'))
        except:
            app_logger.exception("uuidcode={} - Could not delete/destroy Job via J4J_UNICORE. {}".format(uuidcode, utils_common.remove_secret(request_headers)))


def delete_job(app_logger, uuidcode, request_headers, delete_header, app_urls, system, kernelurl, filedir, port, account, project):
    # Create Header to communicate with J4J_UNICORE
    if len(delete_header) == 0:
        # It's the first server with this name we want to delete. So we have to load the basic stuff
        for key, value in request_headers.items():
            delete_header[key] = value
        delete_header['Intern-Authorization'] = utils_file_loads.get_j4j_unicore_token()
    delete_header['system'] = system
    delete_header['kernelurl'] = kernelurl
    delete_header['filedir'] = filedir
    delete_header['port'] = port
    delete_header['account'] = account
    delete_header['project'] = project
    delete_header["tokenurl"] = request_headers.get("tokenurl")
    delete_header["authorizeurl"] = request_headers.get("authorizeurl")

    # Send DELETE to J4J_UNICORE
    method = "DELETE"
    method_args = {"url": app_urls.get('unicore', {}).get('url_jobs'),
                   "headers": delete_header,
                   "certificate": False}
    app_logger.info("uuidcode={} - Delete J4J_UNICORE".format(uuidcode))
    text, status_code, headers = jobs_threads_unicore_utils.communicate(app_logger,
                                                                        uuidcode,
                                                                        method,
                                                                        method_args)
    if status_code == 200:
        app_logger.debug("uuidcode={} - J4J_UNICORE communication successful: {} {}".format(uuidcode, text, status_code))
        app_logger.trace("uuidcode={} - J4J_UNICORE communication successful: {}".format(uuidcode, headers))
        delete_header['accesstoken'] = headers['accesstoken']
        delete_header['expire'] = headers['expire']
        delete_header['X-UNICORE-SecuritySession'] = headers['X-UNICORE-SecuritySession']
    else:
        app_logger.warning("uuidcode={} - J4J_UNICORE communication not successful: {} {} {}".format(uuidcode, text, status_code, utils_common.remove_secret(headers)))
        raise Exception("{} - J4J_UNICORE communication not successful. Throw exception because of wrong status_code: {}".format(uuidcode, status_code))
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
            app_logger.error("uuidcode={} - Could not find unused port in 20 trys. Return port 0. Last tried random port: {}".format(uuidcode, port))
            return 0
    return port
