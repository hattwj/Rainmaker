# stdlib imports
from __future__ import print_function
#from abc import ABCMeta, abstractmethod
from warnings import warn
from threading import Thread
from time import sleep

# lib imports
from pytox import Tox, OperationFailedError

# local imports
from rainmaker.main import Application
from rainmaker.tox import tox_env
from rainmaker.tox import tox_errors

from rainmaker.net.state import StateMachine, RunLevel
from rainmaker.net.events import EventHandler, EventError
from rainmaker.net.msg_buffer import MsgBuffer


'''
    - Ring func, pass in sync
    - Dont subclass Tox, proxy it instead
    - Proxy receives tox, mock tox param for testing 
'''
class ToxBase(object):
    '''
        Base class with overrides/defaults for Tox
        - mixin class
    '''
    running = False
    was_connected = False
    ever_connected = False
    _bootstrap = None
    primary = None
    base_group_id = None

    def __init__(self, data=None):
        super().__init__()
        if data:
            self.load(data)
        self.router = EventHandler(self)
        self.events = EventHandler(self)
        self.state_machine = StateMachine()
        self.msg_buffer = MsgBuffer()
        self.register = self.router.register

    def start(self):
        self.state_machine.start()

    def stop(self):
        self.state_machine.stop()

    def gsend(self, cmd, data=None):
        raise NotImplementedError()
    
    def fsend(self, fid, cmd, data=None):
        raise NotImplementedError()

    def group_message_send(self, gid, data):
        raise NotImplementedError()

    def send_message(self, fid, msg):
        raise NotImplementedError()

class ToxBot(Tox, ToxBase):
    
    def __init__(self, data=None):
        super().__init__()

def acts_as_connect_bot(tox):
    '''
        Manage tox connection state
    '''
 
    def bootstrap():
        if not tox._bootstrap: 
            tox._bootstrap = tox_env.random_server()
        return tox._bootstrap

    def state_level_changed(name, code, prev_code):
        print('%s: %s %s' % (tox.__class__.__name__, StateMachine.ACTION_NAMES[code], name)) 
        ename = '%s_%s' % (name, StateMachine.ACTION_NAMES[code])
        tox.events.call_event(ename)

    def __conn_run_level__():
        '''
            Base Tox run_level
            - threaded to constantly check tox.do
            - check for shut down
        '''
        def _tox_do():
            do = tox.tox.do
            while True:
                do()
                sleep(0.04)
                if not run_level.should_run:
                    break
        
        def _start():
            ip, port, pubk = tox.bootstrap 
            tox.bootstrap_from_address(ip, port, pubk)
        
        def _stop():
            tox._bootstrap = None
        
        def _valid():
            return tox.isconnected()
        
        _tox_thread = Thread(target=_tox_do)
        _tox_thread.daemon = True
        _tox_thread.start()
        
        name = 'tox_connection'
        run_level = RunLevel(name, _start, _stop, _valid, 30)
        return run_level

    # connection state manager
    tox.state_machine.add(tox.__conn_run_level__())
    tox.state_machine.level_changed = tox.state_level_changed

def acts_as_message_bot(tox):
    '''
        compose Bots to manage individual tasks
        - connection
        - text
        - file transfer
    ''' 
    router = tox.router
    send_buffer = tox.msg_buffer.send
    recv_buffer = tox.msg_buffer.recv
     
    def gsend(event):
        '''
            Broadcast event
        '''
        cmd, status, data = event.cmd, event.status, event.data
        rcode = router.temp(event.reply_with)
        for msg in send_buffer(rcode, cmd, status, data):
            tox.group_message_send(tox.base_group_id, msg) 

    def fsend(fid, event):
        '''
            Send event to friend
        '''
        cmd, status, data = event.cmd, event.status, event.data
        rcode = router.temp(rcode, event.reply, timeout=30)
        for msg in send_buffer(cmd, data, chunk=1300):
            tox.send_message(fid, msg)
    
    def on_friend_request(pk, msg):
        '''
            Pass to authenticate
        '''
        key = 'tox-fr-%s-%s' % (id(tox), pk)
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_pk': pk,
                'params': params
            }
            tox.router.call_event('authenticate', params=params)

    def on_friend_message(fid, msg):
        '''
            A friend has sent a message
        '''
        # manage reply from handler
        def freply(event):
            # send reply to caller
            tox.fsend(fid, event.name, event.val())
        
        # Generate a unique key for this request stream
        key = 'tox-fm-%s-%s' % (id(tox), fid)
        # Only yield when msg is complete
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_id': fid,
                'params': params
            }
            tox.router.call_event(cmd, params=params, reply=freply)

    def on_group_message(gno, fid, msg):
        '''
            A group member sent a message
        '''
        def greply(event):
            tox.gsend(event.name, event.val())

        key = 'tox-gm-%s-%s-%s' % (id(tox), gno, fid)
        for cmd, params in recv_buffer(key, msg):
            params = {
                'friend_id': fid,
                'group_number': gno,
                'params': params
            }
            tox.router.call_event(cmd, params=params, reply=greply)

    # events received from tox client
    tox.on_group_message = on_group_message
    tox.on_friend_message = on_friend_message
    tox.on_friend_request = on_friend_request
    tox.gsend = gsend
    tox.fsend = fsend

def acts_as_search_bot(tox, primary_bot_address):
        
    def __search_run_level__():  
        # ran when level starts
        def _start():
            '''Start tox search'''
            #self.__search_tries_left -= 1
            if len(tox.get_friendlist()) == 0:
                tox.add_friend(primary_bot_address, auth_msg)
        
        # ran when level stops
        def _stop():
            #if self.__search_tries_left <= 0:
            #    self.state_machine.stop()
            pass

        # Periodic check to see if level is valid
        def _valid():
            if tox.get_friend_connection_status(0):
                #self.__search_tries_left = 2
                return True
            else:
                try:
                    # try to reach friends
                    for fid in tox.get_friendlist():
                        tox.fsend(fid, 'ping')
                except OperationFailedError as e:
                    pass
                return False
        
        return RunLevel('tox_search', _start, _stop, _valid, 40)

    def on_group_invite(friend_num, gtype, grp_pubkey):
        print('Joining group: %s' % gtype)
        group_id = tox.join_groupchat(friend_num, grp_pubkey)
    
    assert tox.primary is None
    tox.primary = False
    tox.state_machine.add(__search_run_level__())
    tox.on_group_invite = on_group_invite

def acts_as_primary_bot(tox):
    '''
        Primary tox node:
        - create group chat
        - hand off on shutdown
        - Inherited base functions
    '''
    assert tox.primary is None
    tox.primary = True
    # group chat room
    tox.base_group_id = tox.add_groupchat()
 
