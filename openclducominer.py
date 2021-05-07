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
import traceback

colorama.init()

soc = socket.socket()
pool_address = ''
pool_port = 0

def reconnect():
    global pool_address,pool_port,soc
    soc = socket.socket()
    soc.connect((pool_address, int(pool_port)))
    soc.settimeout(20)
    server_version = soc.recv(3).decode()  # Get server version
    print(Fore.RED + "\nServer is on version", server_version)

debug = 0
write_combined_file = True

def sha1(opencl_algo, ctx, last_hash, expected_hash, start, end):
    clresult=opencl_algo.cl_sha1(ctx,last_hash,expected_hash,start,end)

    return(clresult)

    
def sendresult(result,timeDifference,difficulty) -> bool:
    to_return = True
    hashrate = result / timeDifference
    try:
        # Send numeric result to the server
        soc.send(bytes(str(result)+ ","+ str(hashrate)+ ",OpenCL Miner",encoding="utf8"))
        # Get feedback about the result
        feedback = soc.recv(1024).decode().rstrip("\n")
    except Exception as e:
        print(e)
        to_return = False
        return to_return
    # If result was good
    if feedback == "GOOD":
        print(Fore.GREEN + "Accepted share Good Job  Result: ",result,"Hashrate: ",int(hashrate/1000) ,"kH/s ","Difficulty: ",difficulty)
    # If result was incorrect
    elif feedback == "BAD":
        print(Fore.RED + "Rejected share HAHA YOUR BAD  Result: ",result,"Hashrate: ",int(hashrate/1000),"kH/s ","Difficulty: ",difficulty)
    elif feedback == '':
        to_return = False
    return to_return
    
def main(argv):
    global pool_address, pool_port,soc
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
    pool_port = int(content[1])

    # This section connects and logs user to the server
    
    
    print(Fore.GREEN + "DuinoCoin OpenCL Miner for CPU/GPU\n")
    username = input ("Enter your username: ")
    info=opencl_information()
    info.printplatforms()
    

    platform = input("Select which platform to mine at: ")

    
    opencl_algos = opencl.opencl_algos(int(platform), debug, write_combined_file,inv_memory_density=10,openclDevice=0)
    ctx = opencl_algos.cl_sha1_init()

    while True:
        reconnect()
        # Mining section
        connected = True
        while connected:
            # Send job request
            try:
                soc.send(bytes(
                    "JOB,"
                    + str(username)
                    + ",EXTREME", # will change
                    encoding="utf8"))
            except:
                connected = False
                continue

            try:
                # Receive work
                job = soc.recv(128).decode().rstrip("\n")
            except:
                connected = False
                continue
            if job == '':
                connected = False
                continue

            # Split received data to job and difficulty
            job = job.split(",")
            if debug == 1:
                print("Received: " + " ".join(job))
                print("job[0] " + str(type(job[0])))
            difficulty = int(job[2])
            job1 = job[0]
        
            expected_hash = bytearray.fromhex(job[1])
            last_hash = job[0].encode('ascii')

            job_amount = 10000000
        

            if difficulty*100 < job_amount:
                job_amount = difficulty*100


            hashingStartTime = time.time()

            real_difficulty = 100 * int(difficulty)+1

            stop_mining = False
            for result in range(0,real_difficulty,job_amount):
            
                plus_amount = job_amount
                if result+job_amount>real_difficulty:
                    plus_amount = real_difficulty - result

                if debug == 1:
                    print("hashme " + str(type(hashme)) + " " + str(hashme))
                    print("job[1]" + str(job[1]))
            

                ducos = sha1(opencl_algos, ctx, last_hash, expected_hash, result, result+plus_amount)

                if debug == 1:
                    time.sleep(2)

                #res = numpy.where(ducos==1)[0]
                if ducos != None:
                    hashingStopTime = time.time()
                    timeDifference = hashingStopTime - hashingStartTime
                    sendresult(ducos,timeDifference,difficulty)
                    stop_mining = True

                if stop_mining:
                    break

            
            

if __name__ == '__main__':
    try:
        main(sys.argv)
    except:
        traceback.print_exc()
    input()
