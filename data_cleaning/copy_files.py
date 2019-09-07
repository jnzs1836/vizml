import os
from shutil import copyfile, move
if __name__ == '__main__':
    base_dir = '/media/vidi/Data/raw/splits/splits/'
    target_dir = '/media/vidi/Data/raw/splits/p1/'
    if not os.path.exists(target_dir):
        os.mkdir(target_dir)
    # files = os.listdir(base_dir)
    mid_files = [f for f in os.listdir(base_dir) if f.endswith('with_all_fields_and_header.tsv')]
    print(len(mid_files)/2)
    for file in mid_files:
        move(os.path.join(base_dir, file), os.path.join(target_dir, file))
