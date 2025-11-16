import argparse
import logging
from pathlib import Path
from typing import List, Dict, Any # <- 先頭に移動
import sys

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    from chromadb.errors import ChromaError 
    from chromadb.api.models.Collection import Collection # Collectionの型ヒント
except ImportError:
    print("Error: 'chromadb' or 'sentence-transformers' not installed.")
    print("Please install them via: pip install chromadb sentence-transformers")
    sys.exit(1)

try:
    from ...utils.text_processing import convert_pdf_markdown, chunk_text
except ImportError:
    print("Error: Could not import text processing functions.")
    print("Ensure 'lib/aim/utils/text_processing.py' exists and contains 'convert_pdf_markdown' and 'chunk_text'.")
    sys.exit(1)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
logger = logging.getLogger(__name__)


class ChromaClient:
    def __init__(
        self,
        collection_name: str, # デフォルトを削除 (明示的に指定させる)
        persist_directory: Path, # デフォルトを削除 (明示的に指定させる)
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.persist_directory = persist_directory
        
        # 1. クライアントを初期化
        self.client: chromadb.Client = self.create_chroma_client()
        
        # 2. 埋め込み関数を初期化
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        # 3. コレクションを取得または作成 (効率化)
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=self.ef
        )
        logger.info(f"Collection '{collection_name}' loaded/created.")

    def create_chroma_client(self) -> chromadb.Client:    
        # (このメソッドは変更なし、元のままでOK)
        if self.persist_directory is None:
            logger.error("ChromaDB の persist_directory が None で指定されました。")
            raise ValueError("persist_directory must be provided and cannot be None.")

        logger.info(f"Initializing Chroma client (persist_directory: {self.persist_directory})")
        
        try:
            if not self.persist_directory.exists():
                logger.info(f"Directory not found. Attempting to create: {self.persist_directory}")
                self.persist_directory.mkdir(parents=True, exist_ok=True)
            elif not self.persist_directory.is_dir():
                logger.error(f"Specified path is not a directory: {self.persist_directory}")
                raise IOError(f"Path '{self.persist_directory}' exists but is not a directory.")

            settings = Settings(
                persist_directory=str(self.persist_directory),
                is_persistent=True,
            )
            client = chromadb.Client(settings)
            return client
            
        except PermissionError as e:
            logger.error(f"Permission denied for ChromaDB directory: {self.persist_directory}", exc_info=True)
            raise IOError(f"Permission denied for {self.persist_directory}. Check folder permissions.") from e
        except ChromaError as e:
            logger.error(f"ChromaDB initialization error: {e}", exc_info=True)
            raise Exception(f"Failed to initialize ChromaDB client (DB might be locked or corrupted): {e}") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during ChromaDB initialization: {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred: {e}") from e

    def query_chroma(
        self, 
        question: str, 
        k: int = 4
    ) -> List[Dict[str, Any]]:
        
        if not question:
            logger.warning("Query question is empty. Returning empty list.")
            return []

        try:
            logger.info(f"Querying collection '{self.collection_name}' (k={k})")
            
            # coll = self.client.get_collection(...) を self.collection に変更
            res = self.collection.query(query_texts=[question], n_results=k)
            
            out = []
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            distances = res.get("distances", [[]])[0]
            
            for d, m, dist in zip(docs, metas, distances):
                out.append({"text": d, "meta": m, "distance": dist})
                
            return out

        except ChromaError as e: # CollectionNotFoundError は ChromaError のサブクラス
            logger.error(f"ChromaDB error during query on collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error querying collection: {e}")
            return []
        except Exception as e:
            logger.error(f"Failed to query collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error querying collection: {e}")
            return []
    
    def upsert_chunks(
        self, # <- self が必須
        chunks: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str],
    ) -> None:
        try:
            # self.collection は __init__ で準備済み
            if not chunks:
                logger.warning("No chunks provided to index. Skipping.")
                print("No documents to index.")
                return

            if not (len(chunks) == len(metadatas) == len(ids)):
                msg = f"Chunks ({len(chunks)}), Metadatas ({len(metadatas)}), and IDs ({len(ids)}) lists must have the same length."
                logger.error(msg)
                raise ValueError(msg)

            logger.info(f"Indexing {len(chunks)} chunks into collection '{self.collection_name}'...")
            
            # coll.upsert を self.collection.upsert に変更
            self.collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
            
            print(f"Indexed (upserted) {len(chunks)} chunks into collection '{self.collection_name}'.")

        except Exception as e:
            logger.error(f"Failed to build index for collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error building index: {e}")

    def upsert_chunk(
            self,
            chunk: str,
            metadata: Dict[str, Any],
            id: str
        ) -> None:
            """
            単一のチャンク、メタデータ、IDをコレクションに upsert (挿入/更新) する。
            内部的にはバッチ処理用の `upsert_chunks` を呼び出します。
            """
            try:
                # 呼び出し先を upsert_chunks に変更
                self.upsert_chunks(
                    chunks=[chunk],
                    metadatas=[metadata],
                    ids=[id]
                )
            except Exception as e:
                logger.error(f"Failed to upsert single chunk (ID: {id}): {e}", exc_info=True)
                print(f"Error upserting single chunk (ID: {id}): {e}")

    def delete_chunks(
        self, # <- 1. 最初の引数は self
        ids: List[str] = None,
        where: Dict[str, Any] = None
    ) -> None:
        
        if ids is None and where is None:
            msg = "Failed to delete: At least one of 'ids' or 'where' must be provided."
            logger.error(msg)
            raise ValueError(msg)

        try:
            # 2. self.collection_name を使用
            logger.info(f"Attempting to delete from collection '{self.collection_name}'...")
            if ids:
                logger.info(f"Deleting {len(ids)} specific IDs.")
            if where:
                logger.info(f"Deleting based on 'where' filter: {where}")

            # 3. self.collection を使用
            self.collection.delete(ids=ids, where=where)
            
            logger.info(f"Successfully deleted chunks from '{self.collection_name}'.")

        except ChromaError as e:
            logger.error(f"ChromaDB error during delete on collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error deleting from collection: {e}")
            
        except Exception as e:
            logger.error(f"Failed to delete from collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error deleting from collection: {e}")