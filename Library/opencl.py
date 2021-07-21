#!/usr/bin/python3
# -*- coding: utf-8 -*-
'''
    SHA1 PyOpenCl implementation
    MIT License
    Implementation was confirmed to work with Intel OpenCL on Intel(R) HD Graphics 520 and Intel(R) Core(TM) i5-6200U CPU
'''

from Library.buffer_structs import buffer_structs
import pyopencl as cl
import numpy as np
import binascii
from binascii import hexlify
import os
from itertools import chain, repeat, zip_longest
from binascii import unhexlify
from collections import deque
import time
import os, sys, inspect
import math

current_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
parent_dir = os.path.dirname(current_dir)

# Corresponding to opencl (CAN'T BE CHANGED):
r = 8
BLOCK_LEN_BYTES = 128 * r

# Little helper, (22,5) -> 5,5,5,5,2.  itertools is bae
def takeInChunks(n,d):
    assert d > 0 and n >= 0
    return chain(repeat(d, n // d), filter(lambda x:x!=0, [n % d]))
def printif(b, s):
    if b:
        print(s)

class opencl_interface:
    debug=False
    inv_memory_density=1
    # Initialiser for the key properties
    #   pbkdf related initialisation removed, will reappear somewhere else
    def __init__(self, platformNum, debug=0, write_combined_file=False, maxWorkgroupSize=60000, inv_memory_density=1,
                 N_value=15, openclDevice = 0):
        self.workgroupsize = 0
        self.computeunits = 0
        self.wordSize = None
        self.N = None
        self.wordType = None
        printif(debug, "Using Platform %d:" % platformNum)
        device = cl.get_platforms()[platformNum].get_devices()[openclDevice]
        self.platform_number = platformNum
        # Show devices for the platform, and adjust workgroup size
        # Create the context for GPU/CPU
        # Adjust workgroup size so that we don't run out of RAM:

        self.inv_memory_density = inv_memory_density
        self.ctx = cl.Context([device])
        self.queue = cl.CommandQueue(self.ctx, device)
        self.debug = debug
        self.available_memmory = 0
        #for device in devices:
        #    printif(debug, '--------------------------------------------------------------------------')
        #    printif(debug, ' Device - Name: ' + device.name)
        #    printif(debug, ' Device - Type: ' + cl.device_type.to_string(device.type))
        #    printif(debug, ' Device - Compute Units: {0}'.format(device.max_compute_units))
        #    printif(debug, ' Device - Max Work Group Size: {0:.0f}'.format(device.max_work_group_size))
        #    printif(debug, ' Device - Global memory size: {}'.format(device.global_mem_size))
        #    printif(debug, ' Device - Local memory size:  {}'.format(device.local_mem_size))
        #    printif(debug, ' Device - Max clock frequency: {} MHz'.format(device.max_clock_frequency))

        self.workgroupsize = device.max_work_group_size*20
        self.computeunits = device.max_compute_units   
        self.available_memmory = device.local_mem_size

        printif(debug, "\nUsing work group size of %d\n" % self.workgroupsize)

        # Set the debug flags
        os.environ['PYOPENCL_COMPILER_OUTPUT'] = str(debug)
        self.write_combined_file = write_combined_file


    def compile(self, bufferStructsObj, library_file, footer_file=None, N=15, invMemoryDensity=2):

        src_file = open(os.path.join('.', 'Library', 'worker', 'generic', 'sha1.cl'), 'r')
        src = src_file.read()
        src_file.close()
        src.replace('\r\n','\n')

        # Kernel function instantiation. Build returns self.
        prg = cl.Program(self.ctx, src).build(cache_dir='./')
        return prg


    def run(self,  
            func, 
            pwdIter,
            expected_hash,
            paddedLenFunc,
            last_hash,
            start,
            end,
            max_batch_size):
        '''
        if max_batch_size == -1 - will use maximum available batch size
        '''

        ctx=self.ctx
        queue=self.queue


        # Allocate data
        last_hash_array = np.frombuffer(last_hash,dtype=np.ubyte)
        #last_hash_size_uint = np.uint32(len(last_hash))     
        result_byte_array = np.zeros(2,dtype=np.uint64)
        expected_hash_array = np.frombuffer(expected_hash,dtype=np.ubyte)
        found_array = np.zeros(1,dtype=np.ubyte)

        # Allocate memory for variables on the device
        last_hash_buffer = cl.Buffer(ctx,
                                     cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                     hostbuf=last_hash_array)
        result_byte_array_buffer = cl.Buffer(ctx,cl.mem_flags.WRITE_ONLY | cl.mem_flags.USE_HOST_PTR,
                                             hostbuf=result_byte_array)
        expected_hash_buffer = cl.Buffer(ctx,
                                        cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                        hostbuf=expected_hash_array)
                                        
        found_buffer = cl.Buffer(ctx,
                                 cl.mem_flags.READ_WRITE | cl.mem_flags.COPY_HOST_PTR,
                                 hostbuf=found_array)

        batch_size = ((end-start)//self.workgroupsize)+1
        if max_batch_size != -1:
            if batch_size > max_batch_size:
                batch_size = max_batch_size
        else:
            print("USING MAX BATCH SIZE, F TO YOUR GPU")

        batch_size_uint = np.uint64(batch_size)

        #debug = np.zeros(1,dtype = np.uint32)
        #debug_buffer = cl.Buffer(ctx,cl.mem_flags.WRITE_ONLY,debug.nbytes)

        # Main loop is taking chunks of at most the workgroup size
        for i in range(start,end,batch_size*self.workgroupsize):
            
            workgroup_size = self.workgroupsize
            #if i + workgroup_size>end:
            #    workgroup_size = end-i
             
            result_byte_array[0] = 0
            result_byte_array[1] = 1
            found_array[0] = 0

            start_uint = np.uint64(i)
            #if i+workgroup_size*batch_size > 111802225 and i < 111802225:
            #    a = 1+1

            # Call Kernel. Automatically takes care of block/grid distribution
            pwdim = (workgroup_size,)
           
            func(self,
                 pwdim,
                 last_hash_buffer,
                 #last_hash_size_uint, 
                 result_byte_array_buffer, 
                 expected_hash_buffer,
                 start_uint,
                 batch_size_uint,
                 found_buffer)

            cl.enqueue_copy(self.queue, 
                            result_byte_array,
                           result_byte_array_buffer)
            #cl.enqueue_copy(self.queue,
            #                debug,
            #                debug_buffer)
            
            if result_byte_array[0] == 1:
                return result_byte_array[1]


        # No main return
        return None



        

        

def mdPad_64_func(self, pwdLen, blockSize):
        # both parameters in bytes
        # length appended as a 64-bit integer
        l = (pwdLen + 1 + 8)
        l += (-l) % blockSize
        return l


class opencl_algos:
    def __init__(self, platform, debug, write_combined_file, inv_memory_density=1, openclDevice = 0):
        if debug==False:
            debug=0
        self.opencl_ctx = opencl_interface(platform, debug, write_combined_file, openclDevice = openclDevice)
        self.platform_number=platform
        self.inv_memory_density=inv_memory_density

    def concat(self, ll):
        return [obj for l in ll for obj in l]




    def cl_sha1_init(self, option=""):
        bufStructs = buffer_structs()
        bufStructs.specifySHA1()
        assert bufStructs.wordSize == 4  # set when you specify sha1
        prg=self.opencl_ctx.compile(bufStructs, 'sha1.cl', option)
        return [prg, bufStructs]

    def cl_sha1(self, ctx, last_hash, expected_hash, start, end, max_batch_size = 2):
        prg = ctx[0]
        def func(s, pwdim, last_hash, result_bytes_array, expected_hash, start, batch_size,found_buffer, debug_buffer=None):
            prg.hash_main(s.queue, pwdim, None, last_hash,start, result_bytes_array, expected_hash, batch_size,found_buffer)
            
        starting_point = 0
        return self.opencl_ctx.run(func, None, expected_hash, mdPad_64_func, last_hash, start, end, max_batch_size)

