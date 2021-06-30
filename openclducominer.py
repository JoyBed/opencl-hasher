#!/usr/bin/env python3
# OpenCL Miner for Duino-Coin project, can be used on CPU or GPU. 
# Created by JoyBed, later also developed by TheSewerSide. 
# Edited By: Primitt(color and asthetics)
import hashlib
import os
import socket
import sys
import time
import urllib.request
import binascii
import functools, operator
from GPUtil.GPUtil import GPU
import colorama
import threading
import psutil
import GPUtil
from binascii import Error, hexlify, unhexlify
from Library import opencl
from Library.opencl_information import opencl_information
from collections import deque
from colorama import Fore, Back, Style
from tabulate import tabulate
from subprocess import DEVNULL, Popen, check_call
from os import name as osname
from pathlib import Path
import pyopencl
import numpy
import requests
import traceback
import logging

colorama.init()
gpus = GPUtil.getGPUs()
soc = socket.socket()
pool_address = ''
pool_port = 0
debug = 0
write_combined_file = True
goodshares = int(0)
badshares = int(0)
mhashrate = float()
mhashrate2 = float()
restart = 0
stable = False
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
logs =''
errors =''
allthreads = ''

def check_thread_alive(thr):
    thr.join(timeout=0.0)
    time.sleep(0.5)
    return thr.is_alive()

def setup_logger(name, log_file, level=logging.INFO):
    global formatter

    handler = logging.FileHandler(log_file, mode='w')        
    handler.setFormatter(formatter)

    logger = logging.getLogger(name)
    logger.setLevel(level)
    logger.addHandler(handler)

    return logger

def reconnect():
    global pool_address,pool_port,soc,restart,stable, errors, logs
    
    while True:
        stable = False
        try:
            soc = socket.socket()
            soc.connect((pool_address, int(pool_port)))
            soc.settimeout(15)
            server_version = soc.recv(3).decode()  # Get server version
            print(Fore.GREEN + "\nServer is on version", server_version)
            stable = True
            break   
        except socket.error or socket.timeout or Error or Exception as error:
            stable = False
            print("Connection failed, retrying in 5 seconds.")
            restart = restart + 1
            time.sleep(6)
            errors.info("Connection to server failed due to the following exception")
            errors.info(error,exc_info=True)
            continue     
    
def sha1(opencl_algo, ctx, last_hash, expected_hash, start, end, max_batch_size = 2):
    clresult=opencl_algo.cl_sha1(ctx, 
                                 last_hash, 
                                 expected_hash, 
                                 start, 
                                 end, 
                                 max_batch_size)
    return(clresult)

def get_cpu_info():
    cpuusage = psutil.cpu_percent(percpu=True)
    return cpuusage

def get_gpu_info():
    gpuusage = GPUtil.showUtilization()
    return gpuusage

def mine(ctx, opencl_algos, username):
    global goodshares, badshares, mhashrate, logs, errors
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
            except Exception or Error as error:
                connected = False
                errors.info(error,exc_info=True)
                continue

            try:
                # Receive work
                job = soc.recv(128).decode().rstrip("\n")
            except Exception or Error as error:
                connected = False
                errors.info(error,exc_info=True)
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
            logs.info(f'Last Processed Hash: {job[1]}')
            hashingStartTime = time.time()

            real_difficulty = 100 * int(difficulty)+1
            #stop_mining = False

            ducos = sha1(opencl_algos, ctx, last_hash, expected_hash, 0, real_difficulty, 1000)
            if ducos != None:
                hashingStopTime = time.time()
                timeDifference = hashingStopTime - hashingStartTime
                #sendresult(ducos,timeDifference,difficulty)
                hashrate = ducos / timeDifference
                mhashrate = hashrate / 1000000
                soc.send(bytes(str(ducos)+ ","+ str(hashrate)+ ",OpenCL Miner",encoding="utf8"))
                feedback = soc.recv(1024).decode().rstrip("\n")
                # If result was good
                if feedback == "GOOD":
                    goodshares += 1
                    logs.info("Good Job")
                # If result was incorrect
                elif feedback == "BAD":
                    badshares += 1
                    logs.info("Bad Job")

def stats():
    global goodshares, badshares, mhashrate, stable, logs, errors

    while True:
        if stable: 
            clear()
            print(Fore.GREEN + "="*40, "CPU Info", "="*40)
            # number of cores
            print(Fore.WHITE + "Physical cores:", psutil.cpu_count(logical=False))
            print("Total cores:", psutil.cpu_count(logical=True))
            # No of Mining Threads
            print(f"No of Mining threads: {threading.active_count()-2}") # 2 because 1 is for main thread and 1 is for stats
            # Resrtart Count - Minethread
            print(f"Attempts to establish connection : {restart}")
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
            print(Fore.GREEN + "="*40, "GPU Info", "="*40)
            for gpu in gpus:
                # get the GPU id
                gpu_id = gpu.id
                # name of GPU
                gpu_name = gpu.name
                # get % percentage of GPU usage of that GPU
                gpu_load = f"{gpu.load*100}%"
                logs.info(f"GPU LOAD: {gpu.load*100}%")
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
            print(Fore.WHITE + tabulate(list_gpus, headers=("id", "name", "load", "free memory", "used memory", "total memory", "temperature", "uuid")))
            print('\n')
            print(Fore.GREEN + "Good shares: " + str(goodshares) + Fore.RED + "  Bad shares: " + str(badshares) + Fore.YELLOW + "  Hashrate: " + str(round(mhashrate, 2)) + "MH/s")
            
        else:
            print("Connection is not stable. Trying to establish a stable connection.")
        time.sleep(5)

