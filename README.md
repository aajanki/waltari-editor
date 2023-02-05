# Waltari editor - analyzing written Finnish text

Waltari is a text editor that analyzes Finnish text. It highlights sentences
that are difficult to understand and sentences that use passive voice.

## Running

Backend:

```shell
cd backend
python3 -m venv venv
source venv/bin/activate
pip install wheel
pip install -r requirements.txt -r requirements-dev.txt

uvicorn main:app --reload
```

Frontend:

```shell
cd editor-app
npm install

npm start
```

## Backend unit tests

```
cd backend
python -m pytest
```
