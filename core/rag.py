from pathlib import Path
from typing import List
import argparse
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

from ...utils.text_processing import extract_pdf_text, chunk_text  # [`lib/aim/utils/text_processing.py`]

CHROMA_PERSIST_DIR = Path(".chromadb")

def create_chroma_client(persist_directory: Path = CHROMA_PERSIST_DIR):
    settings = Settings(persist_directory=str(persist_directory))
    client = chromadb.Client(settings)
    return client

def build_index_from_files(
    client: chromadb.Client,
    collection_name: str,
    source_folder: Path,
    persist_dir: Path = CHROMA_PERSIST_DIR,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 2000
):
    client = create_chroma_client(persist_dir)
    ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
    coll = client.get_or_create_collection(name=collection_name, embedding_function=ef)

    file_paths = sorted([p for p in source_folder.glob("**/*") if p.suffix.lower() in (".pdf", ".txt", ".md")])
    if not file_paths:
        print(f"No files found in {source_folder}")
        return

    ids = []
    docs = []
    metas = []
    for p in file_paths:
        if p.suffix.lower() == ".pdf":
            text = extract_pdf_text(str(p))
        else:
            text = p.read_text(encoding="utf-8", errors="ignore")
        if not text:
            continue
        chunks = chunk_text(text, max_chars=chunk_size)
        for i, c in enumerate(chunks):
            ids.append(f"{p.stem}-{i}")
            docs.append(c)
            metas.append({"source": str(p), "chunk": i})
    if ids:
        coll.upsert(ids=ids, documents=docs, metadatas=metas)
        print(f"Indexed {len(ids)} chunks into collection '{collection_name}' (persist: {persist_dir}).")
    else:
        print("No documents to index.")

def query_chroma(collection_name: str, question: str, k: int = 4, persist_dir: Path = CHROMA_PERSIST_DIR):
    client = create_chroma_client(persist_dir)
    coll = client.get_collection(name=collection_name)
    res = coll.query(query_texts=[question], n_results=k)
    out = []
    docs = res.get("documents", [[]])[0]
    metas = res.get("metadatas", [[]])[0]
    for d, m in zip(docs, metas):
        out.append({"text": d, "meta": m})
    return out

def index_folder_to_chroma(
    collection_name: str,
    source_folder: Path,
    persist_dir: Path = CHROMA_PERSIST_DIR,
    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2",
    chunk_size: int = 2000
):
    """
    CLI 互換のラッパー — 内部でクライアントを作成し、既存の build_index_from_files を呼ぶ。
    """
    client = create_chroma_client(persist_dir)
    return build_index_from_files(
        client=client,
        collection_name=collection_name,
        source_folder=source_folder,
        persist_dir=persist_dir,
        embedding_model=embedding_model,
        chunk_size=chunk_size
    )

def main():
    parser = argparse.ArgumentParser(description="Chroma RAG helper (index/query).")
    sub = parser.add_subparsers(dest="cmd")

    p_index = sub.add_parser("index", help="Index PDFs/TXT in folder into Chroma")
    p_index.add_argument("--collection", required=True)
    p_index.add_argument("--source", required=True, help="Source folder with PDFs/TXT")
    p_index.add_argument("--persist", default=str(CHROMA_PERSIST_DIR))
    p_index.add_argument("--model", default="sentence-transformers/all-MiniLM-L6-v2")
    p_index.add_argument("--chunk-size", type=int, default=2000)

    p_q = sub.add_parser("query", help="Query a Chroma collection")
    p_q.add_argument("--collection", required=True)
    p_q.add_argument("--question", required=True)
    p_q.add_argument("--k", type=int, default=4)
    p_q.add_argument("--persist", default=str(CHROMA_PERSIST_DIR))

    args = parser.parse_args()
    if args.cmd == "index":
        index_folder_to_chroma(
            collection_name=args.collection,
            source_folder=Path(args.source),
            persist_dir=Path(args.persist),
            embedding_model=args.model,
            chunk_size=args.chunk_size
        )
    elif args.cmd == "query":
        hits = query_chroma(args.collection, args.question, k=args.k, persist_dir=Path(args.persist))
        for h in hits:
            print("="*40)
            print(h["meta"])
            print(h["text"][:1000])
            print()
    else:
        parser.print_help()

if __name__ == "__main__":
    main()