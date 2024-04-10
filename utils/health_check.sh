# intention module health check
curl -X GET http://ip-10-0-0-93.us-west-2.compute.internal:8888/health -H "Content-Type: application/json" -H "X-Api-Key: 230e2b5e-fb08-405c-b9d2-f17e66be3b47"

# papyrus module health check
curl -X GET http://ip-10-0-0-93.us-west-2.compute.internal:8090/health 
# curl -X GET http://ip-10-0-0-93.us-west-2.compute.internal:3333/health 

# pipeline health check 
curl -X GET http://ip-10-0-0-93.us-west-2.compute.internal:2222/health 

