#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np
import pandas as pd
from indexes.base import Index
import global_data


class MTM(Index):
    """
        MTM 默认参数为N=12, M=6
        DELTA:CLOSE-REF(CLOSE,N);  # 当日收盘价与N日前的收盘价的差
        MTMMA:MA(DELTA,M);  # 求M日移动平均
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_mtm(self, date, n=12, m=6):
        """ 获取给定日期的 MTM(n, m) 假定已有最新的K线数据 计算出来后由于可能性多 不填入数据库 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None
        closes = data['close']

        # DELTA:CLOSE-REF(CLOSE,N)
        # 前n日的收盘价 相当于closes这个series左移了n天 长度少了n所以在开头补上n个初始值0
        ref = np.concatenate((np.array([0]*n), closes[:-n]))
        delta = closes - ref

        # MTMMA:MA(DELTA,M)
        mtm = pd.Series(self.ma(delta, m), index=data.index)  # 转换为series

        # 计算MTM需要较多运算 不能直接读取 所以把结果暂时存下来
        self.temp_saved_values = mtm   # series

        try:
            return mtm.loc[date]  # 最终返回对应日期的MTM值
        except KeyError:  # 该日停牌 返回nan
            return np.nan
