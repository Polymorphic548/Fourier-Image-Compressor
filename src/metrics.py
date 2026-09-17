import math
import numpy as np

def mse(a, b):
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(np.mean((a-b)**2))

def psnr(a, b):
    e = mse(a,b)
    return float("inf") if e == 0 else 20*math.log10(255/math.sqrt(e))

def ratio(original, compressed):
    return original/compressed if compressed else float("inf")

def reduction(original, compressed):
    return (1-compressed/original)*100 if original else 0.0
