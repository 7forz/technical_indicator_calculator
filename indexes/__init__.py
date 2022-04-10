#!/usr/bin/python3
# -*- encoding: utf-8 -*-

from .base import Index

# 下面都使用单例，不要浪费计算得出的数据
from .ma import ma_instance
from .macd import macd_instance
from .rsi import rsi_instance
from .kdj import kdj_instance
from .mtm import mtm_instance
from .cci import cci_instance
from .dmi import dmi_instance
