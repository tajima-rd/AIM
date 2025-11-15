import requests
import json
import uvicorn
import time
import multiprocessing
from enum import Enum
from typing import List, Dict, Optional, Any
from .server import app as server_app
from ...models.drama import Character

class MCPClientManager:
    def __init__(self, host: str = "127.0.0.1", port: int = 8000):
        self.host = host
        self.port = port
        self.server_url = f"http://{self.host}:{self.port}"
        self._server_process: Optional[multiprocessing.Process] = None

    def _run_server_process(self):
        uvicorn.run(server_app, host=self.host, port=self.port)

    def start_server(self, wait: bool = True) -> bool:
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

    def shutdown_server(self):
        if self._server_process and self._server_process.is_alive():
            print("\nMCPサーバーをシャットダウンします。")
            self._server_process.terminate()
            self._server_process.join()
            self._server_process = None
            print("サーバーをシャットダウンしました。")
        else:
            print("サーバーは起動していません。")

    def configure(self, configs: List[Dict]) -> bool:
        # 1. 引数のマッピング
        configs_data = configs 
        configure_endpoint = f"{self.server_url}/configure"
        
        if not configs_data:
            print("PROJECTから有効なジェネレーター設定を構築できませんでした。")
            return False

        request_body = {"configs": configs_data}
        
        print(f">>> MCPサーバー ({configure_endpoint}) に設定を送信します...")
        print(f"/configure へ設定をPOSTします: {request_body}") # server.py側のprintも移植

        try:
            # 2. server.py の try...except ブロックを移植
            response = requests.post(
                configure_endpoint,
                data=json.dumps(request_body), # server.py は json=request_body を使っていた
                headers={"Content-Type": "application/json"},
                timeout=10
            )
            response.raise_for_status()
            
            response_data = response.json() # server.py側の処理
            print(f"サーバーの設定が完了しました。")
            print(f"MCPサーバー設定成功。利用可能なモデル: {response_data.get('configured_generators')}")
            return True

        except requests.exceptions.ConnectionError:
            print(f"/configure 呼び出し失敗: サーバー ({self.server_url}) に接続できません。")
            return False
        except Exception as e:
            # server.py のエラーハンドリングを移植
            print(f"/configure 呼び出し中にエラー: {e}")
            if 'response' in locals() and hasattr(response, 'text'):
                print(f"サーバーからのエラーメッセージ: {response.text}")
            return False

    def generate_text(self, model: str, messages: List[Dict[str, str]]) -> Optional[str]:
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