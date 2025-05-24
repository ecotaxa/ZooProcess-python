source venv312/bin/activate
# Set the SECRET environment variable for JWT token signing and verification
# In a production environment, use a strong, unique secret key
export SECRET="your-production-secret-key"
PYTHONPATH=$PYTHONPATH:src python3 -m uvicorn main:app --reload
