"""
Seeding tests.

Author(s): Arno Bakker, Niels Zeilemaker
"""
from __future__ import absolute_import

import logging
import os

from twisted.internet.defer import Deferred, inlineCallbacks

from Tribler.Core.TorrentDef import TorrentDef
from Tribler.Core.simpledefs import DLSTATUS_SEEDING, dlstatus_strings
from Tribler.Test.common import TESTS_DATA_DIR
from Tribler.Test.test_as_server import TestAsServer
from Tribler.Test.tools import trial_timeout


class TestSeeding(TestAsServer):
    """
    Test whether the seeding works correctly.
    """

    @inlineCallbacks
    def setUp(self):
        yield super(TestSeeding, self).setUp()
        self._logger = logging.getLogger(self.__class__.__name__)
        self.test_deferred = Deferred()
        self.tdef = TorrentDef.load(os.path.join(TESTS_DATA_DIR, 'video.avi.torrent'))
        self.sourcefn = os.path.join(TESTS_DATA_DIR, 'video.avi')

    def setUpPreSession(self):
        super(TestSeeding, self).setUpPreSession()
        self.config.set_libtorrent_enabled(True)

    def start_download(self, dscfg):
        download = self.session.start_download_from_tdef(self.tdef, dscfg)
        download.set_state_callback(self.downloader_state_callback)

        download.add_peer(("127.0.0.1", self.seeder_session.config.get_libtorrent_port()))

    @trial_timeout(60)
    def test_seeding(self):
        """
        Test whether a torrent is correctly seeded
        """
        def start_download(_):
            dscfg = self.dscfg_seed.copy()
            dscfg.set_dest_dir(self.getDestDir())
            self.start_download(dscfg)

        self.setup_seeder(self.tdef, TESTS_DATA_DIR).addCallback(start_download)
        return self.test_deferred

    def downloader_state_callback(self, ds):
        d = ds.get_download()
        self._logger.debug("download status: %s %s %s",
                           repr(d.get_def().get_name()),
                           dlstatus_strings[ds.get_status()],
                           ds.get_progress())

        if ds.get_status() == DLSTATUS_SEEDING:
            # File is in
            destfn = os.path.join(self.getDestDir(), "video.avi")
            f = open(destfn, "rb")
            realdata = f.read()
            f.close()
            f = open(self.sourcefn, "rb")
            expdata = f.read()
            f.close()

            self.assertEqual(realdata, expdata)
            self.test_deferred.callback(None)
            return 0.0
        return 1.0
