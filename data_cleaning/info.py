import os
if __name__ == '__main__':
    base_dir = '/media/vidi/Data/raw/splits/splits/'
    # files = os.listdir(base_dir)
    mid_files = [f for f in os.listdir(base_dir) if f.endswith('header.tsv')]
    print(len(mid_files)/2)