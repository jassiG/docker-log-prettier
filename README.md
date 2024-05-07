I hate raw docker logs

pipe the live rcms docker output into the python script:

`docker logs -f --tail 10 <CONTAINER_NAME> | python3 pretty_json.py`

syntax: 
use `--SM` prefix for message1, if you want small output
