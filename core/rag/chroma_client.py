"""
Chroma RAG クライアント

指定されたフォルダ内のドキュメント（PDF, TXT, MD）を読み込み、
フラットな構造で ChromaDB にインデックスを作成し、クエリを実行するユーティリティ。

前提:
- このファイルは `lib/aim/rag/chroma_client.py` に配置されます。
- `lib/aim/utils/text_processing.py` に `extract_pdf_text` と `chunk_text` が
  実装されている必要があります。

CLI実行例:
1. インデックス作成:
   python -m lib.aim.rag.chroma_client index \
       --collection "my_docs" \
       --source "path/to/source_files" \
       --persist ".chromadb_storage"

2. クエリ実行:
   python -m lib.aim.rag.chroma_client query \
       --collection "my_docs" \
       --question "RAGとは何ですか？" \
       --persist ".chromadb_storage"
"""

import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
except ImportError:
    print("Error: 'chromadb' or 'sentence-transformers' not installed.")
    print("Please install them via: pip install chromadb sentence-transformers")
    exit(1)

try:
    from ...utils.text_processing import extract_pdf_text, chunk_text
except ImportError:
    print("Error: Could not import text processing functions.")
    print("Ensure 'lib/aim/utils/text_processing.py' exists and contains 'extract_pdf_text' and 'chunk_text'.")
    # CLI実行のために、ダミー関数を定義（スクリプトが停止しないように）
    def extract_pdf_text(path: str) -> str:
        print(f"[Warning] Using DUMMY extract_pdf_text for {path}")
        return "Dummy PDF Text"
    def chunk_text(text: str, max_chars: int) -> List[str]:
        print(f"[Warning] Using DUMMY chunk_text (size: {max_chars})")
        return [text[i:i+max_chars] for i in range(0, len(text), max_chars)]

CHROMA_PERSIST_DIR = Path(".chromadb")
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 2000

logger = logging.getLogger(__name__)

def create_chroma_client(persist_directory: Path = CHROMA_PERSIST_DIR) -> chromadb.Client:
    """
    ChromaDBクライアントを指定された永続ディレクトリで初期化（または接続）する。
    """
    logger.info(f"Initializing Chroma client (persist_directory: {persist_directory})")
    
    # Chroma 0.5.x 以降の推奨設定
    settings = Settings(
        persist_directory=str(persist_directory),
        is_persistent=True,
    )
    client = chromadb.Client(settings)
    return client

def build_index_from_files(
    client: chromadb.Client,
    collection_name: str,
    source_folder: Path,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    chunk_size: int = DEFAULT_CHUNK_SIZE
):
    """
    指定されたフォルダからファイルを読み込み、チャンク化し、Chromaコレクションにインデックスを作成する。

    注意: この関数はクライアントの永続ディレクトリ設定（persist_dir）を直接は扱いません。
          クライアントは `create_chroma_client` ですでに設定済みである必要があります。
    """
    try:
        ef = embedding_functions.SentenceTransformerEmbeddingFunction(model_name=embedding_model)
        logger.info(f"Getting or creating collection: {collection_name} (Model: {embedding_model})")
        coll = client.get_or_create_collection(name=collection_name, embedding_function=ef)

        file_paths = sorted([p for p in source_folder.glob("**/*") if p.suffix.lower() in (".pdf", ".txt", ".md") and p.is_file()])
        if not file_paths:
            logger.warning(f"No source files (.pdf, .txt, .md) found in {source_folder}")
            print(f"No source files found in {source_folder}")
            return

        logger.info(f"Found {len(file_paths)} files to index...")

        ids = []
        docs = []
        metas = []
        
        for p in file_paths:
            logger.debug(f"Processing file: {p}")
            try:
                if p.suffix.lower() == ".pdf":
                    text = extract_pdf_text(str(p))
                else:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                
                if not text or text.strip() == "":
                    logger.warning(f"No text extracted from {p}, skipping.")
                    continue
                
                chunks = chunk_text(text, max_chars=chunk_size)
                
                for i, c in enumerate(chunks):
                    # IDはファイル名とチャンク番号で構成
                    doc_id = f"{p.stem}-{i}"
                    ids.append(doc_id)
                    docs.append(c)
                    metas.append({"source": str(p.resolve()), "chunk": i})
            
            except Exception as e:
                logger.error(f"Failed to process file {p}: {e}", exc_info=True)

        if ids:
            logger.info(f"Indexing {len(ids)} chunks into collection '{collection_name}'...")
            # upsert を使い、既存のIDがあれば更新
            coll.upsert(ids=ids, documents=docs, metadatas=metas)
            print(f"Indexed (upserted) {len(ids)} chunks into collection '{collection_name}'.")
        else:
            logger.info("No documents to index.")
            print("No documents to index.")

    except Exception as e:
        logger.error(f"Failed to build index for collection {collection_name}: {e}", exc_info=True)
        print(f"Error building index: {e}")

