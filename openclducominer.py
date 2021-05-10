#!/usr/bin/env python3
# OpenCL Miner for Duino-Coin project, can be used on CPU or GPU. 
# Created by JoyBed, later also developed by TheSewerSide . 
# Edited By: Primitt(color and asthetics)
import hashlib
import os
import socket
import sys
import time
import urllib.request
import binascii
import functools, operator
import colorama
import threading
import psutil
import GPUtil
from binascii import hexlify, unhexlify
from Library import opencl
from Library.opencl_information import opencl_information
from collections import deque
from colorama import Fore, Back, Style
from tabulate import tabulate
import pyopencl
import numpy
import traceback

colorama.init()
gpus = GPUtil.getGPUs()
soc = socket.socket()
pool_address = ''
pool_port = 0
debug = 0
write_combined_file = True

def reconnect():
    global pool_address,pool_port,soc
    soc = socket.socket()
    soc.connect((pool_address, int(pool_port)))
    soc.settimeout(20)
    server_version = soc.recv(3).decode()  # Get server version
    print(Fore.RED + "\nServer is on version", server_version)

def sha1(opencl_algo, ctx, last_hash, expected_hash, start, end, max_batch_size = 2):
    clresult=opencl_algo.cl_sha1(ctx, 
                                 last_hash, 
                                 expected_hash, 
                                 start, 
                                 end, 
                                 max_batch_size)
    return(clresult)
    
def sendresult(result,timeDifference,difficulty,shares) -> bool:
    clear()
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
    
    print("="*40, "CPU Info", "="*40)
    # number of cores
    print("Physical cores:", psutil.cpu_count(logical=False))
    print("Total cores:", psutil.cpu_count(logical=True))
    # CPU frequencies
    cpufreq = psutil.cpu_freq()
    print(f"Max Frequency: {cpufreq.max:.2f}Mhz")
    print(f"Min Frequency: {cpufreq.min:.2f}Mhz")
    print(f"Current Frequency: {cpufreq.current:.2f}Mhz")
    # CPU usage
    print("CPU Usage Per Core:")
    for i, percentage in enumerate(psutil.cpu_percent(percpu=True, interval=1)):
        print(f"Core {i}: {percentage}%")
    print(f"Total CPU Usage: {psutil.cpu_percent()}%")
    
    list_gpus = []
    print("="*40, "GPU Info", "="*40)
    for gpu in gpus:
        # get the GPU id
        gpu_id = gpu.id
        # name of GPU
        gpu_name = gpu.name
        # get % percentage of GPU usage of that GPU
        gpu_load = f"{gpu.load*100}%"
        # get free memory in MB format
        gpu_free_memory = f"{gpu.memoryFree}MB"
        # get used memory
        gpu_used_memory = f"{gpu.memoryUsed}MB"
        # get total memory
        gpu_total_memory = f"{gpu.memoryTotal}MB"
        # get GPU temperature in Celsius
        gpu_temperature = f"{gpu.temperature} °C"
        gpu_uuid = gpu.uuid
        list_gpus.append((
            gpu_id, gpu_name, gpu_load, gpu_free_memory, gpu_used_memory,
            gpu_total_memory, gpu_temperature, gpu_uuid
        ))

    print(tabulate(list_gpus, headers=("id", "name", "load", "free memory", "used memory", "total memory", "temperature", "uuid")))
    print('\n')
    # If result was good
    if feedback == "GOOD":
        print(Fore.GREEN + "Accepted share #" + str(shares) + " | Good Job  Result: ",result,"Hashrate: ",int(hashrate/1000000) ,"MH/s ","Difficulty: ",difficulty)
    # If result was incorrect
    elif feedback == "BAD":
        print(Fore.RED + "Rejected share HAHA YOUR BAD | Result: ",result,"Hashrate: ",int(hashrate/1000000),"MH/s ","Difficulty: ",difficulty)
    elif feedback == '':
        to_return = False
    return to_return

def get_cpu_info():
    cpuusage = psutil.cpu_percent(percpu=True)
    return cpuusage

def get_gpu_info():
    gpuusage = GPUtil.showUtilization()
    return gpuusage

def mine(ctx, opencl_algos, username):
    while True:
        reconnect()
        # Mining section
        connected = True
        shares = int(0)
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

            hashingStartTime = time.time()

            real_difficulty = 100 * int(difficulty)+1
            #stop_mining = False

            ducos = sha1(opencl_algos, ctx, last_hash, expected_hash, 0, real_difficulty, 1000)
            if ducos != None:
                hashingStopTime = time.time()
                timeDifference = hashingStopTime - hashingStartTime
                shares+=1
                sendresult(ducos,timeDifference,difficulty,shares)

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def main(argv):
    global pool_address, pool_port, soc
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
    
    minethread = threading.Thread(target=mine, args=(ctx, opencl_algos, username))
    minethread.daemon = True
    minethread.start()
    
    while True:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except:
        traceback.print_exc()
    input()
