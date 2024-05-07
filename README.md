pipe the live docker output into the python script:

`docker logs -f --tail 10 <CONTAINER_NAME> | python3 pretty_json.py`