def index_folder_to_chroma(
    collection_name: str,
    source_folder: Path,
    persist_dir: Path = CHROMA_PERSIST_DIR,
    embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    chunk_size: int = DEFAULT_CHUNK_SIZE
):
    """
    CLI互換のラッパー。
    クライアントを作成し、`build_index_from_files` を呼び出す。
    """
    try:
        client = create_chroma_client(persist_dir)
        build_index_from_files(
            client=client,
            collection_name=collection_name,
            source_folder=source_folder,
            embedding_model=embedding_model,
            chunk_size=chunk_size
        )
    except Exception as e:
        logger.error(f"index_folder_to_chroma failed: {e}", exc_info=True)
        print(f"Error during indexing: {e}")

def query_chroma(
    collection_name: str, 
    question: str, 
    k: int = 4, 
    persist_dir: Path = CHROMA_PERSIST_DIR
) -> List[Dict[str, Any]]:
    """
    既存のChromaコレクションにクエリを実行し、結果を整形して返す。
    """
    try:
        client = create_chroma_client(persist_dir)
        
        logger.info(f"Querying collection '{collection_name}' (k={k})")
        coll = client.get_collection(name=collection_name)
        
        res = coll.query(query_texts=[question], n_results=k)
        
        out = []
        docs = res.get("documents", [[]])[0]
        metas = res.get("metadatas", [[]])[0]
        distances = res.get("distances", [[]])[0]
        
        for d, m, dist in zip(docs, metas, distances):
            out.append({"text": d, "meta": m, "distance": dist})
            
        return out

    except chromadb.errors.CollectionNotFoundError:
        logger.error(f"Collection '{collection_name}' not found at {persist_dir}.")
        print(f"Error: Collection '{collection_name}' not found.")
        return []
    except Exception as e:
        logger.error(f"Failed to query collection {collection_name}: {e}", exc_info=True)
        print(f"Error querying collection: {e}")
        return []

def main():
    """
    コマンドラインインターフェースのエントリポイント。
    """
    # CLI実行時には基本的なロギングを設定
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    parser = argparse.ArgumentParser(description="Chroma RAG helper (index/query).")
    sub = parser.add_subparsers(dest="cmd", help="Command to execute", required=True)

    # --- Index コマンド ---
    p_index = sub.add_parser("index", help="Index PDFs/TXT/MD in folder into Chroma")
    p_index.add_argument("--collection", required=True, help="Name of the Chroma collection.")
    p_index.add_argument("--source", required=True, help="Source folder with PDFs/TXT/MD files.")
    p_index.add_argument("--persist", default=str(CHROMA_PERSIST_DIR), help=f"Chroma persist directory (default: {CHROMA_PERSIST_DIR})")
    p_index.add_argument("--model", default=DEFAULT_EMBEDDING_MODEL, help=f"Embedding model (default: {DEFAULT_EMBEDDING_MODEL})")
    p_index.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE, help=f"Chunk size in characters (default: {DEFAULT_CHUNK_SIZE})")

    # --- Query コマンド ---
    p_q = sub.add_parser("query", help="Query a Chroma collection")
    p_q.add_argument("--collection", required=True, help="Name of the Chroma collection.")
    p_q.add_argument("--question", required=True, help="Question to ask.")
    p_q.add_argument("--k", type=int, default=4, help="Number of results (k) (default: 4)")
    p_q.add_argument("--persist", default=str(CHROMA_PERSIST_DIR), help=f"Chroma persist directory (default: {CHROMA_PERSIST_DIR})")

    args = parser.parse_args()

    if args.cmd == "index":
        print(f"Starting indexing...")
        index_folder_to_chroma(
            collection_name=args.collection,
            source_folder=Path(args.source),
            persist_dir=Path(args.persist),
            embedding_model=args.model,
            chunk_size=args.chunk_size
        )
        print(f"Indexing complete.")
        
    elif args.cmd == "query":
        print(f"Querying collection '{args.collection}' with question: '{args.question[:50]}...'")
        hits = query_chroma(
            collection_name=args.collection, 
            question=args.question, 
            k=args.k, 
            persist_dir=Path(args.persist)
        )
        
        if not hits:
            print("No results found.")
            return
            
        print(f"Found {len(hits)} results:")
        for i, h in enumerate(hits):
            print("="*40)
            print(f"Rank {i+1} (Distance: {h.get('distance', 0.0):.4f})")
            print(f"Source: {h['meta'].get('source', 'N/A')} (Chunk: {h['meta'].get('chunk', 'N/A')})")
            print("---")
            print(h["text"][:1000] + "..." if len(h["text"]) > 1000 else h["text"])
            print()

if __name__ == "__main__":
    main()