import argparse
import json
import logging
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    import chromadb
    from chromadb.config import Settings
    from chromadb.utils import embedding_functions
    from chromadb.api.types import EmbeddingFunction
except ImportError:
    print("Error: 'chromadb' or 'sentence-transformers' not installed.")
    print("Please install them via: pip install chromadb sentence-transformers")
    exit(1)

# 2階層上の utils をインポート
try:
    from ...utils.text_processing import extract_pdf_text, chunk_text
except ImportError:
    print("Error: Could not import text processing functions.")
    print("Ensure 'lib/aim/utils/text_processing.py' exists and contains 'extract_pdf_text' and 'chunk_text'.")
    # CLI実行のために、ダミー関数を定義
    def extract_pdf_text(path: str) -> str:
        print(f"[Warning] Using DUMMY extract_pdf_text for {path}")
        return "Dummy PDF Text: " + "江戸時代の参勤交代は..." * 10
    def chunk_text(text: str, max_chars: int, overlap: int = 0) -> List[str]:
        print(f"[Warning] Using DUMMY chunk_text (size: {max_chars})")
        # overlap を考慮した簡易チャンキング
        chunks = []
        start = 0
        while start < len(text):
            end = start + max_chars
            chunks.append(text[start:end])
            start += max_chars - overlap
        return chunks


# --- ロガー ---
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# --- デフォルト設定 ---
DEFAULT_PERSIST_DIR = Path(".chromadb_hierarchical")
DEFAULT_EMBEDDING_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
DEFAULT_CHUNK_SIZE = 1000
DEFAULT_CHUNK_OVERLAP = 100

# ===========================================================
# 1. 階層データ構造 (Dataclass) の定義
# ===========================================================

@dataclass
class SourceCollection:
    """
    RAGの検索対象となる「コレクション」単位（書籍一冊、論文一本など）
    を管理するクラス。（親）
    """
    collection_id: str
    source_type: str
    metadata: Dict[str, Any]
    summary_text: str = ""

@dataclass
class SourceNode:
    """
    SourceCollection（親）に属する、個別のテキストチャンク（ノード）。（子）
    """
    text: str
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    parent_collection_id: str
    metadata: Dict[str, Any]
    embedding: Optional[List[float]] = field(default=None, repr=False)


# ===========================================================
# 2. 階層型RAGクライアントクラス
# ===========================================================

