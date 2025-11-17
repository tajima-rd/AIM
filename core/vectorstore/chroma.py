"""
ChromaDBとの通信を担当するリポジトリ層
(Pydantic非依存・パス修正版)
"""
import logging
import json
import sys
import os
from pathlib import Path
from typing import List, Dict, Any

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    from chromadb.errors import ChromaError
    from chromadb.api.models.Collection import Collection
except ImportError:
    print("Error: 'chromadb' or 'sentence-transformers' not installed.")
    print("Please install them via: pip install chromadb sentence-transformers")
    sys.exit(1)

DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
logger = logging.getLogger(__name__)


class ChromaRepository:
    def __init__(
        self,
        collection_name: str,
        persist_directory: str,  # JSONからは文字列として渡される
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model_name
        
        # 【重要】ここで文字列を Path オブジェクトに変換します
        # これにより .exists() や .mkdir() が使えるようになります
        self.persist_directory = Path(persist_directory)

        # DB接続の初期化
        self._initialize_chroma()

    def _initialize_chroma(self):
        """DB接続の実処理"""
        # DBクライアント作成 (内部で self.persist_directory.exists() を使用)
        self.client = self._create_chroma_client()
        
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=self.ef
        )
        logger.info(f"Collection '{self.collection_name}' loaded/created.")

    @classmethod
    def load_from_json(cls, config_path: Path) -> List["ChromaRepository"]:
        if not config_path.exists():
            print(f"設定ファイルが見つかりません: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data_list = json.load(f)
            
            clients_data_list = None
            # JSON構造の解析
            if isinstance(config_data_list, list):
                for item in config_data_list:
                    if isinstance(item, dict) and "VectorStores" in item:
                        clients_data_list = item["VectorStores"]
                        break
            elif isinstance(config_data_list, dict) and "VectorStores" in config_data_list:
                clients_data_list = config_data_list["VectorStores"]
            
            if clients_data_list is None:
                raise ValueError("JSON内に 'VectorStores' キーが見つかりません。")

            if not isinstance(clients_data_list, list):
                raise ValueError("JSON内の 'VectorStores' がリストではありません。")

            repositories = []
            for store_config in clients_data_list:
                try:
                    # ここで __init__ が呼ばれる (引数はすべて文字列のまま)
                    repo_instance = cls(**store_config)
                    repositories.append(repo_instance)
                except Exception as e:
                    print(f"警告: VectorStore 設定の初期化に失敗しました: {store_config}, エラー: {e}")
                    continue
            
            return repositories
                
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSONパースに失敗しました: {config_path} ({e})")
            raise ValueError(f"Failed to parse config file: {e}") from e
        except Exception as e:
            print(f"設定データのロードに失敗しました: {e}")
            raise ValueError(f"Failed to parse or validate config data: {e}") from e
    
    def _create_chroma_client(self) -> chromadb.Client:    
        if self.persist_directory is None:
            logger.error("ChromaDB の persist_directory が None で指定されました。")
            raise ValueError("persist_directory must be provided.")

        logger.info(f"Initializing Chroma client (persist_directory: {self.persist_directory})")
        
        try:
            # self.persist_directory は Path オブジェクトになっているため .exists() が動作する
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
            return chromadb.Client(settings)
            
        except PermissionError as e:
            logger.error(f"Permission denied for ChromaDB directory: {self.persist_directory}", exc_info=True)
            raise IOError(f"Permission denied for {self.persist_directory}. Check folder permissions.") from e
        except Exception as e:
            logger.error(f"An unexpected error occurred during ChromaDB initialization: {e}", exc_info=True)
            raise Exception(f"An unexpected error occurred: {e}") from e

    def query_collection(
        self, 
        query_texts: List[str], 
        k: int = 4,
        where_filter: Dict[str, Any] = None 
    ) -> List[Dict[str, Any]]:
        if not query_texts:
            logger.warning("Query texts list is empty. Returning empty list.")
            return []

        try:
            logger.info(f"Querying collection '{self.collection_name}' (k={k}, filter={where_filter})")
            
            res = self.collection.query(
                query_texts=query_texts, 
                n_results=k,
                where=where_filter 
            )
            
            out = []
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            distances = res.get("distances", [[]])[0]
            
            if docs is None: docs = []
            if metas is None: metas = []
            if distances is None: distances = []

            for d, m, dist in zip(docs, metas, distances):
                out.append({"text": d, "meta": m, "distance": dist})
                
            return out

        except Exception as e:
            logger.error(f"Failed to query collection {self.collection_name}: {e}", exc_info=True)
            return []
    
    def upsert_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]], 
        ids: List[str],
    ) -> None:
        try:
            if not chunks:
                logger.warning("No chunks provided to index. Skipping.")
                return

            if not (len(chunks) == len(metadatas) == len(ids)):
                msg = f"Length mismatch: Chunks({len(chunks)}), Metadatas({len(metadatas)}), IDs({len(ids)})"
                logger.error(msg)
                raise ValueError(msg)

            logger.info(f"Indexing {len(chunks)} chunks into collection '{self.collection_name}'...")
            
            self.collection.upsert(ids=ids, documents=chunks, metadatas=metadatas)
            
            logger.info(f"Indexed (upserted) {len(chunks)} chunks into collection '{self.collection_name}'.")

        except Exception as e:
            logger.error(f"Failed to build index for collection {self.collection_name}: {e}", exc_info=True)
            print(f"Error building index: {e}")

    def delete_chunks(
        self,
        ids: List[str] = None,
        where: Dict[str, Any] = None
    ) -> None:
        if ids is None and where is None:
            msg = "Failed to delete: At least one of 'ids' or 'where' must be provided."
            logger.error(msg)
            raise ValueError(msg)

        try:
            logger.info(f"Attempting to delete from collection '{self.collection_name}'...")
            
            self.collection.delete(ids=ids, where=where)
            
            logger.info(f"Successfully deleted chunks from '{self.collection_name}'.")

        except Exception as e:
            logger.error(f"Failed to delete from collection {self.collection_name}: {e}", exc_info=True)