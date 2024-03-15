#!/bin/bash

# Loop 100 times

count_execution=$(grep -o 'Execution' ~/qigong/data/2222_running_1.log | wc -l)
count_case1=$(grep -o 'telemetry ietf event-destination' ~/qigong/data/2222_running_1.log | wc -l)
count_case7=$(grep -o 'ip http secure-server' ~/qigong/data/2222_running_1.log | wc -l)
clear
echo ""
echo "=================================================================="
echo "LOG OF ~/qigong/data/2222_running_1.log"
echo "=================================================================="
tail -n 19 ~/qigong/data/2222_running_1.log
echo "=================================================================="
echo ""

echo "Excution iter: $count_execution"
echo "Case 1 iter: $count_case1"
echo "Case 7 iter: $count_case7"
echo ""
echo "------------------"

if [ "$count_execution" -eq "$count_case1" ]; then
  echo "The number of occurrences of 'Execution' and 'telemetry ietf event-destination' are the same for case 1: $count_execution"
else
  echo "[ERROR] The number of occurrences of 'Execution' is $count_execution, and 'telemetry ietf event-destination' is $count_case1. They are not the same."
fi
if [ "$count_execution" -eq "$count_case7" ]; then
  echo "The number of occurrences of 'Execution' and 'ip http secure-server' are the same for case 7: $count_execution"
else
  echo "[ERROR]  The number of occurrences of 'Execution' is $count_execution, and 'ip http secure-server' is $count_case7. They are not the same."
fi
echo "=================================================================="
