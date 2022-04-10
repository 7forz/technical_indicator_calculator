#!/usr/bin/python3
# -*- encoding: utf-8 -*-

from typing import List

def bin_search(l: List, item):
    """ 传入一个递增的数组, 返回一个偏移量, 该偏移量对应数组的值是大于等于给定item的第一个偏移量, 若item大于数组最大值将返回最末的偏移量 """
    left = 0
    right = len(l) -1
    while left < right:
        mid = (left + right) // 2
        if item == l[mid]:
            return mid
        elif item > l[mid]:
            left = mid + 1
        else:
            right = mid - 1
    return left
