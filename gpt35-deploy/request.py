import json 
import requests

# Set up the URL
url = 'http://localhost:8888/dev'

# Set up the headers
headers = {
    'Content-Type': 'application/json',
    'X-Api-Key': '230e2b5e-fb08-405c-b9d2-f17e66be3b47'
}

# Set up the request body
payload = {
    'user_input': 'One of our network management systems has shown that memory utilization for the device dtw-302-9300-sw-1 has been increasing. When I log into Catalyst Center, the device is not showing as managed. Today the switch had a log about memory value exceeding 90%. I have noticed that the pubd process is consuming the majority of memory.  Is this a bug?',
}
json_payload = json.dumps(payload)

# Make the POST request
response = requests.post(
    url, 
    headers=headers, data=json_payload)

# Check the response
if response.status_code == 200:
    print('Request successful!')
    print(response.json())
else:
    print('Request failed!')
    print(response.text)