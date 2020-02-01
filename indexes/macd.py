#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import pandas as pd
from indexes.base import Index
import global_data


class MACD(Index):
    """
        Moving Average Convergence and Divergence 指数平滑异动移动平均线
        通达信软件中的公式为：
        DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        DEA:EMA(DIF,MID);
        MACD:(DIF-DEA)*2;
        共3个参数：short long mid
        核心函数为EMA
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_macd(self, date, short=12, long=26, mid=9):
        """ 获取给定日期的MACD 假定已有最新的K线数据 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None
        assert data is not None, 'must have K-data before using get_macd()!'

        closes = data['close'].to_numpy()  # 到当日的全部收盘价

        # 数据库存在分2种情况 1.已经算出来给定日期的EMA 2.没有给定日期的EMA  注意K线数据是最新的
        # 情况1: 直接提取   情况2: 算出最新的EMA数据
        try:
            date_index = list(data.index).index(date)  # 给定日期的数组下标
        except ValueError:  # 给的日期太新导致越界 判断是情况1与情况2
            date_index = 99999999999  # 保证数组越界

        # 获取EMA(CLOSE,SHORT)
        try:
            ema_short = data[f'ema{short}'].to_numpy()  # 若没有EMA(N)数据会抛出KeyError
            if str(ema_short[date_index]) == 'nan':
                raise RuntimeError
        except (KeyError, RuntimeError, IndexError):
            # 没有数据 计算出全部的EMA(short)值
            ema_short = self.ema(closes, short)
            global_data.add_column(self.stock, f'ema{short}', ema_short)  # 保存EMA(N)的值到总表

        # 获取EMA(CLOSE,LONG)
        try:
            ema_long = data[f'ema{long}'].to_numpy()  # 若没有EMA(N)数据会抛出KeyError
            if str(ema_long[date_index]) == 'nan':
                raise RuntimeError
        except (KeyError, RuntimeError, IndexError):
            # 没有数据 计算出全部的EMA(long)值
            ema_long = self.ema(closes, long)
            global_data.add_column(self.stock, f'ema{long}', ema_long)

        # DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        dif = ema_short - ema_long  # array

        # DEA:EMA(DIF,MID);
        dea = self.ema(dif, mid)

        # MACD:(DIF-DEA)*2;
        macd = pd.Series((dif - dea) * 2, index=data.index)  # 转换为series

        # 计算MACD需要较多运算 不能直接读取(至少要算一次dif的EMA) 所以把结果暂时存下来
        self.temp_saved_values = macd   # series

        try:
            date_index = list(data.index).index(date)  # 给定日期的数组下标
            return macd[date_index]
        except ValueError:  # 当天停牌
            return macd[-1]  # 尝试返回最近的数据

    def previous_value(self, date, n):
        """ 必须先调用get_macd()后再调用此方法 从已计算的MACD数据中获取给定日期n天前的MACD值 """
        data = global_data.get_data(self.stock)
        date_index = list(data.index).index(date)
        return self.temp_saved_values[date_index-n]

    def get_saved_macd(self, date):
        """ 从已经计算的MACD列表中提取值 series可以像字典那样用 也可以像列表那样用 """
        return self.temp_saved_values[date]
