# Copyright (C) 2020. Huawei Technologies Co., Ltd. All rights reserved.
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
import os
from random import randrange
import sys
import logging
from time import time
import ctypes
from contextlib import contextmanager
import atexit


@contextmanager
def timeit(name: str):
    start = time()
    yield
    ellapsed_time = (time() - start) * 1000

    logging.info(f'"{name}" took: {ellapsed_time:4f}ms')


libc = ctypes.CDLL(None)
try:
    c_stdout = ctypes.c_void_p.in_dll(libc, "stdout")
except:
    # macOS
    c_stdout = ctypes.c_void_p.in_dll(libc, "__stdoutp")


@contextmanager
def surpress_stdout():
    original_stdout_fno = sys.stdout.fileno()

    # XXX: Range is to prevent collisions if there are race conditions with multiple
    #      processes calling redirect_stdout.
    dup_stdout_fno = randrange(5, 128)
    os.dup2(original_stdout_fno, dup_stdout_fno)
    # dup_stdout_fno = os.dup(original_stdout_fno)

    devnull_fno = os.open(os.devnull, os.O_WRONLY)
    os.dup2(devnull_fno, original_stdout_fno)
    sys.stdout = os.fdopen(devnull_fno, "w")

    try:
        yield
    finally:
        sys.stdout.flush()
        libc.fflush(c_stdout)
        os.fsync(devnull_fno)
        os.close(devnull_fno)

        os.dup2(dup_stdout_fno, original_stdout_fno)
        os.fsync(dup_stdout_fno)

        sys.stdout = os.fdopen(dup_stdout_fno, "w")

        def close():
            sys.stdout.close()

        atexit.register(close)
