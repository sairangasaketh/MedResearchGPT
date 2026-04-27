from fastapi import FastAPI, UploadFile, File
from pypdf import PdfReader
from transformers import pipeline
from sentence_transformers import SentenceTransformer
import chromadb
import tempfile

app = FastAPI(title="MedResearchGPT API")

summarizer = pipeline(
    "text2text-generation",
    model="google/flan-t5-base"
)

embedder = SentenceTransformer("all-MiniLM-L6-v2")

client = chromadb.Client()
collection = client.get_or_create_collection("papers")

stored_text = ""

@app.get("/")
def home():
    return {"message": "MedResearchGPT API Running"}

@app.post("/upload-pdf/")
async def upload_pdf(file: UploadFile = File(...)):
    global stored_text

    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
        temp_file.write(await file.read())
        temp_path = temp_file.name

    reader = PdfReader(temp_path)

    text = ""
    for page in reader.pages:
        extracted = page.extract_text()
        if extracted:
            text += extracted + "\n"

    stored_text = text

    chunks = []
    for i in range(0, len(text), 1000):
        chunks.append(text[i:i+1000])

    existing = collection.get()

    if existing["ids"]:
        collection.delete(ids=existing["ids"])

    for idx, chunk in enumerate(chunks):
        collection.add(
            documents=[chunk],
            ids=[str(idx)]
        )

    clean_text = text[3000:9000]

    prompt = "Summarize this medical paper:\n" + clean_text

    summary = summarizer(
        prompt,
        max_length=220,
        min_length=80,
        do_sample=False
    )

    return {
        "filename": file.filename,
        "characters": len(text),
        "summary": summary[0]["generated_text"]
    }

@app.get("/ask/")
def ask_question(q: str):
    results = collection.query(
        query_texts=[q],
        n_results=2
    )

    context = " ".join(results["documents"][0])

    prompt = f"Answer based on research paper:\n{context}\nQuestion:{q}"

    answer = summarizer(
        prompt,
        max_length=180,
        do_sample=False
    )

    return {
        "question": q,
        "answer": answer[0]["generated_text"]
    }