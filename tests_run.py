import unittest
import logging
from lib import logger

logger.base_level = logging.DEBUG

from test.unit import *

unittest.main()

