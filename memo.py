from typing import Dict

import numpy as np


class Memo:
    def __init__(self):
        self._data: Dict[str, np.ndarray] = {}  # key由symbol-column拼装而成，如 {'000001-ma5': np.array([...])}

    def contains(self, symbol: str, name: str) -> bool:
        return f'{symbol}-{name}' in self._data

    def get(self, symbol: str, name: str):
        """ 若不存在将抛出异常, 应先调用contains()判断 """
        return self._data[f'{symbol}-{name}']

    def set(self, symbol: str, name: str, array: np.ndarray):
        self._data[f'{symbol}-{name}'] = array
