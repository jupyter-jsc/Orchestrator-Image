import psycopg2
import json

from contextlib import closing

def get_all_servernames(app_logger, uuidcode, username, database):
    # return list of all servernames
    username = "{}%".format(username)
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT servername FROM server WHERE servername LIKE %s"
                app_logger.trace("uuidcode={} - Execute: {}, username: {}".format(uuidcode, cmd, username))
                cur.execute(cmd,
                            (username, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    ret = []
    for result in results:
        ret.append(result[0])
    return ret

def get_entry_servername(app_logger, uuidcode, servername, database):
    # return list of results
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT system, kernelurl, filesurl, port, account, project FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}, userserver={}".format(uuidcode, cmd, servername))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    return results

def get_tunneldb_port(app_logger, uuidcode, port, database):
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT hostname FROM tunnels WHERE port = %s"
                app_logger.trace("uuidcode={} - Execute: {}, port: {}".format(uuidcode, cmd, port))
                cur.execute(cmd,
                            (str(port), ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    return results
    

def get_entry_port(app_logger, uuidcode, port, database):
    # return list of results
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT servername FROM server WHERE port = %s"
                app_logger.trace("uuidcode={} - Execute: {}, port: {}".format(uuidcode, cmd, port))
                cur.execute(cmd,
                            (str(port), ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
    return results

def set_skip(app_logger, uuidcode, servername, database, value):
    app_logger.debug("uuidcode={} - Set skip for userserver={} to {}".format(uuidcode, servername, value))
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "UPDATE server SET skip = %s WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}, args: {}".format(uuidcode, cmd, (value, servername)))
                cur.execute(cmd,
                            (value, servername))

def get_skip(app_logger, uuidcode, servername, database):
    app_logger.debug("uuidcode={} - Get skip value for userserver={}".format(uuidcode, servername))
    infos = []
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT skip FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
                for result in results:
                    infos.append(result[0].lower()=='true')
                # DEBUG:
                cmd = "SELECT * FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - DEBUG: Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - DEBUG Results: {}".format(uuidcode, results))
                ## DEBUG ENDE
    return infos


def remove_entrys(app_logger, uuidcode, servername, database):
    app_logger.debug("uuidcode={} - Remove entrys from database ( userserver={} )".format(uuidcode, servername))
    # open db
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "DELETE FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: '{}' ( userserver={} )".format(uuidcode, cmd, servername))
                cur.execute(cmd,
                            (servername, ))

def create_entry_docker(app_logger, uuidcode, database, servername, jhubtoken, port, dockerimage):
    app_logger.debug("uuidcode={} - Add server to database ( userserver={} )".format(uuidcode, servername))
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "INSERT INTO server (servername, jhubtoken, system, port, account, project, partition, reservation, Checkboxes, Resources, kernelurl, filesurl, spawning, skip, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd, (servername,
                                  jhubtoken,
                                  "docker",
                                  port,
                                  dockerimage,
                                  "docker",
                                  "docker",
                                  None,
                                  None,
                                  None,
                                  "docker",
                                  "docker",
                                  "true",
                                  "false"
                                  ))

def create_entry(app_logger, uuidcode, request_headers, request_json, database, kernelurl, filedir):
    app_logger.debug("uuidcode={} - Add server to database ( userserver={} )".format(uuidcode, request_json.get('servername')))
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "INSERT INTO server (servername, jhubtoken, system, port, account, project, partition, reservation, Checkboxes, Resources, kernelurl, filesurl, spawning, skip, date) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, now())"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd, (request_json.get('servername'),
                                  request_headers.get('jhubtoken'),
                                  request_json.get('system'),
                                  request_json.get('port'),
                                  request_headers.get('account'),
                                  request_headers.get('project'),
                                  request_json.get('partition'),
                                  request_json.get('reservation'),
                                  ';'.join(request_json.get('Checkboxes')),
                                  json.dumps(request_json.get('Resources')),
                                  kernelurl,
                                  filedir,
                                  "true",
                                  "false"
                                  ))


def get_entry_infos(app_logger, uuidcode, servername, database):
    app_logger.debug("uuidcode={} - Get all server with userserver={}".format(uuidcode, servername))
    infos = []
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT kernelurl, filesurl, system, port, account, project, jhubtoken, spawning FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
                for result in results:
                    kernelurl, filedir, system, port, account, project, jhubtoken, spawning = result
                    infos.append( {"kernelurl": kernelurl,
                                   "filedir": filedir,
                                   "system": system,
                                   "port": port,
                                   "account": account,
                                   "project": project,
                                   "jhubtoken": jhubtoken,
                                   "spawning": spawning})
    return infos

def get_spawning(app_logger, uuidcode, servername, database):
    app_logger.debug("uuidcode={} - Get spawning value for userserver={}".format(uuidcode, servername))
    infos = []
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "SELECT spawning FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - Results: {}".format(uuidcode, results))
                for result in results:
                    infos.append(result[0].lower()=='true')
                # DEBUG:
                cmd = "SELECT * FROM server WHERE servername = %s"
                app_logger.trace("uuidcode={} - DEBUG: Execute: {}".format(uuidcode, cmd))
                cur.execute(cmd,
                            (servername, ))
                results = cur.fetchall()
                app_logger.trace("uuidcode={} - DEBUG Results: {}".format(uuidcode, results))
                ## DEBUG ENDE
    return infos

def set_spawning(app_logger, uuidcode, servername, database, value):
    app_logger.debug("uuidcode={} - Set spawning for servername userserver={} to {}".format(uuidcode, servername, value))
    with closing(psycopg2.connect(host=database.get('host'),
                                  port=database.get('port'),
                                  user=database.get('user'),
                                  password=database.get('password'),
                                  database=database.get('database'))) as con: # auto closes
        with closing(con.cursor()) as cur: # auto closes
            with con: # auto commit
                cmd = "UPDATE server SET spawning = %s WHERE servername = %s"
                app_logger.trace("uuidcode={} - Execute: {}, args: {}".format(uuidcode, cmd, (value, servername)))
                cur.execute(cmd,
                            (value, servername))
