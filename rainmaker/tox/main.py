# Python imports
from __future__ import print_function
from sys import exit

# Lib imports
from twisted.internet import defer

# Local imports
from rainmaker.tox import tox_updater, tox_env
from rainmaker.main import Application
from rainmaker.db.main import ToxServer

def init_tox(session, **opts):
    # check db
    tox_servers = session.query(ToxServer).all()
    
    # load server data
    if not tox_servers:
        # attempt to load
        nodes = tox_updater.fetch(opts.get('tox_html', None))
        if not nodes:
            print('Unable to find any nodes')
            exit()
        for ipv4, port, pubkey in nodes:
            server = ToxServer(ipv4=ipv4, 
                port=port, pubkey=pubkey)
            tox_servers.append(server)
            session.add(server)
        session.commit()
    
    tox_servers = session.query(ToxServer).all()
    
    if not tox_servers:
        print('Unable to find any nodes')
        exit()
    for ts in tox_servers:
        tox_env.add_server(ts.ipv4, ts.port, ts.pubkey)
    print('Found %s tox servers' % len(tox_servers))

