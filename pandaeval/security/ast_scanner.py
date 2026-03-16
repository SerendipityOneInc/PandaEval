"""AST-based security scanner for Python files.

Detects dangerous patterns that regex cannot catch:
  - eval/exec with dynamic arguments
  - __import__ calls
  - getattr on builtins
  - subprocess/os.system with dynamic input
  - compile() + exec() chains

Uses only stdlib ast module — zero external dependencies.
"""

import ast
from pathlib import Path


# Functions considered dangerous when called with non-literal arguments
_DANGEROUS_CALLS = {
    "eval", "exec", "compile",
    "getattr", "setattr", "delattr",
}

# Functions that are always dangerous regardless of argument type
_ALWAYS_DANGEROUS_CALLS = {
    "__import__",
}

# Modules whose function calls warrant scrutiny
_DANGEROUS_MODULE_CALLS = {
    ("os", "system"),
    ("os", "popen"),
    ("os", "exec"),
    ("os", "execvp"),
    ("os", "execve"),
    ("subprocess", "run"),
    ("subprocess", "call"),
    ("subprocess", "Popen"),
    ("subprocess", "check_output"),
    ("subprocess", "check_call"),
    ("shutil", "rmtree"),
}


class _ASTVisitor(ast.NodeVisitor):
    """Walk Python AST to find dangerous patterns."""

    def __init__(self):
        self.findings = []
        # Maps local alias → real module name (e.g., {"x": "os", "sp": "subprocess"})
        self._module_aliases = {}
        # Maps local name → (module, func) for from-imports (e.g., {"run": ("subprocess", "run")})
        self._from_imports = {}

    def _is_literal(self, node):
        """Check if a node is a safe literal value."""
        if isinstance(node, ast.Constant):
            return True
        if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            return all(self._is_literal(e) for e in node.elts)
        if isinstance(node, ast.Dict):
            return all(
                self._is_literal(k) and self._is_literal(v)
                for k, v in zip(node.keys, node.values)
                if k is not None
            )
        return False

    def _get_call_name(self, node):
        """Extract the function name from a Call node."""
        if isinstance(node.func, ast.Name):
            return node.func.id
        if isinstance(node.func, ast.Attribute):
            return node.func.attr
        return None

    def _get_full_call_name(self, node):
        """Extract module.func from a Call node, resolving aliases."""
        if isinstance(node.func, ast.Attribute):
            if isinstance(node.func.value, ast.Name):
                local_name = node.func.value.id
                real_module = self._module_aliases.get(local_name, local_name)
                return (real_module, node.func.attr)
        return None

    def _resolve_from_import(self, name):
        """Resolve a bare function name to (module, func) via from-import aliases."""
        return self._from_imports.get(name)

    def _has_dynamic_args(self, node):
        """Check if any argument to a Call node is non-literal."""
        return any(not self._is_literal(arg) for arg in node.args)

    def visit_Call(self, node):
        name = self._get_call_name(node)

        # Check always-dangerous calls: __import__(...)
        if name in _ALWAYS_DANGEROUS_CALLS:
            self.findings.append({
                "category": "ast_dangerous_call",
                "pattern": f"{name}() call",
                "line": node.lineno,
            })

        # Check bare dangerous calls: eval(...), exec(...)
        if name in _DANGEROUS_CALLS:
            if self._has_dynamic_args(node) or not node.args:
                self.findings.append({
                    "category": "ast_dangerous_call",
                    "pattern": f"{name}() with dynamic argument",
                    "line": node.lineno,
                })

        # Check bare calls that are from-imported dangerous functions
        # e.g., `from subprocess import run; run(cmd)`
        if name and isinstance(node.func, ast.Name):
            resolved = self._resolve_from_import(name)
            if resolved and resolved in _DANGEROUS_MODULE_CALLS:
                if self._has_dynamic_args(node):
                    self.findings.append({
                        "category": "ast_dangerous_call",
                        "pattern": f"{resolved[0]}.{resolved[1]}() with dynamic argument (from-import)",
                        "line": node.lineno,
                    })

        # Check module.func calls: os.system(...), subprocess.run(...)
        # Resolves aliases: import os as x; x.system(cmd) → ("os", "system")
        full_name = self._get_full_call_name(node)
        if full_name in _DANGEROUS_MODULE_CALLS:
            if self._has_dynamic_args(node):
                self.findings.append({
                    "category": "ast_dangerous_call",
                    "pattern": f"{full_name[0]}.{full_name[1]}() with dynamic argument",
                    "line": node.lineno,
                })

        self.generic_visit(node)

    def visit_Import(self, node):
        """Track import aliases and flag dangerous modules."""
        for alias in node.names:
            # Track alias: import os as x → _module_aliases["x"] = "os"
            local_name = alias.asname if alias.asname else alias.name
            self._module_aliases[local_name] = alias.name

            if alias.name in ("ctypes", "code", "codeop"):
                self.findings.append({
                    "category": "ast_suspicious_import",
                    "pattern": f"import {alias.name}",
                    "line": node.lineno,
                })
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """Track from-import aliases and flag dangerous modules."""
        if node.module in ("ctypes", "code", "codeop"):
            self.findings.append({
                "category": "ast_suspicious_import",
                "pattern": f"from {node.module} import ...",
                "line": node.lineno,
            })

        # Track from-imports: from subprocess import run as r → _from_imports["r"] = ("subprocess", "run")
        if node.module:
            for alias in (node.names or []):
                local_name = alias.asname if alias.asname else alias.name
                self._from_imports[local_name] = (node.module, alias.name)

        self.generic_visit(node)


def scan_python_file(source, filename="<unknown>"):
    """Scan a single Python source string for dangerous AST patterns.

    Args:
        source: Python source code string.
        filename: For error reporting.

    Returns:
        list of finding dicts with category, pattern, line, file keys.
    """
    try:
        tree = ast.parse(source, filename=filename)
    except SyntaxError:
        return []  # Not valid Python — skip

    visitor = _ASTVisitor()
    visitor.visit(tree)
    for f in visitor.findings:
        f["file"] = filename
    return visitor.findings


def ast_scan(skill_dir):
    """Scan all Python files in a skill directory using AST analysis.

    Args:
        skill_dir: Path to skill directory.

    Returns:
        dict with keys:
            findings: list of finding dicts
            files_scanned: number of .py files scanned
            notes: list of human-readable notes
    """
    base = Path(skill_dir)
    all_findings = []
    files_scanned = 0

    py_files = list(base.glob("**/*.py"))
    for py_file in py_files:
        if py_file.stat().st_size > 500_000:
            continue
        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue

        files_scanned += 1
        findings = scan_python_file(source, filename=str(py_file.relative_to(base)))
        all_findings.extend(findings)

    notes = [f"[ast:{f['category']}] {f['pattern']} at {f['file']}:{f['line']}" for f in all_findings]
    if not all_findings and files_scanned > 0:
        notes.append("AST scan: no dangerous patterns detected")
    elif files_scanned == 0:
        notes.append("AST scan: no Python files to scan")

    return {
        "findings": all_findings,
        "files_scanned": files_scanned,
        "notes": notes,
    }
