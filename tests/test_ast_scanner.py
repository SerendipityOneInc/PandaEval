"""Tests for security.ast_scanner module."""

from pandaeval.security.ast_scanner import scan_python_file, ast_scan


class TestScanPythonFile:
    def test_clean_code(self):
        source = "x = 1 + 2\nprint(x)\n"
        findings = scan_python_file(source)
        assert findings == []

    def test_eval_with_dynamic_arg(self):
        source = "x = input()\neval(x)\n"
        findings = scan_python_file(source)
        assert len(findings) == 1
        assert findings[0]["category"] == "ast_dangerous_call"
        assert "eval()" in findings[0]["pattern"]

    def test_eval_with_literal_is_still_flagged_if_empty(self):
        """eval() with no args is suspicious."""
        source = "eval()\n"
        findings = scan_python_file(source)
        assert len(findings) == 1

    def test_eval_with_string_literal_not_flagged(self):
        source = 'eval("1 + 2")\n'
        findings = scan_python_file(source)
        assert findings == []

    def test_exec_with_dynamic_arg(self):
        source = "code = get_code()\nexec(code)\n"
        findings = scan_python_file(source)
        assert any("exec()" in f["pattern"] for f in findings)

    def test_dunder_import(self):
        source = "__import__('os').system('ls')\n"
        findings = scan_python_file(source)
        assert any("__import__" in f["pattern"] for f in findings)

    def test_getattr_dynamic(self):
        source = "getattr(__builtins__, name)()\n"
        findings = scan_python_file(source)
        assert any("getattr()" in f["pattern"] for f in findings)

    def test_os_system_dynamic(self):
        source = "import os\ncmd = input()\nos.system(cmd)\n"
        findings = scan_python_file(source)
        assert any("os.system()" in f["pattern"] for f in findings)

    def test_subprocess_run_dynamic(self):
        source = "import subprocess\nsubprocess.run(user_cmd, shell=True)\n"
        findings = scan_python_file(source)
        assert any("subprocess.run()" in f["pattern"] for f in findings)

    def test_shutil_rmtree_dynamic(self):
        source = "import shutil\nshutil.rmtree(path)\n"
        findings = scan_python_file(source)
        assert any("shutil.rmtree()" in f["pattern"] for f in findings)

    def test_compile_exec_chain(self):
        source = "code = compile(source, '<string>', 'exec')\nexec(code)\n"
        findings = scan_python_file(source)
        cats = [f["pattern"] for f in findings]
        assert any("compile()" in c for c in cats)
        assert any("exec()" in c for c in cats)

    def test_suspicious_import_ctypes(self):
        source = "import ctypes\n"
        findings = scan_python_file(source)
        assert any("import ctypes" in f["pattern"] for f in findings)

    def test_suspicious_from_import(self):
        source = "from code import InteractiveConsole\n"
        findings = scan_python_file(source)
        assert any("from code import" in f["pattern"] for f in findings)

    def test_normal_imports_not_flagged(self):
        source = "import os\nimport json\nimport subprocess\n"
        findings = scan_python_file(source)
        assert findings == []

    def test_syntax_error_returns_empty(self):
        source = "def broken(\n"
        findings = scan_python_file(source)
        assert findings == []

    def test_line_numbers(self):
        source = "x = 1\ny = 2\neval(z)\n"
        findings = scan_python_file(source)
        assert findings[0]["line"] == 3

    def test_hex_decode_eval(self):
        """The real bypass scenario: eval(bytes.fromhex(...).decode())"""
        source = 'eval(bytes.fromhex("726d").decode())\n'
        findings = scan_python_file(source)
        assert any("eval()" in f["pattern"] for f in findings)

    def test_chr_concatenation_exec(self):
        source = "exec(chr(114)+chr(109))\n"
        findings = scan_python_file(source)
        assert any("exec()" in f["pattern"] for f in findings)

    def test_os_popen(self):
        source = "import os\nos.popen(cmd)\n"
        findings = scan_python_file(source)
        assert any("os.popen()" in f["pattern"] for f in findings)


class TestAstScan:
    def test_scans_py_files(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("# Test")
        (tmp_path / "evil.py").write_text("eval(payload)\n")
        result = ast_scan(tmp_path)
        assert result["files_scanned"] == 1
        assert len(result["findings"]) == 1

    def test_scans_nested_py(self, tmp_path):
        scripts = tmp_path / "scripts"
        scripts.mkdir()
        (scripts / "run.py").write_text("exec(code)\n")
        result = ast_scan(tmp_path)
        assert result["files_scanned"] == 1
        assert len(result["findings"]) >= 1

    def test_no_python_files(self, tmp_path):
        (tmp_path / "SKILL.md").write_text("# Test")
        result = ast_scan(tmp_path)
        assert result["files_scanned"] == 0
        assert "no Python files" in result["notes"][0]

    def test_clean_python(self, tmp_path):
        (tmp_path / "helper.py").write_text("def add(a, b): return a + b\n")
        result = ast_scan(tmp_path)
        assert result["findings"] == []
        assert "no dangerous patterns" in result["notes"][0]

    def test_skips_large_files(self, tmp_path):
        large = tmp_path / "big.py"
        large.write_text("x = 1\n" * 200_000)
        result = ast_scan(tmp_path)
        assert result["files_scanned"] == 0

    def test_multiple_files(self, tmp_path):
        (tmp_path / "a.py").write_text("eval(x)\n")
        (tmp_path / "b.py").write_text("exec(y)\n")
        result = ast_scan(tmp_path)
        assert result["files_scanned"] == 2
        assert len(result["findings"]) == 2
