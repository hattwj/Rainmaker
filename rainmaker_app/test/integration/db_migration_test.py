from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *


class SchemaMigrationTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

    @inlineCallbacks
    def test_track_changes(self):
        pass
