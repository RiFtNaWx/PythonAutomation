# datalog.py
# VCC	IN_T_O_HL	IN_T_O_LH	TDIS	TEN	TIDLE_HL
# 5.5	3.2 ns	3.5 ns	6.8 ns	7.1 ns	3.0 ns

import pandas as pd
import os

def save_results(data_list, filename):
    df_new = pd.DataFrame(data_list)

    if os.path.exists(filename):
        df_old = pd.read_excel(filename)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_excel(filename, index=False)