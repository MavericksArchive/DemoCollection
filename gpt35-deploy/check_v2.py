# # from threading import Thread
# import time 
# import asyncio
# import requests
# import subprocess



# def tap(url, name):
#     # Flask app serving check with requests
#     try:
#         r = requests.get(url)
#         r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
#     except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
#         print(f"Down: {name}")
#         return False 
#     except requests.exceptions.HTTPError:
#         print(f"4xx, 5xx {name}")
#         return False
#     else:
#         print(f"All good!, {name}" ) # Proceed to do stuff with `r` 
#         return True
    

# # task that runs at a fixed interval
# def background_task(interval_sec):
#     count = 1
#     while True:
#         time.sleep(interval_sec)
#         # periodic tapping 
#         topic_module = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8888/dev', name='topic:8888')
#         if not topic_module:
#             # run_subprocess(command='python app_topic_gpt35.py')
            
#             # docker stop
#             run_subprocess(command='docker stop $(docker ps -q --filter ancestor=project-x-topic-gpt35)')
#             # docker start 
#             run_subprocess(command='docker run -p 8888:8888 project-x-topic-gpt35')

#         embedding = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8089/query', name='bi/ce:8089')
#         papyrus = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8090/generate', name='papyrus:8090')
#         pipeline = tap('http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen', name='pipeline:2222')
#         nowgmt = time.strftime("%Y-%m-%d %H:%M:%S", time.gmtime())
#         print(f'{nowgmt}: check_v2.py Daemon background task!\t#{count}')
#         count += 1


# def run_subprocess(command):
#     # Using system() method to
#     # execute shell commands
#     subprocess.Popen(command, shell=True)


# async def periodic():
#     while True:
#         background_task(interval_sec=30)
#         await asyncio.sleep(1)


# def launch():
    
#     def stop():
#         task.cancel()
    
#     loop = asyncio.get_event_loop()
#     loop.call_later(2, stop)
#     task = loop.create_task(periodic())

#     try:
#         loop.run_until_complete(task)
#     except asyncio.CancelledError:
#         pass
    

# if __name__ == '__main__':
#     launch()
    