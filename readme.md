
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


# venv

## create it
```
python3 -m venv .venv
```
or
```
virtualenv -p python3.9.6 venv
```


## use it
```
source .venv/bin/activate
```

## dependencies
cf. requirement

+
```
pip install pytest 
```


## leave it
```
deactivate
```


## run DEEP-OC-multi_plankton_separation container
ssh niko
cd ~/complex/DEEP-OC-multi_plankton_separation

# build the container
docker build -t deephdc/uc-emmaamblard-deep-oc-multi_plankton_separation .


# run it to have interactive shell
~/complex/DEEP-OC-multi_plankton_separation$ docker run -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-emmaamblard-deep-oc-multi_plankton_separation 

# run it in detach mode
~/complex/DEEP-OC-multi_plankton_separation$ docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8888:8888 deephdc/uc-emmaamblard-deep-oc-multi_plankton_separation 


# change local port 8888 to 8889, because already use by another container,      which ????
~/complex/DEEP-OC-multi_plankton_separation$ docker run -d -ti -p 5000:5000 -p 6006:6006 -p 8889:8888 deephdc/uc-emmaamblard-deep-oc-multi_plankton_separation 


## Test with Thunder Client
use the collection named Happy Pipeline

test happy pipeline : to see if server alive

test DEEP plankton separation - niko alive ? : to see if multi_plankton_separation is alive on Niko server

