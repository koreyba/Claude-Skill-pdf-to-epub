import unittest
import logging
import os
import shutil
from pathlib import Path
from pdf_to_epub.core.utils import (
    get_logger, get_project_root, ensure_dir, 
    VERSION, DEFAULT_ENCODING, DEFAULT_CHUNK_SIZE, DEFAULT_OVERLAP
)

class TestUtils(unittest.TestCase):
    def test_constants(self):
        self.assertEqual(VERSION, "0.1.0")
        self.assertEqual(DEFAULT_ENCODING, "utf-8")
        self.assertEqual(DEFAULT_CHUNK_SIZE, 600)
        self.assertEqual(DEFAULT_OVERLAP, 100)

    def test_get_logger(self):
        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertTrue(len(logger.handlers) > 0)

    def test_get_logger_singleton_handlers(self):
        # Multiple calls should not add more handlers
        logger = get_logger("singleton_logger")
        initial_handlers_count = len(logger.handlers)
        
        logger_second_call = get_logger("singleton_logger")
        self.assertEqual(len(logger_second_call.handlers), initial_handlers_count)

    def test_logger_level_env(self):
        # Test that LOG_LEVEL env var is respected
        os.environ["LOG_LEVEL"] = "DEBUG"
        if "debug_logger" in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict["debug_logger"]
        
        logger = get_logger("debug_logger")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_logger_invalid_level_fallback(self):
        # Test fallback to INFO for invalid level
        os.environ["LOG_LEVEL"] = "INVALID_LEVEL_NAME"
        if "fallback_logger" in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict["fallback_logger"]
        
        logger = get_logger("fallback_logger")
        self.assertEqual(logger.level, logging.INFO)

    def test_get_project_root(self):
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())
        self.assertTrue((root / "Product Vision.md").exists())

    def test_ensure_dir(self):
        test_dir = Path("test_temp_dir_utils") / "sub"
        if test_dir.exists():
            shutil.rmtree("test_temp_dir_utils")
            
        ensure_dir(test_dir)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        
        ensure_dir(test_dir)
        self.assertTrue(test_dir.exists())
        
        if Path("test_temp_dir_utils").exists():
            shutil.rmtree("test_temp_dir_utils")

if __name__ == "__main__":
    unittest.main()
