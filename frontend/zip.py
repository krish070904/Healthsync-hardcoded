import shutil

# Folder path
folder_to_zip = r"D:\kaggle"

# Output zip path (will be in D:\healthsync_clean)
output_zip = r"D:\kaggle"

shutil.make_archive(output_zip, 'zip', folder_to_zip)
