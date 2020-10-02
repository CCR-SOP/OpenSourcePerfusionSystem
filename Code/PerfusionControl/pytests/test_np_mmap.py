import mmap
from pathlib import Path
from os import SEEK_END

import numpy as np

base_dir = Path('__data__')
test_file = base_dir / Path('mmap_np_test.dat')


def create_dummy_file():
    print('Creating dummy file')
    _fid = open(test_file, 'wb')
    tmp_data = np.arange(1, 11, 1, dtype=np.uint32)
    _fid.write(tmp_data.tobytes())
    print(tmp_data.tobytes())
    _fid.close()


def print_file():
    print('====test_file contains:')
    _fid = open(test_file, 'r')
    print(_fid.read())
    print('====EOF')
    _fid.close()


def open_mmap(mm_fid=None, rw='r', file_size=1):
    _mm = np.memmap(mm_fid, dtype=np.uint32, mode=rw)
    return _mm


create_dummy_file()

print('testing reading of file')
fid = open(test_file, 'rb')
mm = open_mmap(fid, 'r')
print(mm)
fid.close()

print('testing writing of file')
fid = open(test_file, 'r+b')
mm_read = open_mmap(fid, 'r+')
data = np.arange(11, 21, 1, dtype=np.uint32)
data.tofile(fid)
fid.flush()
fid.close()
print_file()

print('testing writing to file with a read ptr open')
fid = open(test_file, 'r+t')
fid_read = open(test_file, 'r')
fid_read.seek(0, SEEK_END)
mm_len = int(fid_read.tell() / 4)
print(f'mm_len is {mm_len}')
data = np.arange(21, 31, 1, dtype=np.uint32)
fid.seek(0, SEEK_END)
data.tofile(fid)
fid.flush()
fid_read.seek(0, SEEK_END)
mm_len = int(fid_read.tell() / 4)
print(f'mm_len is {mm_len}')

stride = int(mm_len/10)
fid.seek(0)
mm = open_mmap(fid_read, 'r', mm_len)
print(f'stride is {stride}')
print(mm[0:mm_len])
print(mm[0:mm_len:stride])

fid.close()
fid_read.close()


