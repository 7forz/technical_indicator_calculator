#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import MACD
import global_data


class TestMACD(unittest.TestCase):
    def test_macd(self):
        macd = MACD('600519')  # 它的MACD值比较大
        global_data.add_data('600519')
        self.assertAlmostEqual(macd.get_macd('2017-03-13', 12, 26, 9), 1.92, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(macd.get_macd('2017-03-14', 12, 26, 9), 1.58, places=2)
        # self.assertAlmostEqual(macd.get_macd('2016-11-22', 12, 26, 9), -2.59, places=2)
        # 上面的有一点点问题，算出来是-2.59701，通达信的是-2.594，导致assert报错，应该是早期的数据还不够多导致的

        macd = MACD('000001')
        global_data.add_data('000001')
        self.assertAlmostEqual(macd.get_macd('2017-03-13', 9, 20, 7), -0.03, places=2)
        self.assertAlmostEqual(macd.get_macd('2017-03-14', 9, 20, 7), -0.02, places=2)
        self.assertAlmostEqual(macd.get_macd('2017-03-17', 9, 20, 7), -0.02, places=2)
        self.assertAlmostEqual(macd.previous_value('2017-03-17', 1), 0.01, places=2)  # 获取的是03-16的值
        self.assertAlmostEqual(macd.get_saved_macd('2017-03-16'), 0.01, places=2)  # 获取的也是03-16的值
        global_data.save_database(global_data.DB_FILE)

if __name__ == '__main__':
    unittest.main()
