#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes import Index


class CCI(Index):
    """
        TYP:=(HIGH+LOW+CLOSE)/3;
        CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
    """

    def get_cci(self, symbol: str, date: str, n: int):
        """ 计算所有日期的 CCI(n) 序列, 返回给定日期的 CCI(n) """

        key = f'cci-{n}'
        if self.computed_memo.contains(symbol, key):
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                if date in global_data_instance.symbol_to_date_set[symbol]:
                    offset = global_data_instance.find_date_offset(symbol, date)
                    return self.computed_memo.get(symbol, key)[offset]
                else:
                    return np.nan

        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)
        high_array = global_data_instance.get_array_since_date(symbol, OHLCV.HIGH, global_data_instance.START_DOWNLOAD_DATE)
        low_array = global_data_instance.get_array_since_date(symbol, OHLCV.LOW, global_data_instance.START_DOWNLOAD_DATE)


        # TYP:=(HIGH+LOW+CLOSE)/3;
        # CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
        typ = (high_array + low_array + close_array) / 3
        cci = (typ - self.ma(typ, n)) / (0.015 * self.avedev(typ, n))
        self.computed_memo.set(symbol, key, cci)  # 计算出来后填入缓存

        offset = global_data_instance.find_date_offset(symbol, date)
        return cci[offset]

cci_instance = CCI()
