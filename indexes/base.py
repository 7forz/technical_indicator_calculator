#!/usr/bin/python3
# -*- encoding: utf-8 -*-

import numba
import numpy as np
import pandas as pd


class Index():
    """ 指标基类 """

    def __init__(self, stock):
        self.stock = stock

    def ma(self, array:np.ndarray, days:int) -> np.ndarray:
        """ 计算简单移动平均线 传入一个array和days 返回一个array """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        ma_array = calc_ma(array, days)
        return ma_array

    def ema(self, array:np.ndarray, days:int) -> np.ndarray:
        """ 计算指数移动平均线 传入一个array和int 返回一个array """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        ma_array = calc_ma(array, days)
        return ma_array

    def sma(self, array:np.ndarray, n:int, m:int) -> np.ndarray:
        """ 计算array的n日移动平均 m为权重  ema相当于sma(x,n+1,2) """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        sma_array = calc_sma(array, n, m)
        return sma_array

    def llv(self, array:np.ndarray, n:int) -> np.ndarray:
        """ n日内最低价的最低值 从数据的第一天开始往后计算 """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        llv_array = calc_llv(array, n)
        return llv_array

    def hhv(self, array:np.ndarray, n:int) -> np.ndarray:
        """ n日内最高价的最高值 """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        hhv_array = calc_hhv(array, n)
        return hhv_array

    def avedev(self, array, n):
        """ 平均绝对误差 一定区间内的值与该区间MA的差的绝对值之平均 """
        if isinstance(array, pd.Series):
            array = array.to_numpy()
        avedev_array = calc_avedev(array, n)
        return avedev_array

    def previous_value(self, date, n):
        """ 获取给定日期n天前的指标值 由于各不相同 应分别重写该方法 """
        pass

    def next_value(self, date, n):
        """ 获取给定日期n天后的指标值 由于各不相同 应分别重写该方法 """
        pass


@numba.jit(nopython=True)
def calc_ma(array:np.ndarray, days:int) -> np.ndarray:
    """ 计算简单移动平均线 传入一个array和days 返回一个array """
    _weights = np.ones(days) / days  # 权重相等
    ma = np.convolve(_weights, array)[days-1:1-days]  # 求出(array-days+1)天的MA(days) 最早的(days-1)天缺数据
    ma = np.concatenate((np.array([np.nan] * (days-1)), ma))  # 缺数据所以填入(days-1)个nan 确保长度相等日期对齐
    assert len(array) == len(ma)
    return ma

@numba.jit(nopython=True)
def calc_ema(array:np.ndarray, days:int) -> np.ndarray:
    """ 计算指数移动平均线 传入一个array和int 返回一个array """
    _result = [0.0] * len(array)
    _result[0] = array[0]  # result初始值定为array的初值
    for i in range(1, len(array)):  # 后面的进行递归计算
        # EMA(N) = 前一日EMA(N) X (N-1)/(N+1) + 今日收盘价 X 2/(N+1)
        # e.g.
        # EMA(9) = 前一日EMA(9) X 8/10 + 今日收盘价 X 2/10
        _result[i] = _result[i-1] * (days-1) / (days+1) + array[i] * 2 / (days+1)
    return np.array(_result)  # 返回一个np.array而不是list对象 list对象不能运算

@numba.jit(nopython=True)
def calc_sma(array:np.ndarray, n:int, m:int) -> np.ndarray:
    """ 计算array的n日移动平均 m为权重  ema相当于sma(x,n+1,2) """
    _result = [0.0] * len(array)
    _result[0] = array[0]  # result初始值定为array的初值
    for i in range(1, len(array)):  # 后面的进行递归计算
        # SMA(N,M) = 前一日SMA(N) X (N-M)/N + 今日收盘价 X M/N
        # e.g.
        # SMA(6,1) = 前一日SMA(6) X 5/6 + 今日收盘价 X 1/6
        _result[i] = _result[i-1] * (n-m) / n + array[i] * m / n
    return np.array(_result)  # 返回一个np.array而不是list对象 list对象不能运算

@numba.jit(nopython=True)
def calc_llv(array:np.ndarray, n:int) -> np.ndarray:
    """ n日内最低价的最低值 从数据的第一天开始往后计算 """
    assert n > 1, 'n应>=2'
    _result = []
    for i in range(len(array)):
        if i >= n:
            _result.append(min(array[i-n+1:i+1]))
        else:  # 初始的几天 数据不够
            _result.append(min(array[:i+1]))
    return np.array(_result)  # 返回一个np.array而不是list对象 list对象不能运算

@numba.jit(nopython=True)
def calc_hhv(array:np.ndarray, n:int) -> np.ndarray:
    """ n日内最高价的最高值 """
    assert n > 1, 'n应>=2'
    _result = []
    for i in range(len(array)):
        if i >= n:
            _result.append(max(array[i-n+1:i+1]))
        else:  # 初始的几天 数据不够
            _result.append(max(array[:i+1]))
    return np.array(_result)  # 返回一个np.array而不是list对象 list对象不能运算

@numba.jit(nopython=True)
def calc_avedev(array:np.ndarray, n:int):
    """ 平均绝对误差 一定区间内的值与该区间MA的差的绝对值之平均 """
    assert len(array) > n
    ma = calc_ma(array, n)

    _result = [np.nan] * len(array)
    for i in range(n-1, len(array)):
        _sum = 0
        for j in range(n):
            _sum += abs(array[i-j] - ma[i])  # i-n ~ i-1
        _sum /= n
        _result[i] = _sum
    return np.array(_result)
