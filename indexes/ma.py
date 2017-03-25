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
        """ 获取给定日期的 days日均线 假定已有最新的K线数据 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None

        # 数据库存在分2种情况 有当天K线数据且已经算出来 有K线但NaN
        # 尝试从已有数据读取 读取成功马上返回
        try:
            result = data.loc[date, 'ma%s' % days]  # 若没有K线数据会抛出KeyError
            self.temp_saved_values = data['ma%s' % days]  # 暂存该股的所有MAn数据以备用
            if str(result) != 'nan':  # 有K线但NaN result不是简单的np.nan
                return result
            else:
                raise RuntimeError
        except (KeyError, RuntimeError):
            # 没有数据
            closes = data['close']

        # 计算MA
        if len(closes) > days:  # 避免只有50天数据却计算了MA90的问题 否则求卷积后提取时会有问题
            ma = self.ma(closes, days)
            new_data = global_data.add_column(self.stock, 'ma%s' % days, ma)  # 计算出来后填入总表
            self.temp_saved_values = data['ma%s' % days]  # 暂存该股的所有MAn数据以备用
            try:
                return new_data.loc[date, 'ma%s' % days]  # 最终返回对应日期的MA值
            except KeyError:  # 该日停牌 返回nan
                return np.nan
        else:
            return np.nan
