# datalog.py
# VCC	IN_T_O_HL	IN_T_O_LH	TDIS	TEN	TIDLE_HL
# 5.5	3.2 ns	3.5 ns	6.8 ns	7.1 ns	3.0 ns

import pandas as pd
import os

def save_results(data_list, filename, sheet_name='Sheet1'):
    df_new = pd.DataFrame(data_list)

    if os.path.exists(filename):
        with pd.ExcelWriter(filename, engine='openpyxl', mode='a', if_sheet_exists='replace') as writer:
            df_new.to_excel(writer, sheet_name=sheet_name, index=False)
    else:
        df_new.to_excel(filename, sheet_name=sheet_name, index=False)
