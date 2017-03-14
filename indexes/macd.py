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

    def get_macd(self, date, short=12, long=26, mid=9):
        """ 获取给定日期的MACD """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None

        if data is not None:
            # 数据库存在分3种情况 1.已经算出来给定日期的EMA 2.已经算出给定日期以前的EMA 3.只有K线
            try:
                date_index = np.where(data.index == date)[0][0]  # 给定日期的数组下标 where返回(array([123]),)
            except IndexError:  # 给的日期太新导致越界 判断是情况1与情况2 情况2需要补充数据
                data = global_data.update_data(self.stock)
                date_index = 99999999999  # 保证数组越界

            # 获取EMA(CLOSE,SHORT)和EMA(CLOSE,LONG)
            try:
                ema_short = data['ema%s' % short]  # 若没有EMA(N)数据会抛出KeyError
                if not ema_short[date_index]:
                    raise RuntimeError
            except (KeyError, RuntimeError, IndexError):
                # 没有数据 更新数据到最新 并计算出全部的EMA(short)值
                data = global_data.update_data(self.stock)
                closes = data['close']
                ema_short = self.ema(closes, short)
            
            try:
                ema_long = data['ema%s' % long]  # 若没有EMA(N)数据会抛出KeyError
                if not ema_long[date_index]:
                    raise RuntimeError
            except (KeyError, RuntimeError, IndexError):
                # 没有数据 更新数据到最新 并计算出全部的EMA(long)值
                data = global_data.update_data(self.stock)
                closes = data['close']
                ema_long = self.ema(closes, long)
        else:
            # 无该股K线数据则从网上获取 再提取收盘价
            data = global_data.add_data(self.stock, start='2016-01-01')
            closes = data['close']
            ema_short = self.ema(closes, short)
            ema_long = self.ema(closes, long)
        # 计算完毕 保存EMA(N)的值到总表
        new_data = global_data.add_column(self.stock, 'ema%s' % short, ema_short)
        new_data = global_data.add_column(self.stock, 'ema%s' % long, ema_long)

        # DIF:EMA(CLOSE,SHORT)-EMA(CLOSE,LONG);
        dif = ema_short - ema_long  # np.array
        
        # DEA:EMA(DIF,MID);
        dea = self.ema(dif, mid)  # np.array
        
        # MACD:(DIF-DEA)*2;
        macd = (dif - dea) * 2  # np.array
        
        date_index = np.where(data.index == date)[0][0]  # 给定日期的数组下标
        return macd[date_index]
