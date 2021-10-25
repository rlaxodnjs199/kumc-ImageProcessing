# Usage
# - python update_datasheet.py
# Dependency
# - VidaDatasheet.xlsx
# Global Variable -----------------------------------------------------------
XLSX_PATH = r"E:\common\Taewon\oneDrive\OneDrive - University of Kansas Medical Center\VidaSheet.xlsx"
# ---------------------------------------------------------------------------

import pandas as pd

df = pd.read_excel(XLSX_PATH)
print(df.head())