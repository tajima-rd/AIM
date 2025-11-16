"""
ChromaDBとの通信を担当するリポジトリ層
(元の chroma_client.py をリファクタリング)
"""
import logging, json
from pathlib import Path
from typing import List, Dict, Any
import sys

from pydantic import BaseModel, TypeAdapter

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

class RepositoryConfig(BaseModel):    
    collection_name: str
    persist_directory: Path
    embedding_model: str = DEFAULT_EMBEDDING_MODEL

    @classmethod
    def load_from_json(cls, config_path: Path) -> List["ChromaRepository"]:
        if not config_path.exists():
            print(f"設定ファイルが見つかりません: {config_path}")
            raise FileNotFoundError(f"Config file not found: {config_path}")

        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config_data_list = json.load(f)
            
            # "MCP_Clients" セクションを探す
            clients_data_list = None
            if not isinstance(config_data_list, list):
                 raise ValueError("JSONのルートがリストではありません。")

            for item in config_data_list:
                if isinstance(item, dict) and "VectorStores" in item:
                    clients_data_list = item["VectorStores"]
                    break
            
            if clients_data_list is None:
                raise ValueError("JSON内に 'VectorStores' キーが見つかりません。")

            # Pydantic を使って辞書のリストを VectorStores のリストにパースする
            try:
                # Pydantic v2 (推奨)
                adapter = TypeAdapter(List[cls])
                return adapter.validate_python(clients_data_list)
            except ImportError:
                # Pydantic v1 (フォールバック)
                return None
        
        except json.JSONDecodeError as e:
            print(f"設定ファイルのJSONパースに失敗しました: {config_path} ({e})")
            raise ValueError(f"Failed to parse config file: {e}") from e
        except Exception as e:
            # (Pydantic のバリデーションエラーなどもキャッチ)
            print(f"設定データのパースまたはバリデーションに失敗しました: {e}")
            raise ValueError(f"Failed to parse or validate config data: {e}") from e

class ChromaRepository(BaseModel):
    collection_name: str
    persist_directory: Path
    embedding_model: str = DEFAULT_EMBEDDING_MODEL

    def __init__(
        self,
        collection_name: str,
        persist_directory: Path,
        embedding_model: str = DEFAULT_EMBEDDING_MODEL,
    ):
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model
        self.persist_directory = persist_directory
        
        self.client: chromadb.Client = self._create_chroma_client()
        
        self.ef = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name=self.embedding_model_name
        )
        
        self.collection: Collection = self.client.get_or_create_collection(
            name=self.collection_name, 
            embedding_function=self.ef
        )
        logger.info(f"Collection '{collection_name}' loaded/created.")

    def _create_chroma_client(self) -> chromadb.Client:    
        """
        低レベルのクライアント作成処理 (元のロジックをそのまま使用)
        """
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

    def query_collection(
        self, 
        query_texts: List[str], 
        k: int = 4,
        where_filter: Dict[str, Any] = None # Prologの推論結果でフィルタできるよう引数を追加
    ) -> List[Dict[str, Any]]:
        """
        クエリを実行する。
        (元の query_chroma をベースに、フィルタ機能を追加)
        """
        if not query_texts:
            logger.warning("Query texts list is empty. Returning empty list.")
            return []

        try:
            logger.info(f"Querying collection '{self.collection_name}' (k={k}, filter={where_filter})")
            
            res = self.collection.query(
                query_texts=query_texts, 
                n_results=k,
                where=where_filter # where 句を適用
            )
            
            out = []
            # res の構造に合わせて安全に取得 (元のロジックを流用)
            docs = res.get("documents", [[]])[0]
            metas = res.get("metadatas", [[]])[0]
            distances = res.get("distances", [[]])[0]
            
            for d, m, dist in zip(docs, metas, distances):
                out.append({"text": d, "meta": m, "distance": dist})
                
            return out

        except ChromaError as e:
            logger.error(f"ChromaDB error during query on collection {self.collection_name}: {e}", exc_info=True)
            return []
        except Exception as e:
            logger.error(f"Failed to query collection {self.collection_name}: {e}", exc_info=True)
            return []
    
    def upsert_chunks(
        self,
        chunks: List[str],
        metadatas: List[Dict[str, Any]], # Service層が生成したIDベースのメタデータ
        ids: List[str],
    ) -> None:
        """
        チャンクをUpsertする (元のロジックをそのまま使用)
        """
        try:
            if not chunks:
                logger.warning("No chunks provided to index. Skipping.")
                return

            if not (len(chunks) == len(metadatas) == len(ids)):
                msg = f"Chunks ({len(chunks)}), Metadatas ({len(metadatas)}), and IDs ({len(ids)}) lists must have the same length."
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
        """
        チャンクを削除する (元のロジックをそのまま使用)
        """
        if ids is None and where is None:
            msg = "Failed to delete: At least one of 'ids' or 'where' must be provided."
            logger.error(msg)
            raise ValueError(msg)

        try:
            logger.info(f"Attempting to delete from collection '{self.collection_name}'...")
            if ids:
                logger.info(f"Deleting {len(ids)} specific IDs.")
            if where:
                logger.info(f"Deleting based on 'where' filter: {where}")

            self.collection.delete(ids=ids, where=where)
            
            logger.info(f"Successfully deleted chunks from '{self.collection_name}'.")

        except ChromaError as e:
            logger.error(f"ChromaDB error during delete on collection {self.collection_name}: {e}", exc_info=True)
        except Exception as e:
            logger.error(f"Failed to delete from collection {self.collection_name}: {e}", exc_info=True)