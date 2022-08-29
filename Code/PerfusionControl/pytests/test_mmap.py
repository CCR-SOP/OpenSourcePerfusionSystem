# -*- coding: utf-8 -*-
""" Unit test for testing mmap capabilities

This work was created by an employee of the US Federal Gov
and under the public domain.

Author: John Kakareka
"""
import pytest
import mmap
from pathlib import Path

DUMMY_DATA = 'This is a test'.encode('utf-8')

@pytest.fixture()
def data_file(tmp_path_factory):
    fn = tmp_path_factory.mktemp('data') / 'test.dat'
    _fid = open(fn, 'wb')
    _fid.write(DUMMY_DATA)
    _fid.close()
    return fn

def setup_module(module):
    print("setup_module      module:{}".format(module.__name__))


def teardown_module(module):
    print("teardown_module      module:{}".format(module.__name__))


def setup_function(function):
    print("setup_function      module:{}".format(function.__name__))


def teardown_function(function):
    print("teardown_function      module:{}".format(function.__name__))


def test_mmap_write(data_file):
    fid = open(data_file, 'r+b')
    mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_WRITE)
    data = 'more data'.encode('utf-8')
    mm_len = len(mm)
    assert mm_len == len(DUMMY_DATA)

    mm.resize(mm_len + len(data))
    assert len(mm) == mm_len + len(data)

    mm[mm_len:mm_len + len(data)] = data
    fid.flush()

    assert mm[:] == DUMMY_DATA + data

    fid.close()


def test_mmap_read(data_file):
    fid = open(data_file, 'r+b')
    mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_READ)
    assert len(mm) == len(DUMMY_DATA)
    assert mm[:] == DUMMY_DATA
    fid.close()


def test_mmap_read_and_write_simultaneously(data_file):
    fid_read = open(data_file, 'rb')
    data = fid_read.read(5)
    assert data == DUMMY_DATA[0:5]

    fid = open(data_file, 'r+b')
    mm = mmap.mmap(fid.fileno(), length=0, access=mmap.ACCESS_WRITE)

    data = mm[-5:]
    assert data == DUMMY_DATA[-5:]

    mm_len = len(mm)
    new_data = 'more data again'.encode()
    mm.resize(mm_len + len(new_data))
    mm[mm_len:mm_len + len(new_data)] = new_data

    assert mm[-5:] == new_data[-5:]

    fid.flush()

    expected = DUMMY_DATA + new_data
    data = fid_read.read(5)
    assert data == expected[5:10]
