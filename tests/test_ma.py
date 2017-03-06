#!/usr/bin/python3
# -*- encoding: utf8 -*-

import sys
sys.path.append('..')  # 增加上级目录到path
import unittest
from indexes import MA
import global_data


class TestMA(unittest.TestCase):
    def test_ma(self):
        ma = MA('000001')
        self.assertAlmostEqual(ma.get_ma('2017-03-03', 5), 9.45, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(ma.get_ma('2017-02-10', 10), 9.29, places=2)
        self.assertAlmostEqual(ma.get_ma('2016-12-15', 30), 9.37, places=2)
        self.assertAlmostEqual(ma.get_ma('2016-11-01', 90), 9.11, places=2)
        global_data.save_database()

if __name__ == '__main__':
    unittest.main()
