import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from annotate import TextAnnotator, text_from_delta

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
    delta: dict


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/api/annotate")
async def annotate(contents: Contents):
    text = text_from_delta(contents.delta)
    return annotator.analyze(text)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
