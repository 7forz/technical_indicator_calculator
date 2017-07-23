#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import MTM
import global_data


class TestMTM(unittest.TestCase):
    def test_mtm(self):
        mtm = MTM('000002')
        global_data.add_data('000002')
        self.assertAlmostEqual(mtm.get_mtm('2017-06-26', 12, 6), 1.67, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(mtm.get_mtm('2017-07-21', 12, 6), 0.08, places=2)
        global_data.save_database(global_data.DB_FILE)

if __name__ == '__main__':
    unittest.main()