def donation():
    global donateExecutable
    usecores = int(0)
    cores = int(psutil.cpu_count(logical=True))
    
    if osname == "nt":
        # Initial miner executable section
        if not Path("Donate_executable.exe").is_file():
            url = ("https://github.com/"
                   + "revoxhere/"
                   + "duino-coin/blob/useful-tools/"
                   + "DonateExecutableWindows.exe?raw=true")
            r = requests.get(url)
            with open("Donate_executable.exe", "wb") as f:
                f.write(r.content)
    elif osname == "posix":
        # Initial miner executable section
        if not Path("Donate_executable").is_file():
            url = ("https://github.com/"
                   + "revoxhere/"
                   + "duino-coin/blob/useful-tools/"
                   + "DonateExecutableLinux?raw=true")
            r = requests.get(url)
            with open("Donate_executable", "wb") as f:
                f.write(r.content)
    
    if osname == "nt":
        cmd = ("Donate_executable.exe "
            + "-o stratum+tcp://xmg.minerclaim.net:7008 "
            + "-u JoyBed.donate "
            + "-p x -s 4 -t ")

    elif osname == "posix":
        cmd = ("chmod +x Donate_executable "
            + "&& ./Donate_executable "
            + "-o stratum+tcp://xmg.minerclaim.net:7008 "
            + "-u JoyBed.donate "
            + "-p x -s 4 -t ")

    if cores <= 4:
        cmd += "2"
    elif cores <= 8:
        cmd += "3"
    elif cores <= 12:
        cmd += "4"
    elif cores >= 13:
        cmd += "6"

    # Launch CMD as subprocess
    donateExecutable = Popen(
        cmd, shell=True, stdout=DEVNULL)

def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def main(argv):
    global pool_address, pool_port, soc, restart, logs, errors
    
    # File for Mining actions
    logs = setup_logger('miner_logs','miner_logs.log')
     # File for errors and exceptions
    errors = setup_logger('errors','exceptions.log')
    
    logs.info('Main function started')
    
    # This sections grabs pool adress and port from Duino-Coin GitHub file
    # Serverip file URL
    serverip = ("https://raw.githubusercontent.com/"
                + "revoxhere/"
                + "duino-coin/gh-pages/"
                + "serverip.txt")

    with urllib.request.urlopen(serverip) as content:
        # Read content and split into lines
        content = content.read().decode().splitlines()
        # print(f"Content: {content}")
    # Line 1 = IP
    pool_address = content[0] #official server
    #pool_address = "213.160.170.230" #test server
    # Line 2 = port
    pool_port = int(2813) #official server
    # pool_port = 2812 #For debugging only
    # pool_port = int(2811) #test server
    # This section connects and logs user to the server
    clear()
    print(Fore.GREEN + "DuinoCoin OpenCL Miner for CPU/GPU\n")
    username = input ("Enter your username: ")
    clear()
    info=opencl_information()
    info.printplatforms()
    platform = input("Select which platform to mine at: ")
    secondplatform = input("Want to add another platform too?(y/n): ")
    if secondplatform == "y":
        secondplatform = input("Select which platform to mine at: ")
        
    clear()
    donation()
    opencl_algos = opencl.opencl_algos(int(platform), debug, write_combined_file,inv_memory_density=10,openclDevice=0)
    ctx = opencl_algos.cl_sha1_init()
    minethread = threading.Thread(target=mine, args=(ctx, opencl_algos, username))
    minethread.daemon = True
    statsthread = threading.Thread(target=stats)
    statsthread.daemon = True
    minethread.start()
    logs.info('Starting Mining Thread')
    statsthread.start()
    logs.info('Starting Stats Thread')
    if secondplatform == "y":
        minethread2 = threading.Thread(target=mine, args=(ctx, opencl_algos, username))
        minethread2.daemon = True
        minethread2.start()
        logs.info('Starting 2nd Mining Thread')
    while True:
        if check_thread_alive(minethread) == False:
            minethread = threading.Thread(target=mine, args=(ctx, opencl_algos, username), daemon=True)
            minethread.start()
        time.sleep(1)
        
if __name__ == '__main__':
    try:
        main(sys.argv)
    except KeyboardInterrupt or Error or Exception as error:
        errors.info(error,exc_info=True)
    input()
