
import psycopg2
import psycopg2.extras

import psycopg2
import psycopg2.extras
from typing import Optional, List, Tuple, Any

class DBConnection:
    def __init__(
        self,
        host: str,
        port: int,
        database: str,
        user: str,
        password: str,
        driver: str = "psycopg2"
    ):
        """        
        Args:
            host (str): データベースホスト
            port (int): ポート番号
            database (str): データベース名
            user (str): ユーザー名
            password (str): パスワード
            driver (str, optional): 使用するドライバ (現在は 'psycopg2' のみサポート)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        
        if driver != "psycopg2":
            raise ValueError("現在サポートされているドライバは 'psycopg2' のみです。")
        self.driver = driver

    def _get_connection(self):
        try:
            return psycopg2.connect(
                host=self.host,
                port=self.port,
                dbname=self.database,
                user=self.user,
                password=self.password
            )
        except psycopg2.Error as e:
            print(f"データベース接続エラー: {e}")
            raise

    def execute_sql(self, sql: str, params: Optional[tuple] = None) -> Optional[List[tuple]]:
        """
        単一のSQL文（SELECT, INSERT, UPDATE, CREATE TABLE など）を実行します。
        
        Args:
            sql (str): 実行するSQL文。
            params (tuple, optional): SQL文にバインドするパラメータ。
        
        Returns:
            Optional[List[tuple]]: SELECT文の場合は結果セット、それ以外は None。
        """
        print(f"--- 実行 (Single): {sql[:50]}... ---")
        try:
            # 接続の開始と終了を with 文で自動管理
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    
                    cur.execute(sql, params)
                    
                    # SELECT文など、結果が返る場合
                    if cur.description:
                        return cur.fetchall()
                    
                    # INSERT, UPDATE, CREATE など
                    conn.commit()
            
            return None
            
        except psycopg2.Error as e:
            print(f"SQL実行エラー: {e}")
            conn.rollback() # エラー時はロールバック
            raise

    def execute_batch(self, sql: str, params_list: List[tuple]):
        """
        単一のSQL文（通常は INSERT/UPDATE）を、
        複数のパラメータでバッチ実行します。
                
        Args:
            sql (str): 実行するSQL文 (例: "INSERT INTO ... VALUES (%s, %s)")
            params_list (List[tuple]): SQLに渡すパラメータのタプルのリスト
                                        [ (val1, val2), (val3, val4), ... ]
        """
        if not params_list:
            print("バッチ実行: パラメータリストが空のためスキップしました。")
            return
            
        print(f"--- 実行 (Batch, {len(params_list)}件): {sql[:50]}... ---")
        try:
            with self._get_connection() as conn:
                with conn.cursor() as cur:
                    
                    # バッチ実行
                    psycopg2.extras.execute_batch(cur, sql, params_list)
                    
                    conn.commit()
                    
        except psycopg2.Error as e:
            print(f"バッチ実行エラー: {e}")
            conn.rollback()
            raise
