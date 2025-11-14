import requests
import json
import uvicorn
import time
import multiprocessing
from enum import Enum
from typing import List, Dict, Optional, Any

class MCPClientManager:
    """
    MCPサーバーの起動・シャットダウンを管理し、
    クライアントとしてサーバーと通信する機能を提供するクラス。
    """
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.server_url = f"http://{self.host}:{self.port}"
        self._server_process: Optional[multiprocessing.Process] = None

    def _run_server_process(self):
        """
        [内部メソッド] uvicornサーバーを起動するためのターゲット関数。
        """
        uvicorn.run("lib.aim.mcp.server:app", host=self.host, port=self.port)

    def start_server(self, wait: bool = True) -> bool:
        """
        MCPサーバーをバックグラウンドプロセスとして起動する。

        Args:
            wait (bool): Trueの場合、サーバーが完全に起動するまで待機する。

        Returns:
            bool: サーバーの起動が成功したか（または既に起動しているか）。
        """
        if self._server_process and self._server_process.is_alive():
            print("サーバーは既に起動しています。")
            return True

        print("MCPサーバーをバックグラウンドで起動します...")
        self._server_process = multiprocessing.Process(target=self._run_server_process)
        self._server_process.start()
        
        if wait:
            return self.wait_for_server_ready()
        return True

    def wait_for_server_ready(self, retries: int = 10, delay: int = 1) -> bool:
        """
        MCPサーバーが起動し、リクエストを受け付ける準備ができるまで待機する。
        """
        print("サーバーの起動を待っています...")
        health_endpoint = f"{self.server_url}/health"
        for i in range(retries):
            try:
                response = requests.get(health_endpoint, timeout=1)
                if response.status_code == 200:
                    print("サーバーが起動しました。")
                    return True
            except requests.ConnectionError:
                time.sleep(delay)
        
        print("サーバーの起動に失敗しました。")
        return False
    
    def generate_speech(self, model: str, ssml_text: str, characters: List['Character'], output_filename: str) -> Optional[str]:
        """
        MCPサーバーに音声生成リクエストを送信する。
        """
        speech_endpoint = f"{self.server_url}/generate_speech"
        
        # Characterオブジェクトを辞書に変換
        char_list_dict = [char.__dict__ for char in characters]
        # Enumオブジェクトは単純に変換できないため、voice.nameなどを渡す必要がある
        for char_dict in char_list_dict:
            if 'voice' in char_dict and isinstance(char_dict['voice'], Enum):
                char_dict['voice'] = char_dict['voice'].name

        request_data = {
            "model": model,
            "ssml_text": ssml_text,
            "characters": char_list_dict,
            "output_filename": output_filename
        }
        
        print(f">>> MCPサーバーに '{model}' モデルで音声生成リクエストを送信します...")
        
        try:
            response = requests.post(
                speech_endpoint,
                data=json.dumps(request_data, default=str), # default=strでEnumなどを安全に変換
                headers={"Content-Type": "application/json"},
                timeout=180 # 音声生成は時間がかかる場合がある
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("file_path")
        except Exception as e:
            print(f"音声生成リクエスト中にエラーが発生しました: {e}")
            if 'response' in locals():
                print(f"サーバーからのエラーメッセージ: {response.text}")
            return None

    def shutdown_server(self):
        """
        起動中のMCPサーバープロセスをシャットダウンする。
        """
        if self._server_process and self._server_process.is_alive():
            print("\nMCPサーバーをシャットダウンします。")
            self._server_process.terminate()
            self._server_process.join()
            self._server_process = None
            print("サーバーをシャットダウンしました。")
        else:
            print("サーバーは起動していません。")

    def configure(self, configs: List[Dict]) -> bool:
        """
        MCPサーバーにジェネレーターの設定情報をPOSTする。
        """
        configure_endpoint = f"{self.server_url}/configure"
        request_data = {"configs": configs}
        
        print(f">>> MCPサーバー ({configure_endpoint}) に設定を送信します...")
        
        try:
            response = requests.post(
                configure_endpoint,
                data=json.dumps(request_data),
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            print("サーバーの設定が完了しました。")
            print(f"サーバーからの応答: {response.json()}")
            return True
        except Exception as e:
            print(f"サーバーの設定中にエラーが発生しました: {e}")
            if 'response' in locals():
                print(f"サーバーからのエラーメッセージ: {response.text}")
            return False

    def generate_text(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
        """
        MCPサーバーにテキスト生成リクエストを送信する。
        """
        generate_endpoint = f"{self.server_url}/generate_text" # エンドポイント名を確認
        request_data = {"model": model, "messages": messages}
        
        print(f">>> MCPサーバーに '{model}' モデルでリクエストを送信します...")
        
        # ★★★ この try...except ブロックを復元する ★★★
        try:
            response = requests.post(
                generate_endpoint,
                data=json.dumps(request_data),
                headers={"Content-Type": "application/json"},
                timeout=120
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("response_text")

        except requests.exceptions.HTTPError as http_err:
            print(f"HTTPエラーが発生しました: {http_err}")
            # 'response'変数がこのスコープに存在することを保証するため、エラーハンドリングを修正
            if 'response' in locals() and response:
                print(f"サーバーからのエラーメッセージ: {response.text}")
        except requests.exceptions.RequestException as req_err:
            print(f"サーバーへの接続中にエラーが発生しました: {req_err}")
        except Exception as e:
            print(f"予期せぬエラーが発生しました: {e}")
        
        return None

    def generate_speech(self, model: str, ssml_text: str, characters: List[Any], output_filename: str) -> Optional[str]:
        """
        MCPサーバーに音声生成リクエストを送信する。
        """
        speech_endpoint = f"{self.server_url}/generate_speech"
        
        # Characterオブジェクトのリストを、JSONで送信可能な辞書のリストに変換
        char_list_dict = []
        for char in characters:
            char_dict = char.__dict__.copy() # オブジェクトを辞書に
            # voice属性がEnumインスタンスの場合、その名前(文字列)に変換
            if 'voice' in char_dict and isinstance(char_dict['voice'], Enum):
                char_dict['voice'] = char_dict['voice'].name
            char_list_dict.append(char_dict)

        request_data = {
            "model": model,
            "ssml_text": ssml_text,
            "characters": char_list_dict,
            "output_filename": output_filename
        }
        
        print(f">>> MCPサーバーに '{model}' モデルで音声生成リクエストを送信します...")
        
        try:
            response = requests.post(
                speech_endpoint,
                data=json.dumps(request_data, default=str),
                headers={"Content-Type": "application/json"},
                timeout=180 # 音声生成は時間がかかる場合がある
            )
            response.raise_for_status()
            response_data = response.json()
            return response_data.get("file_path")
        except Exception as e:
            print(f"音声生成リクエスト中にエラーが発生しました: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"サーバーからのエラーメッセージ: {response.text}")
            return None