class HierarchicalRagClient:
    """
    階層型RAGインデックス（親/子コレクション）を管理・操作するクライアント。
    """
    
    def __init__(
        self,
        collection_name_base: str = "my_docs",
        persist_directory: Path = DEFAULT_PERSIST_DIR,
        embedding_model_name: str = DEFAULT_EMBEDDING_MODEL
    ):
        """
        クライアントを初期化し、2つのChromaコレクションに接続します。
        """
        logger.info(f"Initializing HierarchicalRagClient for base '{collection_name_base}' at {persist_directory}")
        
        self.collection_name_base = collection_name_base
        self.persist_directory = persist_directory
        
        # 1. ChromaDBクライアントの初期化
        try:
            settings = Settings(
                persist_directory=str(persist_directory.resolve()),
                is_persistent=True,
            )
            self.client_chroma = chromadb.Client(settings)
        except Exception as e:
            logger.critical(f"Failed to initialize Chroma client: {e}", exc_info=True)
            raise
            
        # 2. 埋め込み関数の初期化
        try:
            self.embedding_function = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=embedding_model_name
            )
        except Exception as e:
            logger.critical(f"Failed to load embedding model '{embedding_model_name}': {e}", exc_info=True)
            print("Error: Failed to load embedding model.")
            print("Ensure 'sentence-transformers' is installed and the model name is correct.")
            raise

        # 3. 親子コレクションの取得・作成
        self.collection_name_collections = f"{collection_name_base}_collections"
        self.collection_name_nodes = f"{collection_name_base}_nodes"

        self._coll_collections = self.client_chroma.get_or_create_collection(
            name=self.collection_name_collections,
            embedding_function=self.embedding_function
        )
        logger.info(f"Connected to 'Parent' collection: {self.collection_name_collections}")

        self._coll_nodes = self.client_chroma.get_or_create_collection(
            name=self.collection_name_nodes,
            embedding_function=self.embedding_function
        )
        logger.info(f"Connected to 'Child' collection: {self.collection_name_nodes}")

    # --- インデックス追加 ---

    def add_pdf(
        self,
        pdf_path: Path,
        metadata_dict: Dict[str, Any],
        chunk_size: int = DEFAULT_CHUNK_SIZE,
        chunk_overlap: int = DEFAULT_CHUNK_OVERLAP
    ) -> dict:
        """
        単一のPDFとそのメタデータを、階層RAGインデックスに追加する。
        """
        if not pdf_path.exists() or not pdf_path.is_file():
            msg = f"PDF file not found: {pdf_path}"
            logger.error(msg)
            return {"success": False, "message": msg}

        try:
            # === 1. SourceCollection（親）の準備 ===
            
            # 親IDを決定（メタデータに 'id' があれば優先、なければファイル名）
            collection_id = metadata_dict.get("id", pdf_path.stem)
            
            # 親のメタデータを構築（フィルタリング用）
            parent_metadata = {
                "title": metadata_dict.get("title", pdf_path.name),
                "author": metadata_dict.get("author", []),
                "publication_date": metadata_dict.get("publication_date"),
                "era": metadata_dict.get("era"),
                "region": metadata_dict.get("region"),
                "domain": metadata_dict.get("domain"),
                "source_type": metadata_dict.get("source_type", "pdf"),
                "source_location": str(pdf_path.resolve()) # 元ファイルへの参照
            }
            
            summary_text = metadata_dict.get("summary_text")
            if not summary_text:
                summary_text = f"Title: {parent_metadata['title']}. Author(s): {', '.join(parent_metadata.get('author', []))}"
                logger.warning(f"summary_text not found for {pdf_path.name}. Using fallback summary.")

            sc = SourceCollection(
                collection_id=collection_id,
                source_type=parent_metadata["source_type"],
                metadata=parent_metadata,
                summary_text=summary_text
            )

            # 親コレクション (xxx_collections) に格納 (upsertで更新)
            self._coll_collections.upsert(
                ids=[sc.collection_id],
                documents=[sc.summary_text], # 要約文をベクトル化
                metadatas=[sc.metadata]
            )
            logger.info(f"Upserted Parent Collection: {sc.collection_id}")

            # === 2. SourceNode（子）の準備と格納 ===
            
            # 1. PDFからテキスト抽出
            full_text = extract_pdf_text(str(pdf_path))
            if not full_text or full_text.strip() == "":
                msg = f"No text extracted from {pdf_path.name}."
                logger.warning(msg)
                return {"success": False, "message": msg, "collection_id": collection_id, "nodes_added": 0}

            # 2. テキストをチャンキング
            text_chunks = chunk_text(
                full_text, 
                max_chars=chunk_size, 
                overlap=chunk_overlap
            )
            
            nodes_to_add_ids = []
            nodes_to_add_docs = []
            nodes_to_add_metas = []

            # 3. SourceNode を生成
            for i, chunk_text in enumerate(text_chunks):
                node_id = f"{collection_id}_node_{i}"
                
                # 子ノード固有のメタデータ
                node_meta = { "chunk_number": i }
                
                # ★重要：親のメタデータ（時代・地域・分野など）を子ノードにコピー
                node_meta.update(parent_metadata)
                
                sn = SourceNode(
                    text=chunk_text,
                    node_id=node_id,
                    parent_collection_id=collection_id, # ★親との紐付け
                    metadata=node_meta
                )
                
                nodes_to_add_ids.append(sn.node_id)
                nodes_to_add_docs.append(sn.text) # 本文（チャンク）をベクトル化
                nodes_to_add_metas.append(sn.metadata)

            # 4. 子コレクション (xxx_nodes) に一括格納 (upsertで更新)
            if nodes_to_add_ids:
                self._coll_nodes.upsert(
                    ids=nodes_to_add_ids,
                    documents=nodes_to_add_docs,
                    metadatas=nodes_to_add_metas
                )
            
            msg = f"Successfully indexed {pdf_path.name}. (1 Parent, {len(nodes_to_add_ids)} Nodes)"
            logger.info(msg)
            return {
                "success": True, 
                "message": msg, 
                "collection_id": collection_id, 
                "nodes_added": len(nodes_to_add_ids)
            }

        except Exception as e:
            msg = f"Failed to index {pdf_path.name}: {e}"
            logger.exception(msg)
            return {"success": False, "message": msg}

    # --- クエリ実行 ---

    def query(
        self,
        query_text: str,
        k: int = 5,
        # メタデータ・フィルタリング用の引数
        era: Optional[str] = None,
        region: Optional[str] = None,
        domain: Optional[str] = None,
        source_type: Optional[str] = None,
        parent_id: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        階層インデックスにクエリを実行する。
        メタデータ（era, regionなど）での絞り込み検索（フィルタリング）を行う。
        """
        
        # === ステップ1: フィルタリング (Where句の構築) ===
        # 子ノード (SourceNode) のメタデータには親の情報がコピーされているため、
        # 子コレクション (xxx_nodes) に対して直接 where フィルタをかける。
        
        where_filter: Dict[str, Any] = {}
        
        if era:
            where_filter["era"] = era
        if region:
            where_filter["region"] = region
        if domain:
            where_filter["domain"] = domain
        if source_type:
            where_filter["source_type"] = source_type
        if parent_id:
            # 特定の書籍（親）の中だけを検索対象にする
            where_filter["parent_collection_id"] = parent_id

        logger.info(f"Querying nodes (k={k}) with filter: {where_filter if where_filter else 'None'}")
        
        # === ステップ2: 子ノードのベクトル検索 ===
        try:
            results = self._coll_nodes.query(
                query_texts=[query_text],
                n_results=k,
                where=where_filter if where_filter else None
            )
            
            # 結果を整形して返す
            out = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            distances = results.get("distances", [[]])[0]
            
            for d, m, dist in zip(docs, metas, distances):
                out.append({"text": d, "meta": m, "distance": dist})
                
            return out

        except Exception as e:
            logger.error(f"Failed to query nodes collection: {e}", exc_info=True)
            return []


# ===========================================================
# 3. CLI (コマンドラインインターフェース)
# ===========================================================

def main():
    parser = argparse.ArgumentParser(description="Hierarchical Chroma RAG Client.")
    parser.add_argument(
        "--base-name", 
        required=True, 
        help="Base name for the Chroma collections (e.g., 'my_library')."
    )
    parser.add_argument(
        "--persist", 
        default=str(DEFAULT_PERSIST_DIR), 
        help=f"Chroma persist directory (default: {DEFAULT_PERSIST_DIR})"
    )
    
    subparsers = parser.add_subparsers(dest="cmd", help="Command to execute", required=True)

    # --- 'add' コマンド (PDF追加) ---
    p_add = subparsers.add_parser("add", help="Add a PDF file to the hierarchical index")
    p_add.add_argument("--pdf", required=True, help="Path to the PDF file.")
    p_add.add_argument(
        "--meta-json", 
        required=True, 
        help="Path to the corresponding .json metadata file."
    )
    p_add.add_argument("--chunk-size", type=int, default=DEFAULT_CHUNK_SIZE)
    p_add.add_argument("--chunk-overlap", type=int, default=DEFAULT_CHUNK_OVERLAP)

    # --- 'query' コマンド (検索) ---
    p_query = subparsers.add_parser("query", help="Query the hierarchical index")
    p_query.add_argument("--question", required=True, help="Question to ask.")
    p_query.add_argument("--k", type=int, default=5, help="Number of results (k) (default: 5)")
    # フィルタリング用オプション
    p_query.add_argument("--era", help="Filter by 'era' metadata (e.g., '江戸時代')")
    p_query.add_argument("--region", help="Filter by 'region' metadata (e.g., '日本')")
    p_query.add_argument("--domain", help="Filter by 'domain' metadata (e.g., '歴史学')")
    p_query.add_argument("--source-type", help="Filter by 'source_type' metadata (e.g., 'paper')")
    p_query.add_argument("--parent-id", help="Filter by specific 'parent_collection_id' (e.g., 'history_book_001')")

    args = parser.parse_args()

    # --- クライアントの初期化 ---
    try:
        client = HierarchicalRagClient(
            collection_name_base=args.base_name,
            persist_directory=Path(args.persist),
            # (Note: embedding_model は CLI 引数で変更可能にしてもよい)
        )
    except Exception as e:
        print(f"Failed to initialize RAG client. Exiting.")
        return

    # --- コマンドの実行 ---
    if args.cmd == "add":
        pdf_path = Path(args.pdf)
        json_path = Path(args.meta_json)
        
        if not json_path.exists():
            print(f"Error: Metadata JSON file not found: {json_path}")
            return
            
        try:
            with open(json_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        except Exception as e:
            print(f"Error reading metadata JSON {json_path}: {e}")
            return
            
        print(f"Adding {pdf_path.name} to index '{args.base_name}'...")
        result = client.add_pdf(
            pdf_path=pdf_path,
            metadata_dict=metadata,
            chunk_size=args.chunk_size,
            chunk_overlap=args.chunk_overlap
        )
        print(json.dumps(result, indent=2, ensure_ascii=False))

    elif args.cmd == "query":
        print(f"Querying '{args.base_name}' with question: '{args.question[:50]}...'")
        hits = client.query(
            query_text=args.question,
            k=args.k,
            era=args.era,
            region=args.region,
            domain=args.domain,
            source_type=args.source_type,
            parent_id=args.parent_id
        )
        
        if not hits:
            print("No results found.")
            return
            
        print(f"Found {len(hits)} results:")
        for i, h in enumerate(hits):
            meta = h.get('meta', {})
            print("="*40)
            print(f"Rank {i+1} (Distance: {h.get('distance', 0.0):.4f})")
            print(f"Source: {meta.get('title', 'N/A')} (ID: {meta.get('parent_collection_id', 'N/A')})")
            print(f"Filter: [Era: {meta.get('era')}, Region: {meta.get('region')}, Domain: {meta.get('domain')}]")
            print(f"Location: {meta.get('source_location')} (Chunk: {meta.get('chunk_number')})")
            print("---")
            text = h.get('text', '')
            print(text[:800] + "..." if len(text) > 800 else text)
            print()

if __name__ == "__main__":
    main()