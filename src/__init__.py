"""JAGA-KODE Source Package"""
import numpy as np

# Kompatibilitas mundur NumPy 2.x polyfill
if not hasattr(np, "unicode_"):
    np.unicode_ = np.str_
