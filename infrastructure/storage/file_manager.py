import os
import json
import logging
from typing import Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class FileManager:
    """Manager for local file operations."""

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.ensure_base_path()

    def ensure_base_path(self):
        """Ensure the base path exists."""
        try:
            self.base_path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Failed to create base path {self.base_path}: {e}")
            raise

    def save_json(self, data: Dict[str, Any], filename: str, subdir: Optional[str] = None) -> bool:
        """
        Save JSON data to a local file.
        
        Args:
            data: Dictionary to save as JSON
            filename: Name of the file
            subdir: Optional subdirectory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.base_path
            if subdir:
                file_path = file_path / subdir
                file_path.mkdir(parents=True, exist_ok=True)
            
            file_path = file_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Successfully saved JSON to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save JSON to {filename}: {e}")
            return False

    def load_json(self, filename: str, subdir: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Load JSON data from a local file.
        
        Args:
            filename: Name of the file
            subdir: Optional subdirectory
            
        Returns:
            Dictionary if successful, None otherwise
        """
        try:
            file_path = self.base_path
            if subdir:
                file_path = file_path / subdir
            
            file_path = file_path / filename
            
            if not file_path.exists():
                logger.warning(f"File {file_path} does not exist")
                return None
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
                
        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error for {filename}: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to load JSON from {filename}: {e}")
            return None

    def save_text(self, text: str, filename: str, subdir: Optional[str] = None) -> bool:
        """
        Save text data to a local file.
        
        Args:
            text: Text content to save
            filename: Name of the file
            subdir: Optional subdirectory
            
        Returns:
            True if successful, False otherwise
        """
        try:
            file_path = self.base_path
            if subdir:
                file_path = file_path / subdir
                file_path.mkdir(parents=True, exist_ok=True)
            
            file_path = file_path / filename
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(text)
            
            logger.info(f"Successfully saved text to {file_path}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save text to {filename}: {e}")
            return False

    def list_files(self, pattern: str = "*", subdir: Optional[str] = None) -> list:
        """
        List files matching a pattern.
        
        Args:
            pattern: File pattern (e.g., "*.json")
            subdir: Optional subdirectory
            
        Returns:
            List of matching file paths
        """
        try:
            search_path = self.base_path
            if subdir:
                search_path = search_path / subdir
            
            if not search_path.exists():
                return []
            
            return list(search_path.glob(pattern))
            
        except Exception as e:
            logger.error(f"Failed to list files with pattern {pattern}: {e}")
            return []