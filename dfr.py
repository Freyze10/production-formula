import pandas as pd
from dbfread import DBF

primary = pd.DataFrame(iter(DBF(r'\\system-server\SYSTEM-NEW-OLD\tbl_formula01.dbf')))
print(primary.columns.tolist())

secondary = pd.DataFrame(iter(DBF(r'\\system-server\SYSTEM-NEW-OLD\tbl_formula03.dbf')))

pd.set_option('display.max_columns', None)
pd.set_option('display.width', None)  # Prevent line wrapping
pd.set_option('display.max_colwidth', None)

print(secondary.tail(50))
