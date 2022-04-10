#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes import Index
from indexes.base import Index


class KDJ(Index):
    """
        KDJ指标
        通达信软件中的公式为：
        RSV:=(CLOSE-LLV(LOW,N))/(HHV(HIGH,N)-LLV(LOW,N))*100;
        K:SMA(RSV,M1,1);
        D:SMA(K,M2,1);
        J:3*K-2*D;
        共3个参数: n m1 m2 但通达信中m1=m2 所以暂定为2个参数
        n>m
    """

    def get_kdj(self, symbol: str, date: str, n: int, m: int):
        """ 计算所有日期的 KDJ 序列, 返回给定日期的 KDJ 的J值 """

        key = f'kdj-{n}-{m}'
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

        # 获取LLV(N)
        key = f'llv-{n}'
        llv = None
        if self.computed_memo.contains(symbol, key):  # 已有计算
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                llv = self.computed_memo.get(symbol, key)
        if llv is None:
            llv = self.llv(low_array, n)
            self.computed_memo.set(symbol, key, llv)  # 计算出来后填入缓存

        # 获取HHV(N)
        key = f'hhv-{n}'
        hhv = None
        if self.computed_memo.contains(symbol, key):  # 已有计算
            if len(self.computed_memo.get(symbol, key)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                hhv = self.computed_memo.get(symbol, key)
        if hhv is None:
            hhv = self.hhv(high_array, n)
            self.computed_memo.set(symbol, key, hhv)  # 计算出来后填入缓存

        # RSV:=(CLOSE-LLV(LOW,N))/(HHV(HIGH,N)-LLV(LOW,N))*100;
        rsv: np.ndarray = (close_array - llv) / (hhv - llv + 0.00000001) * 100  # 避免除以0
        if np.isnan(rsv[0]):  # 若第一天停牌 则hhv-llv等于0 相除之后会变成nan 导致之后的计算全部错误
            rsv[0] = 0

        k = self.sma(rsv, m, 1)
        d = self.sma(k, m, 1)
        j = 3 * k - 2 * d

        # 计算KDJ需要较多运算 不能直接读取(要算SMA) 所以把结果暂时存下来
        key = f'kdj-{n}-{m}'
        self.computed_memo.set(symbol, key, j)

        offset = global_data_instance.find_date_offset(symbol, date)
        return j[offset]

kdj_instance = KDJ()
