#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numba
import numpy as np
from dto_enum import OHLCV
from global_data import global_data_instance

from indexes.base import Index, ref, sum_recent


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

    def get_dmi(self, symbol: str, date: str, n: int):
        """ 计算所有日期的 PDI、MDI 序列, 返回给定日期的 (PDI, MDI) 值 """

        key_pdi = f'pdi-{n}'
        pdi = None
        if self.computed_memo.contains(symbol, key_pdi):  # 已有计算
            if len(self.computed_memo.get(symbol, key_pdi)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                pdi = self.computed_memo.get(symbol, key_pdi)

        key_mdi = f'mdi-{n}'
        mdi = None
        if self.computed_memo.contains(symbol, key_mdi):  # 已有计算
            if len(self.computed_memo.get(symbol, key_mdi)) == len(global_data_instance.symbol_to_date_list[symbol]):  # 并且array长度相等(数据存在且正确)
                mdi = self.computed_memo.get(symbol, key_mdi)

        if (pdi is not None) and (mdi is not None):
            if date in global_data_instance.symbol_to_date_set[symbol]:
                offset = global_data_instance.find_date_offset(symbol, date)
                return (self.computed_memo.get(symbol, key_pdi)[offset], self.computed_memo.get(symbol, key_mdi)[offset])


        close_array = global_data_instance.get_array_since_date(symbol, OHLCV.CLOSE, global_data_instance.START_DOWNLOAD_DATE)
        high_array = global_data_instance.get_array_since_date(symbol, OHLCV.HIGH, global_data_instance.START_DOWNLOAD_DATE)
        low_array = global_data_instance.get_array_since_date(symbol, OHLCV.LOW, global_data_instance.START_DOWNLOAD_DATE)

        mtr = calc_mtr(high_array, low_array, close_array, n)
        hd: np.ndarray = np.nan_to_num(high_array - ref(high_array, 1))
        ld: np.ndarray = np.nan_to_num(ref(low_array, 1) - low_array)

        dmp = sum_recent(np.where(np.logical_and(hd>0, hd>ld), hd, 0), n)
        dmm = sum_recent(np.where(np.logical_and(ld>0, ld>hd), ld, 0), n)

        pdi = dmp * 100 / mtr
        mdi = dmm * 100 / mtr

        self.computed_memo.set(symbol, key_pdi, pdi)  # 计算出来后填入缓存
        self.computed_memo.set(symbol, key_mdi, mdi)  # 计算出来后填入缓存

        offset = global_data_instance.find_date_offset(symbol, date)
        return (pdi[offset], mdi[offset])


@numba.jit(nopython=True, cache=True)
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

dmi_instance = DMI()
