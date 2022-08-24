import mmap
from pathlib import Path

import numpy as np

base_dir = Path('__data__')
test_file = base_dir / Path('mmap_2np_test.dat')


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


def open_mmap(mm_fid=None, rw=mmap.ACCESS_WRITE):
    _mm = mmap.mmap(mm_fid.fileno(), length=0, access=rw)
    return _mm


create_dummy_file()

print('testing reading of file')
fid = open(test_file, 'rb')
mm = open_mmap(fid, rw=mmap.ACCESS_READ)
data = np.frombuffer(mm[:], dtype=np.uint32)
print(data)
fid.close()

print('testing writing of file')
fid = open(test_file, 'r+b')
mm_read = open_mmap(fid, rw=mmap.ACCESS_READ)
mm = open_mmap(fid, rw=mmap.ACCESS_WRITE)
data = np.arange(11, 21, 1, dtype=np.uint32)
mm_len = len(mm_read)
mm.resize(mm_len + len(data)*4)
print(f'data buffer len is {len(data.tobytes())}')
mm[mm_len:mm_len + len(data)*4] = data.tobytes()
fid.flush()
fid.close()

print('testing writing to file with a read ptr open')
fid_read = open(test_file, 'rt')
print(f'Read file first 5 items: {np.frombuffer(mm[0:20],dtype=np.uint32)}')
fid = open(test_file, 'r+b')

mm = open_mmap(fid, rw=mmap.ACCESS_WRITE)

mm_len = len(mm)
print(f'mm_len is {mm_len}')
data = np.arange(21, 31, 1, dtype=np.uint32)
mm.resize(mm_len + len(data)*4)
mm[mm_len:mm_len + len(data)*4] = data.tobytes()
fid.flush()
mm_len = len(mm)
print(f'mm_len is {mm_len}')
stride = int(mm_len/4/10)
# JWK, python mmap seems to read only byte-level data therefore slicing does not work well as we need to group bytes
data = mm[::stride]
print(data)
print(f'read 10 samples equally spaced: {np.frombuffer(data, dtype=np.uint32)}')
print(f'Read file next 5 chars: {np.frombuffer(fid_read.read(5, dtype=np.uint32))}')

fid.close()


