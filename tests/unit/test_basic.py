"""
Basic unit tests to verify test infrastructure works.

These simple tests validate that the test framework is properly configured
and can run successfully.
"""

import pytest
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))


class TestBasicInfrastructure:
    """Basic infrastructure tests."""
    
    @pytest.mark.unit
    def test_python_version(self):
        """Test Python version is supported."""
        assert sys.version_info >= (3, 8), "Python 3.8+ required"
    
    @pytest.mark.unit
    def test_imports_work(self):
        """Test that basic imports work."""
        try:
            import unittest.mock
            import asyncio
            import datetime
            import pathlib
            assert True
        except ImportError as e:
            pytest.fail(f"Basic import failed: {e}")
    
    @pytest.mark.unit
    def test_pytest_markers(self):
        """Test that pytest markers are working."""
        # This test itself uses the unit marker
        assert True
    
    @pytest.mark.unit
    def test_basic_math(self):
        """Test basic functionality."""
        assert 2 + 2 == 4
        assert 10 / 2 == 5.0
        assert "hello" + " world" == "hello world"
    
    @pytest.mark.unit
    def test_mock_functionality(self):
        """Test that mocking works."""
        from unittest.mock import Mock
        
        mock_obj = Mock()
        mock_obj.test_method.return_value = "mocked"
        
        result = mock_obj.test_method()
        assert result == "mocked"
        mock_obj.test_method.assert_called_once()


class TestProjectStructure:
    """Test project structure is correct."""
    
    @pytest.mark.unit
    def test_source_directory_exists(self):
        """Test that source directory exists."""
        project_root = Path(__file__).parent.parent.parent
        src_dir = project_root / "src" / "tqqq_analysis"
        
        assert src_dir.exists(), f"Source directory not found: {src_dir}"
        assert (src_dir / "__init__.py").exists(), "Source package __init__.py missing"
    
    @pytest.mark.unit
    def test_test_directory_structure(self):
        """Test that test directory structure is correct."""
        tests_dir = Path(__file__).parent.parent
        
        assert tests_dir.name == "tests"
        assert (tests_dir / "__init__.py").exists()
        assert (tests_dir / "conftest.py").exists()
        assert (tests_dir / "unit").exists()
        assert (tests_dir / "integration").exists()
        assert (tests_dir / "fixtures").exists()


if __name__ == "__main__":
    pytest.main([__file__])