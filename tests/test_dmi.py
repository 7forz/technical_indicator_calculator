#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import os
import sys
import unittest
sys.path.append('..')
sys.path.append(os.getcwd())
from indexes import DMI
import global_data


class TestDMI(unittest.TestCase):
    def test_dmi(self):
        dmi = DMI('000001')
        global_data.add_data('000001')
        pdi, mdi  = dmi.get_dmi('2019-10-25', 14)
        self.assertAlmostEqual(pdi, 28.00, places=2)  # 与真实值对比 精确到后2位
        self.assertAlmostEqual(mdi, 11.25, places=2)  # 与真实值对比 精确到后2位

if __name__ == '__main__':
    unittest.main()
