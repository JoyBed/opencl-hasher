#!/usr/bin/python3
# -*- coding: utf-8 -*-
import sys
import hashlib
import binascii
import functools, operator
from Library import opencl
from Library.opencl_information import opencl_information
from collections import deque

def sha1_test(opencl_algo, hash1):
    print("sha1 ..")
    ctx=opencl_algo.cl_sha1_init()
    clresult=opencl_algo.cl_sha1(ctx,hash1)
    
    hashed = str(binascii.hexlify(clresult[0]))
    
    print(hashed)

def main(argv):
    if (len(argv)<2):
        info=opencl_information()
        info.printplatforms()
        print("\nExpected format: python test.py [platform number]")
        return

    hash1 = [b'abc']
    print(str(type(hash1)))

    platform = int(argv[1])
    debug = 1
    write_combined_file = False
    opencl_algos = opencl.opencl_algos(platform, debug, write_combined_file,inv_memory_density=1)
    
    sha1_test(opencl_algos,hash1)

    print("finished")

if __name__ == '__main__':
  main(sys.argv)
