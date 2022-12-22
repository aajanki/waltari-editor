# Tool for analyzing written Finnish text

Running the backend:

```shell
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

uvicorn main:app --reload
```

Running the frontend:

```shell
cd editor-app
npm install

npm start
```
