#!/usr/bin/env python3
# Minimal version of Duino-Coin PC Miner, useful for developing own apps. Created by revox 2020-2021. Edited By: Primitt(color and asthetics)
import hashlib
import os
import socket
import sys  # Only python3 included libraries
import time
import urllib.request
import binascii
import functools, operator
import colorama
# import psutil # Add more about this later (for gpu temps, i will learn how to code this in later, i may not display this)
from binascii import hexlify, unhexlify
from Library import opencl
from Library.opencl_information import opencl_information
from collections import deque
from colorama import Fore, Back, Style
import pyopencl
import numpy

colorama.init()

soc = socket.socket()

debug = 0
write_combined_file = True

def sha1(opencl_algo, ctx, hash1):
    clresult=opencl_algo.cl_sha1(ctx,hash1)
    if debug == 1:
        print("hashed " + str(clresult))
        print("hashed0" + str(clresult[0]))

    return(clresult)

    
def sendresult(result,timeDifference,difficulty):
    hashrate = result / timeDifference
    # Send numeric result to the server
    soc.send(bytes(str(result)+ ","+ str(hashrate)+ ",OpenCL Miner",encoding="utf8"))
    # Get feedback about the result
    feedback = soc.recv(1024).decode().rstrip("\n")
    # If result was good
    if feedback == "GOOD":
        print(Fore.GREEN + "Accepted share Good Job  Result: ",result,"Hashrate: ",int(hashrate/1000) ,"kH/s ","Difficulty: ",difficulty)
    # If result was incorrect
    elif feedback == "BAD":
        print(Fore.RED + "Rejected share HAHA YOUR BAD  Result: ",result,"Hashrate: ",int(hashrate/1000),"kH/s ","Difficulty: ",difficulty)
    
def main(argv):
    # This sections grabs pool adress and port from Duino-Coin GitHub file
    # Serverip file URL
    serverip = ("https://raw.githubusercontent.com/"
                + "revoxhere/"
                + "duino-coin/gh-pages/"
                + "serverip.txt")

    with urllib.request.urlopen(serverip) as content:
        # Read content and split into lines
        content = content.read().decode().splitlines()

    # Line 1 = IP
    pool_address = content[0]
    # Line 2 = port
    pool_port = content[1]

    # This section connects and logs user to the server
    soc.connect((str(pool_address), int(pool_port)))
    soc.settimeout(10)
    server_version = soc.recv(3).decode()  # Get server version
    print(Fore.GREEN + "DuinoCoin OpenCL Miner for CPU/GPU\n")
    username = input ("Enter your username: ")
    info=opencl_information()
    info.printplatforms()
    
    #platforms = pyopencl.get_platforms()
    platform = input("Select which platform to mine at: ")

    #devices = platforms[int(platform)].get_devices()
    #print(platforms[int(platform)].get_devices())

    print(Fore.RED + "\nServer is on version", server_version)
    opencl_algos = opencl.opencl_algos(int(platform), debug, write_combined_file,inv_memory_density=10,openclDevice=0)
    ctx = opencl_algos.cl_sha1_init()

    

    # Mining section
    while True:
        # Send job request
        soc.send(bytes(
            "JOB,"
            + str(username)
            + ",MEDIUM", # will change
            encoding="utf8"))

        # Receive work
        job = soc.recv(128).decode().rstrip("\n")
        # Split received data to job and difficulty
        job = job.split(",")
        if debug == 1:
            print("Received: " + " ".join(job))
            print("job[0] " + str(type(job[0])))
        difficulty = int(job[2])
        job1 = job[0] + str()
        
        expected_hash = bytearray.fromhex(job[1])

        job_amount = 20000
        

        if difficulty*100 < job_amount:
            job_amount = difficulty*100

        hashme = []
        for i in range(job_amount):
            hashme.append('')
        hashme = numpy.array(hashme,dtype=object)

        hashingStartTime = time.time()

        stop_mining = False
        for result in range(0,100 * int(difficulty) + 1,job_amount):

            #start_populate = time.time()
            for i in range(job_amount):
                job_to_append = job[0] + str(result+i)
                hashme[i] = job_to_append.encode('ascii')
            #print('Populate Time:',time.time()-start_populate)
            
            if debug == 1:
                print("hashme " + str(type(hashme)) + " " + str(hashme))
                print("job[1]" + str(job[1]))
            
            #real_time = time.time()
            ducos = sha1(opencl_algos, ctx, hashme)
            #print('Real Time:',time.time()-real_time)

            if debug == 1:
                time.sleep(2)
            #start_checks = time.time()
            for i in range(job_amount):
                if expected_hash == ducos[i]:
                    hashingStopTime = time.time()
                    timeDifference = hashingStopTime - hashingStartTime
                    sendresult(result+i,timeDifference,difficulty)
                    stop_mining = True
                    break
            #print('Checks Time:',time.time()-start_checks)
            if stop_mining:
                break
            
            

if __name__ == '__main__':
  main(sys.argv)
