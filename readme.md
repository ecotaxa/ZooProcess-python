
# API Pipeline
 
A REST API to pilot the Ecotaxa pipelines


# requirement
```
pip install fastapi
pip install pydantic
pip install "uvicorn[standard]"
<!-- pip3 install opencv-python -->
pip install opencv-python
pip install requests
pip install numpy
```


# run it to dev

```
uvicorn main:app --reload
```
ne fonctionne pas en venv ????? why ???


# online docs

http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc




# The gateway API need other containeurs

## run DEEP-OC-multi_plankton_separation container
```bash
ssh niko
cd ~/complex/DEEP-OC-multi_plankton_separation
```

### build the container
```bash
docker build -t deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation .
```


### run it to have interactive shell
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

### run it in detach mode
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

### change local port 8888 to 8889, because already use by another container,      which ????
```bash
~/complex/DEEP-OC-multi_plankton_separation$ 
docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8889:8888 deephdc/uc-ecotaxa-deep-oc-multi_plankton_separation 
```

# Test with Thunder Client (obsolette)
In VSCode Thumder plugin, use the collection named Happy Pipeline

## test happy pipeline
+ to see if server alive
test DEEP plankton separation - niko alive ? : to see if multi_plankton_separation is alive on Niko server


# Run the gateway API in Docker

Built it
```bash
docker build -t gateway_api .
```
Run it
```
docker run -p 8000:8000 -v /Users/sebastiengalvagno/piqv/plankton/:/app/data --name happy_pipeline gateway_api
```

when use Docker use .env.production  else .env.development

at this moment, I can't run in docker because the path are linked to other apps
then it can't find the file

a possibility, to use docker, is to make the very long local path in the container
and use .env.development





# use the Swagger UI
open http://localhost:5000/ui

## through the VPN (niko run)
make a tunnel before open on with local address, port do not pass throught the VPN
```bash
ssh  -f niko -L 5001:localhost:5000 -N
open http://localhost:5001/ui
```


# new container
```bash
cd complex
git clone https://github.com/ai4os-hub/zooprocess-multiple-separator.git
cd zooprocess-multiple-separator/
docker build -t zooprocess-multiple-separator:1 .
docker build --no-cache -t zooprocess-multiple-separator:lastest .

docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8888:8888  zooprocess-multiple-separator:1
```

no detach mode to see error
```
docker run -ti -p 5000:5000 -p 6006:6006 -p 8888:8888  zooprocess-multiple-separator:1
```





# to generate a py client based on openapi.json
```
openapigenerator generate -i http://localhost:5000/openapi.json -g python -o ./src
```

