import os
current_dir = os.path.abspath(__file__)
parent_dir = os.path.dirname(current_dir) 
OUTPUT_DIR = os.path.join(parent_dir, "pdf_exports")
print(OUTPUT_DIR)