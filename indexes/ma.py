#!/usr/bin/python3
# -*- encoding: utf8 -*-

import numpy as np
from indexes.base import Index
import global_data


class MA(Index):
    """ 简单移动平均线 """

    def __init__(self, stock):
        super().__init__(stock)

    def get_ma(self, date, days=5):
        """ 获取给定日期的 days日均线 """
        data = global_data.get_data(self.stock)  # returns dataframe or None
        if data is not None:
            closes = data['close']  # 当前有数据则提取出该股的全部收盘价 注意是全部
        else:
            # 当前无数据则从网上获取 再提取收盘价
            global_data.add_data(self.stock, start='2016-01-01')
            data = global_data.get_data(self.stock)
            closes = data['close']

        if len(closes) > days:  # 避免只有50天数据却计算了MA90的问题 否则求卷积后提取时会有问题
            weights = np.ones(days) / days  # 权重相等
            ma = np.convolve(weights, closes)[days-1:1-days]  # 求出(closes-days+1)天的MA(days) 最早的(days-1)天缺数据
            ma = np.concatenate( (np.array([np.nan] * (days-1)), ma) )  # 缺数据所以填入(days-1)个nan 确保长度相等日期对齐
            global_data.add_column(self.stock, 'ma%s' % days, ma)  # 计算出来后填入总表
            
            new_data = global_data.get_data(self.stock)
            # print('after calculating\n' + str(new_data)  # for debugging
            return new_data.loc[date, 'ma%s' % days]  # 最终返回对应日期的MA值
        else:
            return np.nan
