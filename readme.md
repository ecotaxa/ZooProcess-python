
# API Pipeline
 
A REST API to pilot the Ecotaxa pipelines


# requirement
```
pip install fastapi
pip install pydantic
pip install "uvicorn[standard]"
pip3 install opencv-python
pip install requests
```


# run it to dev

```
uvicorn main:app --reload
```


# online docs

http://127.0.0.1:8000/docs
http://127.0.0.1:8000/redoc


# venv

## create it
```
python3 -m venv .venv
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


