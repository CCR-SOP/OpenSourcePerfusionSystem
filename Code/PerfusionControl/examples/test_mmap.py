# this is a comment
import mmap
from pathlib import Path

base_dir = Path('__data__')
test_file = base_dir / Path('mmap_test.dat')


def create_dummy_file():
    print('Creating dummy file')
    _fid = open(test_file, 'wt')
    print('This is a test', file=_fid)
    _fid.close()


def print_file():
    print('====test_file contains:')
    _fid = open(test_file, 'rt')
    print(_fid.read())
    print('====EOF')
    _fid.close()


create_dummy_file()

print('testing reading of file')
fid = open(test_file, 'r+b')
mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_READ)
print(mm[:])
fid.close()

print('testing writing of file')
fid = open(test_file, 'r+t')
mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_WRITE)
data = bytearray('more data'.encode())
mm_len = len(mm)
print(f'len of data is {len(data)}')
print(f'len of slice is {mm_len + len(data)}')
mm.resize(mm_len + len(data))
mm[mm_len:mm_len + len(data)] = data
print(mm[:])
fid.flush()
fid.close()
print_file()

print('testing writing to file with a read ptr open')
fid_read = open(test_file, 'rt')
print(f'Read file first 5 chars: {fid_read.read(5)}')
fid = open(test_file, 'r+t')
print(f'last 5 bytes are: {mm[-5:]}')
mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_WRITE)
print(f'last 5 bytes are: {mm[-5:]}')
print('adding data again')
mm_len = len(mm)
data = data = bytearray('more data again'.encode())
mm.resize(mm_len + len(data))
mm[mm_len:mm_len + len(data)] = data
print(f'last 5 bytes are: {mm[-5:]}')
print("flushing")
fid.flush()
print(f'last 5 bytes are: {mm[-5:]}')
print(f'Read file next 5 chars: {fid_read.read(5)}')

fid.close()


