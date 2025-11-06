from dataclasses import dataclass
from typing import (
    List, 
    Dict, 
    Union, 
    Tuple,
    Any, 
    Literal,
    Optional
)

class AddtionalAttribute:
    def __init__(
        self,
        key: str,
        value: Any,
        namespace: str = "",
        classname: str = "",
        datatype: str = "", 
        description: str = ""    
    ):
        self.namespace = namespace
        self.classname = classname
        self.key = key 
        self.value = value 
        self.datatype = datatype 
        self.description = description
    
    def __repr__(self) -> str:
        return f"AddtionalAttribute(key='{self.key}', value={self.value}, datatype='{self.datatype}')"

    def as_db_tuple(self) -> tuple:
        """
        DBに挿入するためのパラメータ順にタプルを返します。
        """
        return (
            self.namespace,
            self.classname,
            self.key,
            str(self.value), # DBのTEXT型に合わせて文字列化
            self.datatype,
            self.description
        )

class AttributeRepository:
    def __init__(
        self,
        attributes: List[AddtionalAttribute]
    ):
        self.attributes = attributes if attributes is not None else []
    
    @staticmethod
    def get_create_table_sql(
        table_name: str, 
        parent_table_name: str
    ) -> str:
        """
        Args:
            table_name (str): 
                作成する属性テーブルの名前 (例: "project_attributes")
            parent_table_name (str): 
                紐づける親テーブルの名前 (例: "projects")
        """
        
        # 親テーブル名から、汎用的な外部キーカラム名を生成 (例: "project_id")
        parent_fk_column = f"{parent_table_name.rstrip('s')}_id" 
        
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            id SERIAL PRIMARY KEY,
            
            {parent_fk_column} INTEGER NOT NULL,
            
            -- 属性データ
            namespace TEXT,
            classname TEXT,
            key TEXT NOT NULL,
            value TEXT,
            datatype TEXT,
            description TEXT,
            
            created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
            
            -- 汎用的な外部キー制約
            CONSTRAINT fk_{parent_table_name}
                FOREIGN KEY({parent_fk_column}) 
                REFERENCES {parent_table_name}(id)
                ON DELETE CASCADE,
            
            -- ユニーク制約に親IDも追加
            UNIQUE({parent_fk_column}, namespace, classname, key)
        );
        """

    @staticmethod
    def get_drop_table_sql(table_name: str) -> str:
        # (引数のみ。クラスのデフォルトは使わない)
        return f"DROP TABLE IF EXISTS {table_name};"

    def get_batch_upsert_params(
        self, 
        parent_id: int,           # ★紐づける親ID (例: 5)
        table_name: str,          # ★挿入先のテーブル名 (例: "project_attributes")
        parent_table_name: str    # ★親テーブル名 (例: "projects")
    ) -> Tuple[str, List[tuple]]:
        """
        self.attributes を一括UPSERTするためのSQLとパラメータを返します。
        """
        
        # 親テーブル名から外部キーカラム名を再構築
        parent_fk_column = f"{parent_table_name.rstrip('s')}_id"

        sql = f"""
        INSERT INTO {table_name} (
            {parent_fk_column},  -- ★修正 (例: project_id)
            namespace, classname, key, value, datatype, description
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s) -- プレースホルダは7個
        ON CONFLICT ({parent_fk_column}, namespace, classname, key) DO UPDATE SET
            value = EXCLUDED.value,
            datatype = EXCLUDED.datatype,
            description = EXCLUDED.description,
            updated_at = CURRENT_TIMESTAMP;
        """
        
        params_list = []
        for attr in self.attributes:
            # 外部キーIDを先頭に追加
            params = (parent_id,) + attr.as_db_tuple()
            params_list.append(params)
        
        return sql, params_list
