from rainmaker_app.test.db_helper import *
from rainmaker_app.test.test_helper import *

class DifferenceTest(unittest.TestCase):
    
    @inlineCallbacks
    def setUp(self):
        clean_temp_dir()
        yield initDB(db_path)
        print 'Running'

    @inlineCallbacks
    def tearDown(self):
        yield tearDownDB()

    @inlineCallbacks
    def test_no_conflict(self):
        ''' no difference between sets '''
        yield self.load_fixture('no_conflict')
        g = yield Difference.between_sync_paths(1, 2)
        self.assertEquals( g, [] )
    
    @inlineCallbacks
    def test_deleted(self):
        yield self.load_fixture('deleted')
        g = yield Difference.between_sync_paths(1, 2)
        self.assertEquals( len(g), 2)
        for h in g:
            print h
            print 'last_v'
            print h.last_version

    @inlineCallbacks
    def load_fixture(self, test_name):
        data = load('test/fixtures/unit/model/differences.yml')
        for r in data['my_file'][test_name]:
            yield MyFile(**r).save()

        for r in data['sync_comparison'][test_name]:
            yield SyncComparison(**r).save()


