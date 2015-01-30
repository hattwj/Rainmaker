# Python imports
from __future__ import print_function
# Lib imports
from twisted.internet import defer
# Local imports
from rainmaker_app import tox, app
from rainmaker_app.model.tox_server import ToxServer


@defer.inlineCallbacks
def configure():
    # load settings
    conf = app.tox_settings
    for k, v in app.tox_settings.iteritems():
        setattr(tox.tox_env, k, v)

    # instantiate servers
    tox.tox_env.servers = tox.tox_ring.ToxServers()
    # check db
    tox_servers = yield ToxServer.all()
    # load server data
    if not tox_servers:
        print('Downloading Tox server list')
        nodes = tox.tox_updater.fetch()
        if not nodes:
            print('Unable to find any nodes')
            exit()
        for ipv4, port, pubkey in nodes:
            server = yield ToxServer.findOrCreate(ipv4=ipv4, 
                port=port, pubkey=pubkey)
            tox_servers.append(server)
    
    if not tox_servers:
        print('Unable to find any nodes')
        exit()
    for ts in tox_servers:
        tox.tox_env.servers.add(ts.ipv4, ts.port, ts.pubkey)
    print('Found %s tox servers' % len(tox_servers))