#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes import Index


class MACD(Index):
    """
        Moving Average Convergence and Divergence 指数平滑异动移动平均线
        通达信软件中的公式为：
        DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        DEA:EMA(DIF,MID);
        MACD:(DIF-DEA)*2;
        共3个参数: short long mid
        核心函数为EMA
    """

    def get_macd(self, symbol: str, date: str, short: int, long: int, mid: int):
        """ 计算所有日期的MACD序列, 返回给定日期的MACD """

        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)

        # 获取EMA(CLOSE,SHORT)
        key = f'ema-{short}'
        ema_short = None
        if self.computed_memo.contains(symbol, key):  # 已有计算
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                ema_short = self.computed_memo.get(symbol, key)
        if ema_short is None:
            ema_short = self.ema(close_array, short)
            self.computed_memo.set(symbol, key, ema_short)  # 计算出来后填入缓存

        # 获取EMA(CLOSE,LONG)
        key = f'ema-{long}'
        ema_long = None
        if self.computed_memo.contains(symbol, key):  # 已有计算
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                ema_long = self.computed_memo.get(symbol, key)
        if ema_long is None:
            ema_long = self.ema(close_array, long)
            self.computed_memo.set(symbol, key, ema_long)  # 计算出来后填入缓存

        # DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        dif: np.ndarray = ema_short - ema_long

        # DEA:EMA(DIF,MID);
        dea: np.ndarray = self.ema(dif, mid)

        # MACD:(DIF-DEA)*2;
        macd: np.ndarray = (dif - dea) * 2

        key = f'macd-{short}-{long}-{mid}'
        self.computed_memo.set(symbol, key, macd)

        offset = global_data_instance.find_date_offset(symbol, date)
        return macd[offset]

macd_instance = MACD()
