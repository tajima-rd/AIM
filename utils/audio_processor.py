import struct
import io
from pathlib import Path
from pydub import AudioSegment
from typing import Dict, Optional

class AudioProcessor:
    """
    生の音声データを加工し、ファイルとして保存する責務を持つクラス。
    """
    def parse_audio_mime_type(self, mime_type: str) -> Dict[str, int]:
        """
        MIMEタイプ文字列から音声のパラメータ（ビット深度、サンプルレート）を解析する。
        """
        bits_per_sample = 16
        rate = 24000
        parts = mime_type.split(";")
        for param in parts:
            param = param.strip()
            if param.lower().startswith("rate="):
                try:
                    rate = int(param.split("=", 1)[1])
                except (ValueError, IndexError):
                    pass
            elif param.startswith("audio/L"):
                try:
                    bits_per_sample = int(param.split("L", 1)[1])
                except (ValueError, IndexError):
                    pass
        return {"bits_per_sample": bits_per_sample, "rate": rate}

    def convert_to_wav(self, raw_data: bytes, mime_type: str) -> bytes:
        """
        MIMEタイプ情報に基づき、生の音声データにWAVヘッダを付与する。
        """
        parameters = self.parse_audio_mime_type(mime_type)
        bits_per_sample = parameters["bits_per_sample"]
        sample_rate = parameters["rate"]
        num_channels = 1
        data_size = len(raw_data)
        bytes_per_sample = bits_per_sample // 8
        block_align = num_channels * bytes_per_sample
        byte_rate = sample_rate * block_align
        chunk_size = 36 + data_size

        header = struct.pack(
            "<4sI4s4sIHHIIHH4sI",
            b"RIFF", chunk_size, b"WAVE", b"fmt ",
            16, 1, num_channels, sample_rate,
            byte_rate, block_align, bits_per_sample,
            b"data", data_size
        )
        return header + raw_data

    def save_as_mp3(self, wav_bytes: bytes, output_path: Path) -> Optional[Path]:
        """
        WAV形式のバイトデータをMP3ファイルとして保存する。
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            audio = AudioSegment.from_file(io.BytesIO(wav_bytes), format="wav")
            audio.export(output_path, format="mp3")
            print(f"MP3ファイルとして保存しました: {output_path}")
            return output_path
        except FileNotFoundError:
            print("エラー: ffmpegが見つかりません。ffmpegをインストールし、システムPATHに設定してください。")
            return None
        except Exception as e:
            print(f"MP3への変換中にエラーが発生しました: {e}")
            return None