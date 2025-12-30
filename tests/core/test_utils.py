import unittest
import logging
import os
import shutil
from pathlib import Path
from claude_skill.core.utils import get_logger, get_project_root, ensure_dir, VERSION

class TestUtils(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, "0.1.0")

    def test_get_logger(self):
        logger = get_logger("test_logger")
        self.assertIsInstance(logger, logging.Logger)
        self.assertEqual(logger.name, "test_logger")
        self.assertTrue(len(logger.handlers) > 0)

    def test_logger_level_env(self):
        # Test that LOG_LEVEL env var is respected
        os.environ["LOG_LEVEL"] = "DEBUG"
        # Clean up previous logger if it exists to force reconfiguration
        if "debug_logger" in logging.Logger.manager.loggerDict:
            del logging.Logger.manager.loggerDict["debug_logger"]
        
        logger = get_logger("debug_logger")
        self.assertEqual(logger.level, logging.DEBUG)

    def test_get_project_root(self):
        root = get_project_root()
        self.assertIsInstance(root, Path)
        self.assertTrue(root.exists())
        # Check if a known file exists in root
        self.assertTrue((root / "Product Vision.md").exists())

    def test_ensure_dir(self):
        # Use a local test dir instead of tmp_path for simplicity with unittest
        test_dir = Path("test_temp_dir") / "sub"
        if test_dir.exists():
            shutil.rmtree("test_temp_dir")
            
        ensure_dir(test_dir)
        self.assertTrue(test_dir.exists())
        self.assertTrue(test_dir.is_dir())
        
        # Test existing dir
        ensure_dir(test_dir) # Should not raise error
        self.assertTrue(test_dir.exists())
        
        # Cleanup
        shutil.rmtree("test_temp_dir")

if __name__ == "__main__":
    unittest.main()
