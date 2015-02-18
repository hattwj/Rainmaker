import logging
from rainmaker.utils import Object

levels = {
    'debug': logging.DEBUG,
    'info': logging.INFO,
    'warn': logging.WARN,
    'error': logging.ERROR,
    'none': logging.NOTSET
}
styles = [
    '%(message)s',
    '%(message)s',
    '%(message)s',
    '%(name)-12s %(message)s',
    '%(name)-12s %(levelname)-8s %(message)s'
]

verbosity = {
    'Rainmaker': 0,
    'rainmaker_app.console': 0,
    'rainmaker_app.debug_node': 0,
    'rainmaker_app.db.config': 0,
    'rainmaker_app.lib.net.start_tls': 0,
    'rainmaker_app.lib.net.clients': 0,
    'rainmaker_app.lib.net.udp_multicast': 0,
    'Tests': 4,
    'rainmaker_app.lib.fs_actions': 0,
    'AppLoop': 1,
    'AppProfiles': 1,
    'AppParser': 1,
    'Profile': 2,
    'LogMonitor': 2,
    'FsMonitor': 2,
    'ProfileManager': 2,
    'Handler': 3,
    'RecordScript': 3,
    'RecordHooks': 4,
    'AttrsBag': 4,
    'Callbacks': 4,
    'RegexDict': 4,
}

config = Object(
    init_done=False,
    level='warn', 
    verbosity=0,
    date_style= '%Y-%m-%d-%H-%M-%S',
    log_file_style= '%(message)s'
)

def set_verbosity(val):
    ''' Set logging verbosity '''
    if val <=0:
        val = 0
    elif val >= len(styles):
        val = len(styles)-1
    config.verbosity = val

def create_log(name='',style=None,level=None):
    if config.verbosity < verbosity.get(name, 0):
        level = 'error'
    else:
        level = config.level
    # Get log level and style orvdefaults
    level = levels[level] if level else levels[config.level]
    style = style if style else styles[config.verbosity]
    
    log = logging.getLogger(name)
    log.v=verbosity

    if log.handlers:
        handler = log.handlers[0] 
    else:
        handler = logging.StreamHandler()
        log.addHandler(handler)

    handler.setLevel(level)
    log.setLevel(level)
    # Allow log.msg to act like log.info
    log.msg = log.info
    # set a format which is simpler for f_log use
    formatter = logging.Formatter(style)
    
    # tell the handler to use this format
    handler.setFormatter(formatter) 

    return log

# also log output to a file
def log_to_file(fpath, name ,level=None, style=None,date_style=None):
    level = levels[level] if level else levels[log_level]
    date_style = date_style if date_style else config['date_style']
    style = style if style else config['log_file_style']
    
    log = logging.getLogger(name)

    # define a Handler
    handler = logging.FileHandler(fpath)
    handler.setLevel( level )
    
    # set a format which is simpler for handler use
    formatter = logging.Formatter(style,date_style)
    
    # tell the handler to use this format
    handler.setFormatter(formatter)
    
    # add the handler to the logger
    log.addHandler(handler)
    
    return log
