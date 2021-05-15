#!/usr/bin/python3
# -*- coding: utf-8 -*-
# (c) B. Kerler 2018-2021
# MIT License
'''
    Provides a class for filling in my buffer_structs_template.cl
'''

import os
import re

# # Read the template in
# template = ""
# with open(os.path.join(os.path.dirname(__file__), "worker","generic","buffer_structs_template.cl"), "r") as rf:
    # template = rf.read()

class buffer_structs:
    def __init__(self):
        self.code = ""
        self.wordSize = 4
        
    def setMaxBufferSizes(self, max_in_bytes, max_out_bytes, max_salt_bytes=32, max_ct_bytes=0):
        return None
        # Ensure each are a multiple of 4
        max_in_bytes += (-max_in_bytes % self.wordSize)
        max_out_bytes += (-max_out_bytes % self.wordSize)
        max_salt_bytes += (-max_salt_bytes % self.wordSize)

        self.inBufferSize_bytes = max_in_bytes
        self.outBufferSize_bytes = max_out_bytes
        self.saltBufferSize_bytes = max_salt_bytes
        self.inBufferSize = (max_in_bytes + 3) // self.wordSize
        self.outBufferSize = (max_out_bytes + 3) // self.wordSize
        self.saltBufferSize = (max_salt_bytes + 3) // self.wordSize
        self.ctBufferSize_bytes = max_ct_bytes

    def specifyHashSizes(self, hashBlockSize_bits, hashDigestSize_bits):
        return None
        self.hashBlockSize_bits = hashBlockSize_bits
        self.hashDigestSize_bits = hashDigestSize_bits

    def setBufferSizesForHashing(self, hashMaxNumBlocks):
        return None
        self.setMaxBufferSizes(  ((self.hashBlockSize_bits + 7) // 8) * hashMaxNumBlocks,
                            (self.hashDigestSize_bits + 7) // 8,
                            0)

    def ceilToMult(self, n, k):
        return n + ((-n) % k)

    def fill_template(self):
        return None
        rep = { "<hashBlockSize_bits>": str(self.hashBlockSize_bits),
                "<hashDigestSize_bits>" : str(self.hashDigestSize_bits),
                "<inBufferSize_bytes>" : str(self.inBufferSize_bytes),
                "<outBufferSize_bytes>" : str(self.outBufferSize_bytes),
                "<saltBufferSize_bytes>" : str(self.saltBufferSize_bytes),
                "<ctBufferSize_bytes>" : str(self.ctBufferSize_bytes),
                "<word_size>" : str(self.wordSize)
        }

        rep = dict((re.escape(k), v) for k, v in rep.items())
        pattern = re.compile("|".join(rep.keys()))
        self.code = pattern.sub(lambda m: rep[re.escape(m.group(0))], template)

    def specifySHA1(self, max_in_bytes=128, max_salt_bytes=32, dklen=0, max_ct_bytes=0):
        return None
        self.specifyHashSizes(512,160)
        maxNumBlocks = 3
        self.wordSize = 4
        self.setBufferSizesForHashing(maxNumBlocks)
        max_out_bytes = self.hashDigestSize_bits // 8
        if dklen!=0:
            # Adjust output size to be a multiple of the digest
            max_out_bytes = self.ceilToMult(dklen, (self.hashDigestSize_bits // 8))
        self.setMaxBufferSizes(max_in_bytes, max_out_bytes, max_salt_bytes, max_ct_bytes)
        self.fill_template()
        return max_out_bytes