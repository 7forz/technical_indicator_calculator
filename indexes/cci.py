#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numpy as np

from indexes.base import Index
import global_data


class CCI(Index):
    """
    TYP:=(HIGH+LOW+CLOSE)/3;
    CCI:(TYP-MA(TYP,N))/(0.015*AVEDEV(TYP,N));
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_cci(self, date, days=14):
        """ 获取给定日期的 days日CCI """
        data = global_data.get_data(self.stock)

        # 数据库存在分2种情况 有当天K线数据且已经算出来 有K线但NaN
        # 尝试从已有数据读取 读取成功马上返回
        try:
            result = data.loc[date, f'cci{days}']  # 若没有对应数据会抛出KeyError
            if str(result) != 'nan':  # 有K线但NaN result不是简单的np.nan
                return result
            else:
                raise RuntimeError
        except (KeyError, RuntimeError):
            # 没有所需的CCI数据 将在下面计算
            pass

        typ = (data['high'].to_numpy() + data['low'].to_numpy() + data['close'].to_numpy()) / 3  # series
        cci = (typ - self.ma(typ, days)) / (0.015 * self.avedev(typ, days))

        new_data = global_data.add_column(self.stock, f'cci{days}', cci)  # 计算出来后填入总表

        try:
            return new_data.loc[date, f'cci{days}']  # 最终返回对应日期的CCI值
        except KeyError:  # 该日停牌 返回nan
            return np.nan
