from pathlib import Path
from os import SEEK_END
import logging

import numpy as np

from pyPerfusion.utils import setup_stream_logger

logger = logging.getLogger('test_ai')
setup_stream_logger(logger, logging.DEBUG)

base_dir = Path('__data__')
test_file = base_dir / Path('mmap_np_perf.dat')
SAMPLES_PER_WRITE = 10_000
DATA_TYPE = np.uint32
LAST_NUM = 0


def create_dummy_file():
    logger.debug('Creating dummy file')
    _fid = open(test_file, 'wb')
    write_data(_fid, 0)
    _fid.close()


def open_read():
    _fid = open(test_file, 'r')
    _mm = np.memmap(_fid, dtype=DATA_TYPE, mode='r')
    return _fid, _mm


def open_write():
    _fid = open(test_file, 'r+')
    return _fid


def get_file_size(_fid):
    _fid.seek(0, SEEK_END)
    return int(_fid.tell() / np.dtype(DATA_TYPE).itemsize)


def get_data(_mm, _stride):
    return _mm[::_stride]


def write_data(_fid, start):
    global LAST_NUM
    _data = np.arange(start, start+SAMPLES_PER_WRITE, 1, dtype=DATA_TYPE)
    _data.tofile(_fid)
    _fid.flush()
    LAST_NUM = start + SAMPLES_PER_WRITE


if __name__ == '__main__':
    create_dummy_file()
    fid_write = open_write()

    for i in range(1, 100):
        fid_read, mm = open_read()
        mm_len = get_file_size(fid_read)
        logger.debug(f'file size is {mm_len}')
        stride = int(mm_len / 1000)
        data = get_data(mm, stride)
        logger.debug(f'max is {max(data)}')
        write_data(fid_write, LAST_NUM)
        fid_read.close()

    fid_read.close()
    fid_write.close()


