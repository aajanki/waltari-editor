import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from annotate import TextAnnotator

app = FastAPI()
annotator = TextAnnotator()

origins = [
    "http://localhost:3000",
    "localhost:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


class Contents(BaseModel):
    text: str


@app.get("/")
async def root():
    return 'Text annotation API'


@app.post("/api/annotate")
def annotate(contents: Contents):
    return annotator.analyze(contents.text)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
