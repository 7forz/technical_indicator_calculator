#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import RSI
import global_data


class TestRSI(unittest.TestCase):
    def test_rsi(self):
        rsi = RSI('000001')
        global_data.add_data('000001')
        self.assertAlmostEqual(rsi.get_rsi('2016-08-16', 6), 67.13, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(rsi.get_rsi('2017-02-13', 6), 82.68, places=2)
        self.assertAlmostEqual(rsi.get_rsi('2017-03-24', 6), 27.90, places=2)
        global_data.save_database(global_data.DB_FILE)

if __name__ == '__main__':
    unittest.main()
