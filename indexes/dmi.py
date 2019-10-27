#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numba
import numpy as np
import pandas as pd

import global_data
from indexes.base import Index, sum_recent, ref


class DMI(Index):
    """
        DMI指标
        通达信软件中的公式为：
        MTR:= SUM(MAX(MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1))), ABS(REF(CLOSE, 1) - LOW)), N);
        HD:=  HIGH - REF(HIGH, 1);
        LD:=  REF(LOW, 1) - LOW;
        DMP:= SUM(IF(HD > 0 && HD > LD, HD, 0), N);
        DMM:= SUM(IF(LD > 0 && LD > HD, LD, 0), N);
        PDI:  DMP * 100 / MTR;
        MDI:  DMM * 100 / MTR;

        参数为N
    """

    def __init__(self, stock):
        super().__init__(stock)

    def get_dmi(self, date, n):
        """ 获取给定日期的DMI的PDI,MDI值 假定已有最新的K线数据 """
        data = global_data.get_data(self.stock)  # 数据库存在返回dataframe 否则返回None
        assert data is not None, 'must have K-data before using get_dmi()!'

        close = data['close'].to_numpy()
        high = data['high'].to_numpy()
        low = data['low'].to_numpy()

        mtr = calc_mtr(high, low, close, n)
        hd = high - ref(high, 1)
        ld = ref(low, 1) - low

        dmp = sum_recent(np.where(np.logical_and(hd>0, hd>ld), hd, 0), n)
        dmm = sum_recent(np.where(np.logical_and(ld>0, ld>hd), ld, 0), n)

        pdi = pd.Series(dmp * 100 / mtr, index=data.index)  # series
        mdi = pd.Series(dmm * 100 / mtr, index=data.index)  # series

        # 计算DMI需要较多运算 所以把结果暂时存下来
        self.temp_saved_pdi = pdi   # series
        self.temp_saved_mdi = mdi   # series

        try:
            date_index = list(data.index).index(date)  # 给定日期的数组下标
            return pdi[date_index], mdi[date_index]
        except ValueError:  # 当天停牌
            return pdi[-1], mdi[-1]  # 尝试返回最近的数据


@numba.jit(nopython=True)
def calc_mtr(high: np.ndarray, low: np.ndarray, close: np.ndarray, n: int):
    """
    SUM( MAX( MAX(HIGH - LOW, ABS(HIGH - REF(CLOSE, 1)) ), ABS(REF(CLOSE, 1) - LOW) ), N)
                  ----1-----             -----2-------         -----2-------
                              -----------3-------------    ----------4-------------
              ------------------5------------------------
         ---------------------------------6------------------------------------------
    """
    assert len(close) == len(high) == len(low), 'size must be same'
    assert len(close) > n, 'data too few'

    arr1 = high - low
    arr2 = ref(close, 1)
    arr3 = np.abs(high - arr2)
    arr4 = np.abs(arr2 - low)
    arr5 = np.maximum(arr1, arr3)
    arr6 = np.maximum(arr4, arr5)

    mtr = sum_recent(arr6, n)
    return mtr
