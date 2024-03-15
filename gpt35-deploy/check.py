# from time import sleep
# from threading import Thread
# import requests.exceptions



# # def tap(url, name, retries=3, retry_seconds=2):
# #     retry_codes = [
# #         HTTPStatus.TOO_MANY_REQUESTS,
# #         HTTPStatus.INTERNAL_SERVER_ERROR,
# #         HTTPStatus.BAD_GATEWAY,
# #         HTTPStatus.SERVICE_UNAVAILABLE,
# #         HTTPStatus.GATEWAY_TIMEOUT,
# #     ]
        
# #     # Flask app serving check with requests
# #     for n in range(retries):
# #         try:
# #             response = requests.get(url)
# #             response.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
# #             break
# #         except exceptions.HTTPError as exc:
# #             code = exc.response.status_code
            
# #             if code in retry_codes:
# #                 # retry after n seconds
# #                 time.sleep(retry_seconds)
# #                 continue

# #             print(f"4xx, 5xx {name}")
# #             return '4xx, 5xx' 
# #         except (exceptions.ConnectionError, exceptions.Timeout):
# #             print(f"Down: {name}")
# #             return 'Down' 

# def tap(url, name):
#     # Flask app serving check with requests
#     try:
#         r = requests.get(url)
#         r.raise_for_status()  # Raises a HTTPError if the status is 4xx, 5xxx
#     except (requests.exceptions.ConnectionError, requests.exceptions.Timeout):
#         print(f"Down: {name}")
#         return 'Down' 
#     except requests.exceptions.HTTPError:
#         print(f"4xx, 5xx {name}")
#         return '4xx, 5xx' 
#     else:
#         print(f"All good!, {name}" ) # Proceed to do stuff with `r` 
#         return 'All good'
    

# # task that runs at a fixed interval
# def background_task(interval_sec):
#     count = 0
#     while True:
#         sleep(interval_sec)
#         # periodic tapping 
#         topic_module = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8888/dev', name='topic:8888')
#         embedding = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8089/query', name='bi/ce:8089')
#         papyrus = tap('http://ip-10-0-0-93.us-west-2.compute.internal:8090/generate', name='papyrus:8090')
#         pipeline = tap('http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen', name='pipeline:2222')
#         print(f'Daemon background task! #{count}')
#         count += 1
        

# def run():
#     # create and start the daemon thread
#     print('Starting background task...')
#     daemon = Thread(target=background_task, args=(20,), daemon=True, name='Background')
#     daemon.start()

#     # main thread is carrying on...
#     print('Main thread is carrying on...')
#     sleep(100)
#     print('Main thread done.')


            
# if __name__ == '__main__':
#     run()
    
    