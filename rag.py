import os
import re
import pypdf
import chromadb


# ============================================================
# CONFIGURATION
# ============================================================

PDF_PATH = "./documents/rapport.pdf"
CHROMA_PATH = "./chroma_db"

CHUNK_SIZE = 1200
CHUNK_OVERLAP = 150


# ============================================================
# EXTRACTION DU PDF
# ============================================================

reader = pypdf.PdfReader(PDF_PATH)

pages = []

for page_number, page in enumerate(
    reader.pages,
    start=1
):

    text = page.extract_text() or ""

    text = re.sub(
        r"\s+",
        " ",
        text
    ).strip()

    if text:

        pages.append(
            {
                "page": page_number,
                "text": text
            }
        )


# ============================================================
# CRÉATION DES CHUNKS
# ============================================================

chunks = []

for page_data in pages:

    page_number = page_data["page"]
    text = page_data["text"]

    sentences = re.split(
        r"(?<=[.!?])\s+",
        text
    )

    current_chunk = ""

    for sentence in sentences:

        sentence = sentence.strip()

        if not sentence:
            continue

        if (
            len(current_chunk) + len(sentence)
            > CHUNK_SIZE
        ):

            if current_chunk:

                chunks.append(
                    {
                        "text": current_chunk.strip(),
                        "page": page_number
                    }
                )

            overlap = current_chunk[
                -CHUNK_OVERLAP:
            ]

            current_chunk = (
                overlap + " " + sentence
            )

        else:

            current_chunk += (
                " " + sentence
            )

    if current_chunk.strip():

        chunks.append(
            {
                "text": current_chunk.strip(),
                "page": page_number
            }
        )


# ============================================================
# PRÉPARATION DES DOCUMENTS
# ============================================================

documents = []
metadatas = []
ids = []


for index, chunk in enumerate(
    chunks
):

    chunk_id = (
        f"rapport-page-"
        f"{chunk['page']}-"
        f"chunk-{index}"
    )

    document = (
        f"Document : rapport.pdf\n"
        f"Page : {chunk['page']}\n\n"
        f"{chunk['text']}"
    )

    documents.append(
        document
    )

    metadatas.append(
        {
            "document": "rapport.pdf",
            "page": chunk["page"],
            "chunk_id": chunk_id
        }
    )

    ids.append(
        chunk_id
    )


# ============================================================
# INFORMATIONS
# ============================================================

print(
    f"Nombre de pages extraites : {len(pages)}"
)

print(
    f"Nombre de chunks créés : {len(documents)}"
)


# ============================================================
# CHROMADB
# ============================================================

client = chromadb.PersistentClient(
    path=CHROMA_PATH
)


# Supprime l'ancienne collection
# pour reconstruire proprement l'index.

try:

    client.delete_collection(
        name="company_report"
    )

except Exception:

    pass


collection = client.get_or_create_collection(
    name="company_report"
)


# ============================================================
# INDEXATION
# ============================================================

batch_size = 50

for start in range(
    0,
    len(documents),
    batch_size
):

    end = start + batch_size

    collection.upsert(
        ids=ids[start:end],
        documents=documents[start:end],
        metadatas=metadatas[start:end]
    )

    print(
        f"Indexation : "
        f"{min(end, len(documents))}"
        f"/{len(documents)}"
    )


# ============================================================
# RÉSULTAT
# ============================================================

print(
    f"Nombre de morceaux dans ChromaDB : "
    f"{collection.count()}"
)