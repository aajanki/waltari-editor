import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel
from annotate import TextAnnotator

app = FastAPI()
annotator = TextAnnotator()


class InputText(BaseModel):
    text: str


@app.get("/")
async def read_root():
    return {"Hello": "World"}


@app.post("/api/annotate")
async def read_item(inp: InputText):
    return annotator.analyze(inp.text)


if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
