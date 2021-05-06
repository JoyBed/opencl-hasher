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
from binascii import unhexlify, hexlify
import os
from itertools import chain, repeat, zip_longest
from collections import deque
import time

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
    def __init__(self, platformNum, debug=0, write_combined_file=False, maxWorkgroupSize=60000, inv_memory_density=1, N_value=15, openclDevice = 0):
        printif(debug,"Using Platform %d:" % platformNum)
        devices = cl.get_platforms()[platformNum].get_devices()
        self.platform_number=platformNum
        # Show devices for the platform, and adjust workgroup size
        # Create the context for GPU/CPU
        self.workgroupsize = 0
        self.computeunits = 0
        # Adjust workgroup size so that we don't run out of RAM:
        self.sworkgroupsize = self.determineWorkgroupsize(N_value)
        self.inv_memory_density=inv_memory_density
        self.ctx = cl.Context(devices)
        self.queue = cl.CommandQueue(self.ctx, devices[openclDevice])
        self.debug=debug

        for device in devices:
            printif(debug, '--------------------------------------------------------------------------')
            printif(debug, ' Device - Name: '+ device.name)
            printif(debug, ' Device - Type: '+ cl.device_type.to_string(device.type))
            printif(debug, ' Device - Compute Units: {0}'.format(device.max_compute_units))
            printif(debug, ' Device - Max Work Group Size: {0:.0f}'.format(device.max_work_group_size))
            printif(debug, ' Device - Global memory size: {}'.format(device.global_mem_size))
            printif(debug, ' Device - Local memory size:  {}'.format(device.local_mem_size))
            printif(debug, ' Device - Max clock frequency: {} MHz'.format(device.max_clock_frequency))

            assert device.endian_little == 1, "DEVICE is not little endian : pretty sure we rely on this!"
            if self.workgroupsize == 0:
                self.workgroupsize = maxWorkgroupSize
                self.workgroupsize = min(self.workgroupsize, device.max_work_group_size)
            else:
                self.workgroupsize = min(self.workgroupsize, device.max_work_group_size)
            #if (device.max_work_group_size<self.workgroupsize):
            #    self.workgroupsize=(device.max_work_group_size)*8
            if self.computeunits == 0:
                self.computeunits = device.max_compute_units
            else:
                self.computeunits = min(self.computeunits, device.max_compute_units)
        printif(debug, "\nUsing work group size of %d\n" % self.workgroupsize)

        # Set the debug flags
        os.environ['PYOPENCL_COMPILER_OUTPUT'] = str(debug)
        self.write_combined_file = write_combined_file


    def compile(self, bufferStructsObj, library_file, footer_file=None, N=15, invMemoryDensity=2):
        assert type(N) == int
        assert N < 20, "N >= 20 won't fit in a single buffer, so is unsupported. Nothing sane should use 20, is this wickr?"
        self.N = N
        assert bufferStructsObj is not None, "need to supply a bufferStructsObj : set all to 0 if necessary"
        assert bufferStructsObj.code is not None, "bufferStructsObj should be initialised"
        self.bufStructs = bufferStructsObj
        self.wordSize = self.bufStructs.wordSize

        # set the np word type, for use in .run
        npType = {
            4 : np.uint32,
            8 : np.uint64,
        }
        self.wordType = npType[self.wordSize]

        src = self.bufStructs.code
        if library_file:
            with open(os.path.join("Library","worker","generic",library_file), "r") as rf:
                src += rf.read()

        if footer_file:
            with open(os.path.join("Library","worker","generic",footer_file), "r") as rf:
                src += rf.read()

        # Standardise to using no \r's, move to bytes to stop trickery
        src = src.encode("ascii")
        src = src.replace(b"\r\n",b"\n")

        # Debugging
        if self.write_combined_file:
            with open("combined_" + library_file, "wb") as wf:
                wf.write(src)

        # Convert back to text!
        src = src.decode("ascii")

        # Check that it starts with 2 newlines, for adding our defines
        if src.startswith("\n\n"):
            src = "\n\n" + src
            src = src[len("\n\n"):]
            # Prepend define N and invMemoryDensity
            defines = "#define N {}\n#define invMemoryDensity {}\n".format(N, invMemoryDensity)
            src = defines + src

        # Kernel function instantiation. Build returns self.
        self.prg = cl.Program(self.ctx, src).build()
        return self.prg

    # Forms the input buffer of derived keys
    # Returns the buffer and number in the buffer, <= n (iter may be exhausted)
    def makeInputBuffer(self, dkIter, n):
        inpArray = bytearray()
        numEaten = n

        for i in range(n):
            try:
                dk = dkIter.__next__()
            except StopIteration:
                # Correct the chunk size and break
                numEaten = i
                break

            assert len(dk) == BLOCK_LEN_BYTES
            #   , "Derived key input is length {}, when we expected {}".format(len(dk), BLOCK_LEN_BYTES)

            inpArray.extend(dk)

        # pyopencl doesn't like empty buffers, so just cheer it up
        #   (making the buffer larger isn't an issue)
        if len(inpArray) == 0:
            inpArray = b"\x00"

        inp_g = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=inpArray)

        return inp_g, numEaten

    def run(self, 
            bufStructs, 
            func, 
            pwdIter,
            expected_hash,
            paddedLenFunc=None):
        # PaddedLenFunc is just for checking: lower bound with original length if not supplied
        if not paddedLenFunc: paddedLenFunc = lambda x,bs:x
        # Checks on password list : not possible now we have iters!

        inBufSize_bytes = self.bufStructs.inBufferSize_bytes
        outBufSize_bytes = self.bufStructs.outBufferSize_bytes
        outBufSize_hs = outBufSize_bytes * 2

        # Main loop is taking chunks of at most the workgroup size
        while True:
            # Moved to bytearray initially, avoiding copying and above all
            #   'np.append' which is horrific
            pwArray = bytearray()
            # For each password in our chunk, process it into pwArray, with length first
            # Notice that this lines up with the struct declared in the .cl file!
            chunkSize = self.workgroupsize
            for i in range(self.workgroupsize):
                try:
                    pw = pwdIter.__next__()
                except StopIteration:
                    # Correct the chunk size and break
                    chunkSize = i
                    break

                pwLen = len(pw)
                # Now passing hash block size as a parameter.. could be None?
                assert paddedLenFunc(pwLen, self.bufStructs.hashBlockSize_bits // 8) <= inBufSize_bytes, \
                    "password #" + str(i) + ", '" + pw.decode() + "' (length " + str(pwLen) + ") exceeds the input buffer (length " + str(inBufSize_bytes) + ") when padded"

                # Add the length to our pwArray, then pad with 0s to struct size
                # prev code was np.array([pwLen], dtype=np.uint32), this ultimately is equivalent
                pwArray.extend(pwLen.to_bytes(self.wordSize, 'little')+pw+(b"\x00"* (inBufSize_bytes - pwLen)))
                #pwArray.extend((pwLen).to_bytes(self.wordSize,'little'))
                #pwArray.extend(pw)
                #pwArray.extend([0] * (inBufSize_bytes - pwLen))
            if chunkSize == 0:
                break
            # print("Chunksize = {}".format(chunkSize))
            # Convert the pwArray into a numpy array, just the once.
            # Declare the numpy array for the digest output
            pwArray = np.frombuffer(pwArray, dtype=self.wordType)
            result = np.zeros(bufStructs.outBufferSize * chunkSize, dtype=self.wordType)
            result_byte_array = np.zeros(chunkSize,dtype=np.ubyte)
            expected_hash_array = np.frombuffer(expected_hash,dtype=np.ubyte)

            
            # Allocate memory for variables on the device
            pass_g = cl.Buffer(self.ctx, cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR, hostbuf=pwArray)
            result_g = cl.Buffer(self.ctx, cl.mem_flags.WRITE_ONLY, result.nbytes)
            result_byte_array_buffer = cl.Buffer(self.ctx,cl.mem_flags.WRITE_ONLY, result_byte_array.nbytes)
            expected_hash_buffer = cl.Buffer(self.ctx,
                                             cl.mem_flags.READ_ONLY | cl.mem_flags.COPY_HOST_PTR,
                                             hostbuf=expected_hash_array)

            # Call Kernel. Automatically takes care of block/grid distribution
            pwdim = (chunkSize,)

            #print('Start job')
            # Main function callback : could adapt to pass further data
            func(self, pwdim, pass_g, result_g, result_byte_array_buffer, expected_hash_buffer)
            #print('End job')

            # Read the results back into our array of int32s, then hexlify
            # Some inefficiency here, unavoidable using hexlify
            #print('Start enqueue')
            cl.enqueue_copy(self.queue, result_byte_array, result_byte_array_buffer)
            #cl.enqueue_copy(self.queue, result, result_g)
            #print('End enqueue')

            # Chop up into the individual hash digests, then trim to necessary hash length.
            #results = []
            #for i in range(0, len(result), outBufSize_bytes//bufStructs.wordSize):
            #    v=bytes(result[i:i + outBufSize_bytes//bufStructs.wordSize])
            #    results.append(v)

            yield result_byte_array

        # No main return
        return None

    def determineWorkgroupsize(self, N_value=15):
        devices = cl.get_platforms()[self.platform_number].get_devices()
        wgSize = 0
        for device in devices:
            ## Actually adjust based on invMemoryDensity!
            N_blocks_bytes = (1 << N_value) * BLOCK_LEN_BYTES // self.inv_memory_density
            memoryForOneCore = BLOCK_LEN_BYTES * 2 + N_blocks_bytes  # input, output & V

            ## ! Restrict to half the memory for now
            coresOnDevice = (int(0.5 * device.global_mem_size) // memoryForOneCore)
            percentUsage = 100 * memoryForOneCore * coresOnDevice / device.global_mem_size
            percentUsage = str(percentUsage)[:4]
            if self.debug == 1:
                print("Using {} cores on device with global memory {}, = {}%".format(
                    coresOnDevice, device.global_mem_size, percentUsage
                ))
            wgSize += coresOnDevice

        if self.debug == 1:
            print("Workgroup size determined as {}".format(wgSize))

        return wgSize

class opencl_algos:
    def __init__(self, platform, debug, write_combined_file, inv_memory_density=1, openclDevice = 0):
        if debug==False:
            debug=0
        self.opencl_ctx = opencl_interface(platform, debug, write_combined_file, openclDevice = openclDevice)
        self.platform_number=platform
        self.inv_memory_density=inv_memory_density

    def concat(self, ll):
        return [obj for l in ll for obj in l]


    def mdPad_64_func(self, pwdLen, blockSize):
        # both parameters in bytes
        # length appended as a 64-bit integer
        l = (pwdLen + 1 + 8)
        l += (-l) % blockSize
        return l

    def cl_sha1_init(self, option=""):
        bufStructs = buffer_structs()
        bufStructs.specifySHA1()
        assert bufStructs.wordSize == 4  # set when you specify sha1
        prg=self.opencl_ctx.compile(bufStructs, 'sha1.cl', option)
        return [prg, bufStructs]

    def cl_sha1(self, ctx, passwordlist, expected_hash):
        # self.cl_sha1_init()
        prg = ctx[0]
        bufStructs = ctx[1]
        def func(s, pwdim, pass_g, result_g, result_bytes_array, expected_hash):
            prg.hash_main(s.queue, pwdim, None, pass_g, result_g, result_bytes_array,expected_hash)

        return self.concat(self.opencl_ctx.run(bufStructs, 
                                               func, 
                                               iter(passwordlist), 
                                               expected_hash, 
                                               self.mdPad_64_func))