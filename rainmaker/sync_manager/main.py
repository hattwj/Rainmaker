from rainmaker.sync_manager.scan_manager import scan
from rainmaker.sync_manager.sync_path_manager import SyncPathManager

import rainmaker.logger
log = rainmaker.logger.create_log(__name__)

def init_sync(app):
    for sync in db.query(Sync).all():
        SyncPathManager(sync)


