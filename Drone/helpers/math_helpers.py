
#funkcja mapowania z arduino
def map(x, in_min, in_max, out_min, out_max):
    return int((x - in_min)*(out_max - out_min) / (in_max - in_min) + out_min)
# (17060 - 0) * (2000 - 1000) / (65335 - 0) + 1000

