#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
import pandas as pd
from indexes.base import Index
import global_data


class KDJ(Index):
    """
        KDJ指标
        通达信软件中的公式为：
        RSV:=(CLOSE-LLV(LOW,N))/(HHV(HIGH,N)-LLV(LOW,N))*100;
        K:SMA(RSV,M1,1);
        D:SMA(K,M2,1);
        J:3*K-2*D;
        共3个参数：n m1 m2 但通达信中m1=m2 所以暂定为2个参数
        n>m
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_kdj(self, date, n, m):
        """ 获取给定日期的KDJ的J值 假定已有最新的K线数据 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None
        assert data is not None, 'must have K-data before using get_kdj()!'

        closes = data['close'].to_numpy()
        highs = data['high'].to_numpy()
        lows = data['low'].to_numpy()

        # 数据库存在分2种情况 1.已经算出来给定日期的LLV+HHV 2.没有给定日期的  注意K线数据是最新的
        # 情况1: 直接提取   情况2: 算出最新的EMA数据
        try:
            date_index = list(data.index).index(date)  # 给定日期的数组下标
        except ValueError:  # 给的日期太新导致越界 判断是情况1与情况2
            date_index = 99999999999  # 保证数组越界

        # 获取LLV(N)
        try:
            llvs = data[f'llv{n}'].to_numpy()  # 若没有LLV(N)数据会抛出KeyError
            if str(llvs[date_index]) == 'nan':
                raise RuntimeError
        except (KeyError, RuntimeError, IndexError):
            # 没有数据 计算出全部的LLV(n)值
            llvs = self.llv(lows, n)
            global_data.add_column(self.stock, 'llv%s' % n, llvs)  # 计算完毕 保存值到总表

        # 获取HHV(N)
        try:
            hhvs = data[f'hhv{n}'].to_numpy()  # 若没有HHV(N)数据会抛出KeyError
            if str(hhvs[date_index]) == 'nan':
                raise RuntimeError
        except (KeyError, RuntimeError, IndexError):
            # 没有数据 计算出全部的HHV(n)值
            hhvs = self.hhv(highs, n)
            global_data.add_column(self.stock, 'hhv%s' % n, hhvs)  # 计算完毕 保存值到总表

        rsv = (closes - llvs) / (hhvs - llvs) * 100
        if str(rsv[0]) == 'nan':  # 若第一天停牌 则hhv-llv等于0 相除之后会变成nan 导致之后的计算全部错误
            rsv[0] = 0

        k = self.sma(rsv, m, 1)  # array
        d = self.sma(k, m, 1)  # array
        j = pd.Series(3 * k - 2 * d, index=data.index)  # series

        # 计算KDJ需要较多运算 不能直接读取(要算SMA) 所以把结果暂时存下来
        self.temp_saved_values = j   # series

        try:
            date_index = list(data.index).index(date)  # 给定日期的数组下标
            return j[date_index]
        except ValueError:  # 当天停牌
            return j[-1]  # 尝试返回最近的数据
