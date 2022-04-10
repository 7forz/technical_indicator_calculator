#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes.base import Index, ref


class MTM(Index):
    """
        MTM 默认参数为N=12, M=6
        DELTA:CLOSE-REF(CLOSE,N);  # 当日收盘价与N日前的收盘价的差
        MTMMA:MA(DELTA,M);  # 求M日移动平均
    """

    def get_mtm(self, symbol: str, date: str, n: int, m: int):
        """ 计算所有日期的MTM序列, 返回给定日期的 MTM(n, m) """

        key = f'mtmma-{n}-{m}'
        if self.computed_memo.contains(symbol, key):
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                if date in global_data_instance.symbol_to_date_set[symbol]:
                    offset = global_data_instance.find_date_offset(symbol, date)
                    return self.computed_memo.get(symbol, key)[offset]
                else:
                    return np.nan


        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)

        # DELTA:CLOSE-REF(CLOSE,N)
        delta: np.ndarray = close_array - ref(close_array, n)

        # MTMMA:MA(DELTA,M)
        mtmma = self.ma(delta, m)
        self.computed_memo.set(symbol, key, mtmma)  # 计算出来后填入缓存

        offset = global_data_instance.find_date_offset(symbol, date)
        return mtmma[offset]

mtm_instance = MTM()
