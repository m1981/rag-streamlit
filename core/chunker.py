import re
from dataclasses import dataclass
from typing import List


@dataclass
class TimeChunkModel:
    start_time_str: str
    start_seconds: int
    url: str
    chunk_text: str
    llm_summary: str = ""


class TranscriptChunker:
    def __init__(self, window_seconds: int = 60):
        self.window_seconds = window_seconds
        # Matches: [00:14](.be/bkcsR2XFU48?t=14) Text
        self.pattern = re.compile(r"\[(\d{2}:\d{2})\]\((.*?)\)\s*(.*)")

    def process_raw_text(self, raw_text: str) -> List[TimeChunkModel]:
        lines = raw_text.strip().split("\n")
        chunks = []
        current_text = []
        current_start_time = 0
        current_start_str = ""
        current_url = ""

        for line in lines:
            match = self.pattern.match(line.strip())
            if not match:
                continue

            time_str, raw_url, text = match.groups()
            text = text.strip()

            if text == "[Muzyka]" or not text:
                continue

            full_url = raw_url.replace(".be/", "https://youtu.be/")
            minutes, secs = map(int, time_str.split(":"))
            total_seconds = minutes * 60 + secs

            # Initialize new chunk
            if not current_text:
                current_start_time = total_seconds
                current_start_str = time_str
                current_url = full_url

            current_text.append(text)

            # Close chunk if window exceeded
            if total_seconds - current_start_time >= self.window_seconds:
                chunks.append(
                    TimeChunkModel(
                        start_time_str=current_start_str,
                        start_seconds=current_start_time,
                        url=current_url,
                        chunk_text=" ".join(current_text),
                    )
                )
                current_text = []

        # Catch remaining text
        if current_text:
            chunks.append(
                TimeChunkModel(
                    start_time_str=current_start_str,
                    start_seconds=current_start_time,
                    url=current_url,
                    chunk_text=" ".join(current_text),
                )
            )

        return chunks
