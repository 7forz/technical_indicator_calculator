#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import KDJ
import global_data


class TestKDJ(unittest.TestCase):
    def test_kdj(self):
        kdj = KDJ('000001')
        global_data.add_data('000001')
        self.assertAlmostEqual(kdj.get_kdj('2017-06-16', 9, 3), 1.78, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(kdj.get_kdj('2017-06-01', 9, 3), 109.21, places=2)
        self.assertAlmostEqual(kdj.get_kdj('2017-02-20', 9, 3), 79.49, places=2)
        global_data.save_database(global_data.DB_FILE)

if __name__ == '__main__':
    unittest.main()
