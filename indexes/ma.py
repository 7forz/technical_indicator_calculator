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
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None

        if data is not None:
            # 数据库存在分3种情况 有当天K线数据且已经算出来 有K线但NaN 和没有K线数据
            # 尝试从已有数据读取 读取成功马上返回
            try:
                result = data.loc[date, 'ma%s' % days]  # 也可能抛出KeyError
                if str(result) != 'nan':  # result不是简单的np.nan
                    return result
                else:
                    raise KeyError
            except KeyError:
                # 没有数据 更新数据到最新 然后再计算
                data = global_data.update_data(self.stock)
                closes = data['close']
        else:
            # 无该股K线数据则从网上获取 再提取收盘价
            data = global_data.add_data(self.stock, start='2016-01-01')
            closes = data['close']

        if len(closes) > days:  # 避免只有50天数据却计算了MA90的问题 否则求卷积后提取时会有问题
            weights = np.ones(days) / days  # 权重相等
            ma = np.convolve(weights, closes)[days-1:1-days]  # 求出(closes-days+1)天的MA(days) 最早的(days-1)天缺数据
            ma = np.concatenate( (np.array([np.nan] * (days-1)), ma) )  # 缺数据所以填入(days-1)个nan 确保长度相等日期对齐
            new_data = global_data.add_column(self.stock, 'ma%s' % days, ma)  # 计算出来后填入总表

            # print('after calculating\n' + str(new_data.tail()))  # for debugging
            return new_data.loc[date, 'ma%s' % days]  # 最终返回对应日期的MA值
        else:
            return np.nan
