#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes import Index


class MA(Index):
    """ 简单移动平均线 """

    def get_ma(self, symbol: str, date: str, n: int) -> float:
        """ 计算所有日期的 N日均线 的序列（若有缓存则无需计算），返回给定日期的 N日均线 的值 """

        key = f'ma-{n}'
        if self.computed_memo.contains(symbol, key):  # 已有计算
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                if date in global_data_instance.symbol_to_date_set[symbol]:
                    offset = global_data_instance.find_date_offset(symbol, date)
                    return self.computed_memo.get(symbol, key)[offset]
                else:
                    return np.nan

        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)

        # 计算MA
        if len(close_array) > n:  # 避免只有50天数据却计算了MA90的问题 否则求卷积后提取时会有问题
            ma_array = self.ma(close_array, n)
            self.computed_memo.set(symbol, key, ma_array)  # 计算出来后填入缓存

            offset = global_data_instance.find_date_offset(symbol, date)
            return ma_array[offset]
        else:
            return np.nan

ma_instance = MA()
