from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import requests


@dataclass
class FetchResult:
    success: bool
    content: str = ""
    error_message: Optional[str] = None


class ArticleFetcher:
    def __init__(self, timeout: int = 15, max_content_length: int = 10 * 1024 * 1024):
        self._timeout = timeout
        self._max_content_length = max_content_length
        self._session = requests.Session()
        self._session.headers.update(
            {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "zh-CN,zh;q=0.9,en;q=0.8",
                "Accept-Encoding": "gzip, deflate",
            }
        )

    def fetch(self, url: str) -> FetchResult:
        if not url or not url.strip():
            return FetchResult(success=False, error_message="URL is empty")

        try:
            response = self._session.get(url, timeout=self._timeout)
            response.raise_for_status()
        except requests.exceptions.Timeout:
            return FetchResult(success=False, error_message="Request timed out")
        except requests.exceptions.HTTPError as e:
            return FetchResult(success=False, error_message=f"HTTP error: {str(e)}")
        except requests.exceptions.ConnectionError:
            return FetchResult(success=False, error_message="Connection failed")
        except requests.exceptions.RequestException as e:
            return FetchResult(success=False, error_message=f"Request failed: {str(e)}")

        content = self._decode_content(response)
        if len(content) > self._max_content_length:
            content = content[: self._max_content_length]

        return FetchResult(success=True, content=content)

    def _decode_content(self, response: requests.Response) -> str:
        if response.encoding:
            try:
                return response.text
            except UnicodeDecodeError:
                pass

        for encoding in ["utf-8", "gbk", "gb2312", "gb18030", "latin-1"]:
            try:
                return response.content.decode(encoding)
            except UnicodeDecodeError:
                continue

        return response.content.decode("utf-8", errors="replace")

    @staticmethod
    def get_current_time() -> str:
        return datetime.now().isoformat()
