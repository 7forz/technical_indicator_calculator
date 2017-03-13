#!/usr/bin/python3
# -*- encoding: utf8 -*-

import numpy as np
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

    def _ema(self, array, days):
        """ 计算指数移动平均线 传入一个array和days 返回一个array """
        _result = [array[0]]  # result初始值定为array的初值
        for i in range(1, len(array)):  # 后面的进行递归计算
            # EMA(N) = 前一日EMA(N) X (N-1)/(N+1) + 今日收盘价 X 2/(N+1)
            # e.g.
            # EMA(9) = 前一日EMA(9) X 8/10 + 今日收盘价 X 2/10
            _result.append(_result[i-1] * (days-1) / (days+1) + array[i] * 2 / (days+1))
        assert len(array) == len(_result)
        return np.array(_result)  # 返回一个np.array而不是list对象

    def get_macd(self, date, short=12, long=26, mid=9):
        """ 获取给定日期的MACD """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None

        if data is not None:
            date_index = np.where(data.index == date)[0][0]  # 给定日期的数组下标 where返回(array([123]),)
            # 数据库存在分3种情况 有当天K线数据且已经算出来EMA 有K线但NaN 和没有K线数据
            # 尝试从已有数据读取

            # 获取EMA(CLOSE,SHORT)和EMA(CLOSE,LONG)
            try:
                ema_short = data.loc[:, 'ema%s' % short]  # 若没有EMA(N)数据会抛出KeyError
                if not ema_short[date_index]:
                    raise RuntimeError
            except (KeyError, RuntimeError):
                # 没有数据 更新数据到最新 并计算出全部的EMA(short)值
                data = global_data.update_data(self.stock)
                closes = data['close']
                ema_short = self._ema(closes, short)
            
            try:
                ema_long = data.loc[:, 'ema%s' % long]  # 若没有EMA(N)数据会抛出KeyError
                if not ema_long[date_index]:
                    raise RuntimeError
            except (KeyError, RuntimeError):
                # 没有数据 更新数据到最新 并计算出全部的EMA(long)值
                data = global_data.update_data(self.stock)
                closes = data['close']
                ema_long = self._ema(closes, long)
        else:
            # 无该股K线数据则从网上获取 再提取收盘价
            data = global_data.add_data(self.stock, start='2016-01-01')
            closes = data['close']
            ema_short = self._ema(closes, short)
            ema_long = self._ema(closes, long)
        # 计算完毕 保存EMA(N)的值到总表
        new_data = global_data.add_column(self.stock, 'ema%s' % short, ema_short)
        new_data = global_data.add_column(self.stock, 'ema%s' % long, ema_long)

        # DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        dif = ema_short - ema_long  # np.array
        
        # DEA:EMA(DIF,MID);
        dea = self._ema(dif, mid)  # np.array
        
        # MACD:(DIF-DEA)*2;
        macd = (dif - dea) * 2  # np.array
        
        date_index = np.where(data.index == date)[0][0]  # 给定日期的数组下标
        return macd[date_index]
