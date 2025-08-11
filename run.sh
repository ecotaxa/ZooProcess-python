source venv312/bin/activate
export APP_ENV=dev
PYTHONPATH=$PYTHONPATH:src python3 -m uvicorn main:app --reload
