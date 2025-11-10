from dataclasses import dataclass, field
from typing import Dict, Any, List
import uuid

# -----------------------------------------------------------
# 1. 「親」クラス： 書籍、論文、記事の「全体」
# -----------------------------------------------------------
@dataclass
class SourceCollection:
    """
    RAGの検索対象となる「コレクション」単位（書籍一冊、論文一本など）
    を管理するクラス。
    """
    
    collection_id: str
    """
    このコレクション（本、論文）の固有ID。
    (例: "isbn:978-...", "doi:10.1109/...")
    """
    
    source_type: str # "book", "paper", "article"
    
    metadata: Dict[str, Any]
    """
    コレクション全体の情報（タイトル、著者など）と、
    絞り込み検索用の情報（時代、地域、分野）を格納する。
    
    【格納例】
    {
        # 基本情報
        "title": "日本の近世史",
        "author": ["鈴木 一郎"],
        "publication_date": "2010-05-01",
        
        # --- 絞り込み用の情報 ---
        "era": "江戸時代", # 時代
        "region": "日本",     # 地域
        "domain": "歴史学"   # 分野
        # -------------------------------
    }
    """
    
    summary_text: str = None
    """
    このコレクション「全体」の要約テキスト。
    ステップ1のベクトル検索対象として使用できる。
    """

# -----------------------------------------------------------
# 2. 「子」クラス： チャンク（章、節、段落）
# -----------------------------------------------------------
@dataclass
class SourceNode:
    """
    SourceCollection（親）に属する、個別のテキストチャンク（ノード）。
    """
    
    text: str
    """分割されたテキストチャンク。"""
    
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    """このノード固有のID。"""
    
    parent_collection_id: str
    """このノードが属する SourceCollection の collection_id。"""
    
    metadata: Dict[str, Any]
    """
    このノード固有の出典情報（章、ページ番号など）。
    
    【格納例】
    {
        "chapter": 5,
        "section_title": "5.2 参勤交代の影響",
        "page_number": 152,
        
        # (推奨) 親の絞り込み情報もコピーしておくと、
        # ノード単体での検索時にもフィルタリングが効く。
        "era": "江戸時代",
        "region": "日本",
        "domain": "歴史学"
    }
    """
    
    embedding: List[float] = field(default=None, repr=False)
    """このノード（text）のベクトル表現。"""