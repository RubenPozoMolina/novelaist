from abc import ABC, abstractmethod
from pathlib import Path

class BaseConverter(ABC):
    def __init__(self, output_dir, config, cover_path=None):
        self.output_dir = Path(output_dir)
        self.config = config
        self.cover_path = cover_path

    @abstractmethod
    def convert(self, content, title):
        pass
