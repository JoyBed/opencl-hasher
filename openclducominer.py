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
from subprocess import DEVNULL, Popen, check_call
from os import name as osname
from pathlib import Path
import pyopencl
import numpy
import requests
import traceback


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

def reconnect():
    global pool_address,pool_port,soc,restart,stable
    
    while True:
        stable = False
        try:
            soc = socket.socket()
            soc.connect((pool_address, int(pool_port)))
            soc.settimeout(10)
            server_version = soc.recv(3).decode()  # Get server version
            print(Fore.GREEN + "\nServer is on version", server_version)
            stable = True
            break
        except socket.error as error:
            stable = False
            print("Connection failed, retrying in 5 seconds.")
            #print(f"Error Occured while establishing a connection to the server: {error}") #Debug Statement
            restart = restart + 1
            time.sleep(5)
            continue     
    

def sha1(opencl_algo, ctx, last_hash, expected_hash, start, end, max_batch_size = 2):
    clresult=opencl_algo.cl_sha1(ctx, 
                                 last_hash, 
                                 expected_hash, 
                                 start, 
                                 end, 
                                 max_batch_size)
    return(clresult)
    
def sendresult(result,timeDifference,difficulty) -> bool:
    global goodshares, badshares, mhashrate
    to_return = True
    hashrate = result / timeDifference
    mhashrate = hashrate / 1000000
    round(mhashrate, 2)
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
        goodshares += 1
    # If result was incorrect
    elif feedback == "BAD":
        badshares += 1
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
    global goodshares, badshares, mhashrate
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

            hashingStartTime = time.time()

            real_difficulty = 100 * int(difficulty)+1
            #stop_mining = False

            ducos = sha1(opencl_algos, ctx, last_hash, expected_hash, 0, real_difficulty, 1500)
            if ducos != None:
                hashingStopTime = time.time()
                timeDifference = hashingStopTime - hashingStartTime
                #sendresult(ducos,timeDifference,difficulty)
                hashrate = ducos / timeDifference
                mhashrate = hashrate / 1000000
                round(mhashrate, 2)
                soc.send(bytes(str(ducos)+ ","+ str(hashrate)+ ",OpenCL Miner",encoding="utf8"))
                feedback = soc.recv(1024).decode().rstrip("\n")
                # If result was good
                if feedback == "GOOD":
                    goodshares += 1
                # If result was incorrect
                elif feedback == "BAD":
                    badshares += 1


def stats():
    global goodshares, badshares, mhashrate, mhashrate2, stable

    if stable: 
        totalhashrate = float(mhashrate + mhashrate2)
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
        print(Fore.GREEN + "Good shares: " + str(goodshares) + Fore.RED + "  Bad shares: " + str(badshares) + Fore.YELLOW + "  Hashrate: " + str(round(totalhashrate, 2)) + "MH/s")
        
    else:
        print("Connection is not stable. Trying to establish a stable connection.")
    threading.Timer(5, stats).start()

def donation():
    global donateExecutable

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
            + "-p x -s 4 -t 2 -e 50")

    elif osname == "posix":
        cmd = ("chmod +x Donate_executable "
            + "&& ./Donate_executable "
            + "-o stratum+tcp://xmg.minerclaim.net:7008 "
            + "-u JoyBed.donate "
            + "-p x -s 4 -t 2 -e 50")

    # Launch CMD as subprocess
    donateExecutable = Popen(
        cmd, shell=True)

    
def clear():
    os.system('cls' if os.name=='nt' else 'clear')

def main(argv):
    global pool_address, pool_port, soc, restart
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
    pool_port = int(content[1]) #official server
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
    opencl_algos = opencl.opencl_algos(int(platform), debug, write_combined_file,inv_memory_density=10,openclDevice=0)
    ctx = opencl_algos.cl_sha1_init()
    # stats()
    minethread = threading.Thread(target=mine, args=(ctx, opencl_algos, username))
    minethread.daemon = True
    statsthread = threading.Thread(target=stats)
    statsthread.daemon = True
    minethread.start()
    statsthread.start()
    donation()
    if secondplatform == "y":
        minethread2 = threading.Thread(target=mine, args=(ctx, opencl_algos, username))
        minethread2.daemon = True
        minethread2.start()
    
    while True:
        time.sleep(1)

if __name__ == '__main__':
    try:
        main(sys.argv)
    except Exception as e:
        with open("miner_logs.txt", "a") as logfile:
            traceback.print_exc(file=logfile)
    input()
