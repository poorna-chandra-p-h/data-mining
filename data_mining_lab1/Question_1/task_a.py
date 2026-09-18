import os
import shutil
import glob

# Base directory for the partitioned lakehouse layout
target_base = "annapurna-lake/sales/"
os.makedirs(target_base, exist_ok=True)

# Look for all sales files inside the 'sales' directory (and root just in case)
files = glob.glob("sales/SALES_*.*") + glob.glob("SALES_*.*")

for filepath in files:
    filename = os.path.basename(filepath)
    parts = filename.split('_')
    if len(parts) < 3:
        continue
        
    store_id = parts[1]                     # e.g., "S12"
    date_str = parts[2].split('.')[0]       # e.g., "20240827"
    
    year = date_str[:4]                     # "2024"
    month = date_str[4:6]                   # "08"
    
    # Hive partition directory: annapurna-lake/sales/year=YYYY/month=MM/store=SXX/
    target_dir = os.path.join(target_base, f"year={year}", f"month={month}", f"store={store_id}")
    os.makedirs(target_dir, exist_ok=True)
    
    # Copy file into target partition
    shutil.copy(filepath, os.path.join(target_dir, filename))
    
print(f"Successfully partitioned {len(files)} files into {target_base}")