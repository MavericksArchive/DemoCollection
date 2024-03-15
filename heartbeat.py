# from threading import Thread
import time 
import asyncio
import requests
import subprocess



def tap(url, name):
    # Flask app serving check with requests
    try:
        r = requests.get(url)
        r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
    except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
        print(f'====='* 10)
        print(f' !!! ERROR !!! ')
        print(f"Down: {name}")
        print(f'====='* 10)
        return False 
    except requests.exceptions.HTTPError:
        print(f'====='* 10)
        print(f' !!! ERROR !!! ')
        print(f"4xx, 5xx {name}")
        print(f'====='* 10)
        return False
    else:
        print(f"All good!, {name}" ) # Proceed to do stuff with `r` 
        return True
    

# task that runs at a fixed interval
def background_task(interval_sec):
    count = 1
    while True:
        time.sleep(interval_sec)
        # periodic tapping 
        papyrus = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8090/health', name='papyrus:8090')
        pipeline = tap('http://ip-10-0-0-93.us-west-2.compute.internal:2222/health', name='pipeline:2222')
        nowgmt = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
        print(f'{nowgmt}: check_v2.py Daemon background task!\t#{count}')
        count += 1


def run_subprocess(command):
    # Using system() method to
    # execute shell commands
    subprocess.Popen(command, shell=True)


async def periodic():
    while True:
        background_task(interval_sec=30)
        await asyncio.sleep(1)


def launch():
    
    def stop():
        task.cancel()
    
    loop = asyncio.get_event_loop()
    loop.call_later(2, stop)
    task = loop.create_task(periodic())

    try:
        loop.run_until_complete(task)
    except asyncio.CancelledError:
        pass
    

if __name__ == '__main__':
    launch()
    