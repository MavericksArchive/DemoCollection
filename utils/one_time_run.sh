 #!/bin/bash

# Loop 100 times
current_datetime=$(date "+%Y-%m-%d %H:%M:%S")
echo "Execution at $current_datetime"
# Time the curl command
time curl -X POST "http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=conv_test_from_curl&message_id=msg_test_from_curl&source=netlensdryrun=False&debug=False" -H "Content-Type: application/json" -H "X-Api-Key: 230e2b5e-fb08-405c-b9d2-f17e66be3b47" -d '{"user_input": "One of our networkmanagement systems has shown that memory utilization for a cat9200 switched named MRE-Edge2.cisco.com has been increasing. The device is attempting to sendtelemetry data to DNAC but the connection \\ never establishes. I have noticed that the pubd process is consuming the majority of memory. The device is trying tosend telemetry data to our DNAC, but it seems the receiver is responding with a device not found.  Is this a bug?", "nodes_run_data": []}'
delay=$((5 + RANDOM % 10))
echo "Waiting for $delay second(s)... For case 7"
sleep $delay
time curl -X POST "http://ip-10-0-0-93.us-west-2.compute.internal:2222/papyrusGen?conversation_id=conv_test_from_curl&message_id=msg_test_from_curl&source=netlensdryrun=False&debug=False" -H "Content-Type: application/json" -H "X-Api-Key: 230e2b5e-fb08-405c-b9d2-f17e66be3b47" -d '{"user_input": "I have 187 devices that showas potentially vulnerable to the PSIRT cisco-sa-iosxe-webui-privesc-j22SaA4z. How can I confirm vulnerability to this PSIRT that allows a remote, unauthenticatedattacker to create an account on an affected device with privilege level 15 access and can then use that account to gain control of the affected device?","nodes_run_data": []}'
echo "========================================="