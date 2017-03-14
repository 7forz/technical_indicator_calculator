#!/usr/bin/python3
# -*- encoding: utf8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import MA
import global_data


class TestMA(unittest.TestCase):
    def test_ma(self):
        ma = MA('000001')
        self.assertAlmostEqual(ma.get_ma('2017-03-09', 5), 9.42, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(ma.get_ma('2017-02-10', 10), 9.29, places=2)
        self.assertAlmostEqual(ma.get_ma('2016-12-15', 30), 9.37, places=2)
        self.assertAlmostEqual(ma.get_ma('2017-03-14', 30), 9.41, places=2)
        self.assertAlmostEqual(ma.get_ma('2017-03-09', 90), 9.30, places=2)
        global_data.save_database(global_data.DB_PATH)

if __name__ == '__main__':
    unittest.main()
