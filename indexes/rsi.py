#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes.base import Index, ref


class RSI(Index):
    """
        RSI 相对强弱指数 默认参数为6
        LC:=REF(CLOSE,1);   # LC为1日前的收盘价
        RSI:SMA(MAX(CLOSE-LC,0),N1,1)/SMA(ABS(CLOSE-LC),N1,1)*100;
    """

    def get_rsi(self, symbol: str, date: str, n: int):
        """ 计算所有日期的 RSI(n) 序列, 返回给定日期的 RSI(n) """

        key = f'rsi-{n}'
        if self.computed_memo.contains(symbol, key):
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                if date in global_data_instance.symbol_to_date_set[symbol]:
                    offset = global_data_instance.find_date_offset(symbol, date)
                    return self.computed_memo.get(symbol, key)[offset]
                else:
                    return np.nan

        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)

        # LC:=REF(CLOSE,1);
        lc = ref(close_array, 1)

        # RSI:SMA(MAX(CLOSE-LC,0),N1,1)/SMA(ABS(CLOSE-LC),N1,1)*100;
        rsi = self.sma(np.maximum(close_array-lc, 0), n, 1) / (self.sma(np.abs(close_array-lc), n, 1) + 1e-6) * 100  # 避免0÷0
        self.computed_memo.set(symbol, key, rsi)  # 计算出来后填入缓存

        offset = global_data_instance.find_date_offset(symbol, date)
        return rsi[offset]

rsi_instance = RSI()
