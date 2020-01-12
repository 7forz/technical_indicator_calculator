#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np

import global_data
from indexes.base import Index, ref


class RSI(Index):
    """
        RSI 相对强弱指数 默认参数为6
        LC:=REF(CLOSE,1);   # LC为1日前的收盘价
        RSI:SMA(MAX(CLOSE-LC,0),N1,1)/SMA(ABS(CLOSE-LC),N1,1)*100;
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_rsi(self, date, n=6):
        """ 获取给定日期的 RSI(n) 假定已有最新的K线数据 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None

        # 数据库存在分2种情况 有当天K线数据且已经算出来 有K线但NaN
        # 尝试从已有数据读取 读取成功马上返回
        try:
            result = data.loc[date, f'rsi{n}']  # 若没有K线数据会抛出KeyError
            if str(result) != 'nan':  # 有K线但NaN result不是简单的np.nan
                return result
            else:
                raise RuntimeError
        except (KeyError, RuntimeError):
            # 没有RSI数据 需从收盘价计算
            closes = data['close'].to_numpy()

        # LC:=REF(CLOSE,1);
        lc = ref(closes, 1)

        # RSI:SMA(MAX(CLOSE-LC,0),N1,1)/SMA(ABS(CLOSE-LC),N1,1)*100;
        rsi = self.sma(np.maximum(closes-lc, 0), n, 1) / (self.sma(np.abs(closes-lc), n, 1) + 1e-6) * 100  # 避免0÷0

        new_data = global_data.add_column(self.stock, f'rsi{n}', rsi)  # 计算出来后填入总表

        try:
            return new_data.loc[date, f'rsi{n}']  # 最终返回对应日期的RSI值
        except KeyError:  # 该日停牌 返回nan
            return np.nan
