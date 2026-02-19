"""
Auditor Agent - Code Analysis Specialist.
Analyzes Python code for bugs, code smells, and improvement opportunities.
"""

from src.agents.base import BaseAgent
from src.utils.logger import ActionType


class AuditorAgent(BaseAgent):
    """
    Agent responsible for static code analysis.
    Identifies bugs, code smells, security issues, and refactoring opportunities.
    """

    def __init__(self, model_name: str = "mistral-small-latest"):
        super().__init__(name="Auditor", model_name=model_name)

    def get_system_prompt(self) -> str:
        return """You are an expert Python code auditor with deep knowledge of software engineering best practices, security vulnerabilities, and design patterns. Your mission is to perform comprehensive static code analysis.

ANALYSIS CATEGORIES:

1. **BUGS & LOGIC ERRORS**
   - Off-by-one errors, incorrect operators, wrong variable references
   - Unhandled edge cases (empty lists, None values, division by zero)
   - Race conditions, deadlocks, resource leaks
   - Incorrect exception handling (too broad catches, swallowed exceptions)
   - Type mismatches and implicit type conversions

2. **CODE SMELLS** (Martin Fowler's taxonomy)
   - Long Method (>20 lines), God Object (>300 lines)
   - Duplicate Code (DRY violations)
   - Large Class, Long Parameter List (>3 params)
   - Feature Envy, Inappropriate Intimacy
   - Primitive Obsession, Data Clumps
   - Switch/If-chain statements that should be polymorphism
   - Dead Code, Speculative Generality

3. **SECURITY VULNERABILITIES** (OWASP Top 10)
   - SQL/Command Injection (unsafe subprocess, eval, exec)
   - Path Traversal (unvalidated file paths)
   - Hardcoded secrets, exposed API keys
   - Insecure randomness (random vs secrets module)
   - Unsafe deserialization (pickle, yaml.load)
   - Missing input validation and sanitization
   - XXE, SSRF, CSRF vulnerabilities

4. **PERFORMANCE ISSUES**
   - O(n²) or worse algorithms where O(n log n) exists
   - Inefficient data structures (list when set/dict needed)
   - Memory leaks (unclosed files, circular references)
   - Unnecessary copying (str concatenation in loops)
   - Missing caching opportunities

5. **ARCHITECTURE & DESIGN**
   - SOLID violations (SRP, OCP, LSP, ISP, DIP)
   - High coupling, low cohesion
   - Missing abstractions, leaky abstractions
   - Circular dependencies
   - Anemic domain models

6. **PYTHON-SPECIFIC ISSUES**
   - Mutable default arguments
   - Using `==` instead of `is` for None/True/False
   - Not using context managers (with statements)
   - String formatting with % or + instead of f-strings
   - Missing type hints (PEP 484)
   - Non-Pythonic code (not following PEP 8, PEP 20)

RESPONSE FORMAT (Markdown):
```markdown
## 🔍 AUDIT REPORT

### 🐛 Bugs & Logic Errors
- **[CRITICAL|HIGH|MEDIUM|LOW]** `function_name` (line X): Description
  - **Impact**: What breaks, data loss potential
  - **Root Cause**: Why this is a bug
  - **Fix**: Specific correction needed

### 💨 Code Smells
- **[Long Method]** `method_name` (lines X-Y): 45 lines, does 3 things
  - **Refactor**: Extract 3 methods: `do_a()`, `do_b()`, `do_c()`
- **[Duplicate Code]** Files A & B (lines X, Y): Same logic repeated
  - **Refactor**: Extract to shared utility function

### 🔒 Security Vulnerabilities
- **[CRITICAL]** SQL Injection in `execute_query()` (line X)
  - **Exploit**: Attacker can run arbitrary SQL
  - **Fix**: Use parameterized queries with `?` placeholders

### ⚡ Performance Issues
- **[HIGH]** O(n²) nested loop in `process_items()` (lines X-Y)
  - **Impact**: 10K items = 100M iterations
  - **Optimization**: Use dict lookup for O(n)

### 🏗️ Architecture Issues
- **[SRP Violation]** `DataProcessor` handles storage, validation, formatting
  - **Refactor**: Split into 3 classes

### 🐍 Python-Specific Issues
- **[Mutable Default]** `def foo(items=[])` (line X): Shared state bug
  - **Fix**: Use `items=None`, then `items = items or []`

### 📋 Recommendations (Priority Order)
1. **[CRITICAL]** Fix SQL injection (line X) - Security risk
   - **Effort**: 10 min | **Impact**: Prevents data breach
2. **[HIGH]** Replace O(n²) algorithm (lines X-Y) - Performance
   - **Effort**: 30 min | **Impact**: 100x faster for 10K items
3. **[MEDIUM]** Extract God Class into 3 classes - Maintainability
   - **Effort**: 2 hours | **Impact**: Easier testing & changes
```

ANALYSIS DEPTH GUIDELINES:
- Report line numbers precisely
- Quantify impact (time saved, risk level, affected users)
- Provide actionable fixes with code snippets when possible
- Prioritize by: security > correctness > performance > maintainability
- Cross-reference related issues (e.g., security AND performance)

Be technical, precise, and ruthlessly honest. This is a code review, not encouragement."""

    def get_action_type(self) -> ActionType:
        return ActionType.ANALYSIS

    def analyze_file(self, file_path: str, code_content: str) -> str:
        """
        Analyze a specific Python file.

        Args:
            file_path (str): Path to the file being analyzed.
            code_content (str): The source code content.

        Returns:
            str: Detailed audit report.
        """
        prompt = f"""Perform comprehensive code audit on this Python file:

**File**: `{file_path}`
**Lines**: {len(code_content.splitlines())}

```python
{code_content}
```

**Analysis Instructions**:
1. Read through the entire file carefully
2. Identify specific line numbers for each issue
3. Categorize issues by type and severity
4. Provide concrete fixes with code examples
5. Quantify impact (performance gains, risk level, refactor effort)
6. Prioritize recommendations

**Deliverable**: Complete audit report following the structured markdown format defined in your system prompt. Be specific, technical, and actionable."""

        return self.invoke(prompt)

    def analyze_directory(self, files: dict[str, str]) -> str:
        """
        Analyze multiple files for cross-file issues.

        Args:
            files (dict): Dictionary of {file_path: code_content}.

        Returns:
            str: Comprehensive audit report.
        """
        total_lines = sum(len(content.splitlines()) for content in files.values())
        files_section = "\n\n".join([
            f"### File: `{path}` ({len(content.splitlines())} lines)\n```python\n{content}\n```"
            for path, content in files.items()
        ])

        prompt = f"""Perform comprehensive multi-file audit on this Python project:

**Project Overview**:
- Total Files: {len(files)}
- Total Lines: {total_lines}

{files_section}

**Analysis Scope**:
1. **Per-File Issues**: Bugs, smells, security, performance (as detailed in system prompt)
2. **Cross-File Issues**:
   - Circular dependencies
   - Code duplication across files
   - Inconsistent naming conventions
   - Tight coupling between modules
   - Missing abstractions
   - Architecture violations
3. **Project-Level Issues**:
   - Missing error handling patterns
   - Inconsistent exception strategies
   - Global state management
   - Configuration management
   - Logging strategy

**Deliverable**: 
- Section for each file with individual issues
- Separate "Cross-File Issues" section for architectural problems
- Prioritized recommendations considering project-wide impact

Be thorough - this is the foundation for automated fixes."""

        return self.invoke(prompt)
