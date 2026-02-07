"""
Plugin Testing Framework - Test Runner

Test runner for executing plugin tests in isolation with validation.
"""

import os
import sys
import unittest
import importlib
import ast
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
import logging

from app.plugins.manager import PluginManager
from .mocks import MockFlaskApp
from .helpers import verify_plugin_structure

logger = logging.getLogger(__name__)


class PluginTestRunner:
    """
    Run plugin tests in isolation.

    Features:
    - Discover and run all tests for a plugin
    - Validate plugin structure and code
    - Generate test reports
    - Isolated test execution
    """

    def __init__(self, plugin_dir: Optional[str] = None):
        """
        Initialize plugin test runner.

        Args:
            plugin_dir: Path to plugins directory (optional)
        """
        self.plugin_dir = plugin_dir or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 'installed'
        )
        self.results = {}

    def run_plugin_tests(
        self,
        plugin_name: str,
        test_pattern: str = 'test_*.py',
        verbosity: int = 2
    ) -> unittest.TestResult:
        """
        Discover and run all tests for a plugin.

        Args:
            plugin_name: Name of plugin to test
            test_pattern: Pattern for test file discovery
            verbosity: Test output verbosity (0-2)

        Returns:
            unittest.TestResult with test results

        Raises:
            ValueError: If plugin directory doesn't exist
        """
        plugin_path = os.path.join(self.plugin_dir, plugin_name)

        if not os.path.exists(plugin_path):
            raise ValueError(f"Plugin directory not found: {plugin_path}")

        # Add plugin directory to sys.path temporarily
        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        try:
            # Discover tests in plugin directory
            loader = unittest.TestLoader()
            start_dir = plugin_path
            suite = loader.discover(start_dir, pattern=test_pattern)

            # Run tests
            runner = unittest.TextTestRunner(verbosity=verbosity)
            result = runner.run(suite)

            # Store results
            self.results[plugin_name] = {
                'tests_run': result.testsRun,
                'failures': len(result.failures),
                'errors': len(result.errors),
                'skipped': len(result.skipped),
                'success': result.wasSuccessful()
            }

            return result

        finally:
            # Remove from sys.path
            if self.plugin_dir in sys.path:
                sys.path.remove(self.plugin_dir)

    def validate_plugin(self, plugin_name: str) -> Tuple[bool, List[str]]:
        """
        Run validation checks on a plugin.

        Validates:
        - Directory structure
        - Required files exist
        - Python syntax
        - Plugin class exists
        - Metadata completeness
        - No security issues (basic checks)

        Args:
            plugin_name: Name of plugin to validate

        Returns:
            Tuple of (is_valid, list_of_issues)
        """
        issues = []
        plugin_path = os.path.join(self.plugin_dir, plugin_name)

        # Check structure
        is_valid, error = verify_plugin_structure(plugin_path)
        if not is_valid:
            issues.append(f"Structure error: {error}")
            return False, issues

        # Check for plugin.py
        plugin_file = os.path.join(plugin_path, 'plugin.py')
        if not os.path.exists(plugin_file):
            issues.append("Missing plugin.py file")
            return False, issues

        # Validate Python syntax
        try:
            with open(plugin_file, 'r') as f:
                code = f.read()
                ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error in plugin.py: {e}")
            return False, issues

        # Try to load plugin
        try:
            if self.plugin_dir not in sys.path:
                sys.path.insert(0, self.plugin_dir)

            plugin_module = importlib.import_module(plugin_name)

            # Check for BasePlugin subclass
            from app.plugins.base import BasePlugin
            plugin_class = None
            for attr_name in dir(plugin_module):
                attr = getattr(plugin_module, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BasePlugin) and
                    attr is not BasePlugin):
                    plugin_class = attr
                    break

            if not plugin_class:
                issues.append("No BasePlugin subclass found")
                return False, issues

            # Instantiate and check metadata
            plugin = plugin_class()
            metadata = plugin.get_metadata()

            required_fields = ['name', 'version', 'author', 'description']
            for field in required_fields:
                if field not in metadata or not metadata[field]:
                    issues.append(f"Metadata missing required field: {field}")

            # Validate version format
            version = metadata.get('version', '')
            if version and not self._is_valid_version(version):
                issues.append(f"Invalid version format: {version}")

        except ImportError as e:
            issues.append(f"Failed to import plugin: {e}")
            return False, issues
        except Exception as e:
            issues.append(f"Failed to validate plugin: {e}")
            return False, issues
        finally:
            if self.plugin_dir in sys.path:
                sys.path.remove(self.plugin_dir)

        # Security checks
        security_issues = self._check_security(plugin_file)
        issues.extend(security_issues)

        # Check for manifest.json (optional but recommended)
        manifest_file = os.path.join(plugin_path, 'manifest.json')
        if not os.path.exists(manifest_file):
            issues.append("Warning: No manifest.json file (recommended)")

        is_valid = len([i for i in issues if not i.startswith('Warning:')]) == 0
        return is_valid, issues

    def _check_security(self, plugin_file: str) -> List[str]:
        """
        Basic security checks on plugin code.

        Args:
            plugin_file: Path to plugin.py

        Returns:
            List of security issues found
        """
        issues = []

        try:
            with open(plugin_file, 'r') as f:
                code = f.read()

            # Check for dangerous functions
            dangerous_patterns = [
                ('eval(', 'Use of eval() is dangerous'),
                ('exec(', 'Use of exec() is dangerous'),
                ('__import__(', 'Dynamic imports should be avoided'),
                ('os.system(', 'Use of os.system() is dangerous'),
                ('subprocess.', 'Use of subprocess should be carefully reviewed'),
                ('open(', 'File operations should be limited to allowed paths'),
            ]

            for pattern, message in dangerous_patterns:
                if pattern in code:
                    issues.append(f"Security warning: {message}")

        except Exception as e:
            issues.append(f"Security check failed: {e}")

        return issues

    def _is_valid_version(self, version: str) -> bool:
        """
        Validate semantic version format.

        Args:
            version: Version string

        Returns:
            True if valid
        """
        import re
        pattern = r'^\d+\.\d+\.\d+(-[a-zA-Z0-9]+)?$'
        return bool(re.match(pattern, version))

    def generate_report(self, plugin_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Generate test report.

        Args:
            plugin_name: Optional specific plugin name

        Returns:
            Report dict with test results
        """
        if plugin_name:
            if plugin_name not in self.results:
                return {'error': f"No results for plugin '{plugin_name}'"}
            return {plugin_name: self.results[plugin_name]}

        return self.results.copy()

    def run_single_test(
        self,
        plugin_name: str,
        test_class: str,
        test_method: Optional[str] = None,
        verbosity: int = 2
    ) -> unittest.TestResult:
        """
        Run a specific test class or method.

        Args:
            plugin_name: Name of plugin
            test_class: Test class name (e.g., 'test_plugin.TestMyPlugin')
            test_method: Optional specific test method
            verbosity: Output verbosity

        Returns:
            unittest.TestResult
        """
        plugin_path = os.path.join(self.plugin_dir, plugin_name)

        if not os.path.exists(plugin_path):
            raise ValueError(f"Plugin directory not found: {plugin_path}")

        if self.plugin_dir not in sys.path:
            sys.path.insert(0, self.plugin_dir)

        try:
            # Build test suite
            loader = unittest.TestLoader()

            if test_method:
                # Load specific test method
                suite = loader.loadTestsFromName(
                    f"{plugin_name}.{test_class}.{test_method}"
                )
            else:
                # Load entire test class
                suite = loader.loadTestsFromName(f"{plugin_name}.{test_class}")

            # Run tests
            runner = unittest.TextTestRunner(verbosity=verbosity)
            return runner.run(suite)

        finally:
            if self.plugin_dir in sys.path:
                sys.path.remove(self.plugin_dir)

    def validate_all_plugins(self) -> Dict[str, Tuple[bool, List[str]]]:
        """
        Validate all plugins in plugin directory.

        Returns:
            Dict mapping plugin names to (is_valid, issues) tuples
        """
        results = {}

        if not os.path.exists(self.plugin_dir):
            logger.warning(f"Plugin directory not found: {self.plugin_dir}")
            return results

        for item in os.listdir(self.plugin_dir):
            plugin_path = os.path.join(self.plugin_dir, item)
            if os.path.isdir(plugin_path) and not item.startswith('_'):
                # Check if it's a plugin (has __init__.py)
                if os.path.exists(os.path.join(plugin_path, '__init__.py')):
                    is_valid, issues = self.validate_plugin(item)
                    results[item] = (is_valid, issues)

        return results

    def get_test_coverage(self, plugin_name: str) -> Dict[str, Any]:
        """
        Get test coverage information for a plugin.

        Args:
            plugin_name: Name of plugin

        Returns:
            Coverage information dict
        """
        plugin_path = os.path.join(self.plugin_dir, plugin_name)

        if not os.path.exists(plugin_path):
            return {'error': 'Plugin not found'}

        # Count test files
        test_files = []
        for root, dirs, files in os.walk(plugin_path):
            for file in files:
                if file.startswith('test_') and file.endswith('.py'):
                    test_files.append(file)

        # Count source files
        source_files = []
        for root, dirs, files in os.walk(plugin_path):
            for file in files:
                if file.endswith('.py') and not file.startswith('test_'):
                    source_files.append(file)

        return {
            'plugin_name': plugin_name,
            'test_files': len(test_files),
            'source_files': len(source_files),
            'test_file_list': test_files,
            'has_tests': len(test_files) > 0
        }


class PluginTestValidator:
    """
    Validates plugin test files and test structure.
    """

    def __init__(self):
        """Initialize validator."""
        pass

    def validate_test_file(self, test_file_path: str) -> Tuple[bool, List[str]]:
        """
        Validate a test file.

        Args:
            test_file_path: Path to test file

        Returns:
            Tuple of (is_valid, issues)
        """
        issues = []

        if not os.path.exists(test_file_path):
            return False, ["Test file not found"]

        # Check Python syntax
        try:
            with open(test_file_path, 'r') as f:
                code = f.read()
                ast.parse(code)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            return False, issues

        # Check for test classes/methods
        try:
            tree = ast.parse(code)
            has_test_class = False
            has_test_method = False

            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    # Check if it's a test class (inherits from TestCase or has Test in name)
                    if 'Test' in node.name:
                        has_test_class = True
                        # Check for test methods
                        for item in node.body:
                            if isinstance(item, ast.FunctionDef) and item.name.startswith('test_'):
                                has_test_method = True
                                break

            if not has_test_class:
                issues.append("No test class found")
            if not has_test_method:
                issues.append("No test methods found")

        except Exception as e:
            issues.append(f"Failed to analyze test structure: {e}")

        is_valid = len(issues) == 0
        return is_valid, issues

    def check_test_imports(self, test_file_path: str) -> List[str]:
        """
        Check if test file has proper imports.

        Args:
            test_file_path: Path to test file

        Returns:
            List of missing imports
        """
        missing = []

        try:
            with open(test_file_path, 'r') as f:
                code = f.read()

            required_imports = ['unittest', 'PluginTestCase']
            for imp in required_imports:
                if imp not in code:
                    missing.append(imp)

        except Exception:
            pass

        return missing
