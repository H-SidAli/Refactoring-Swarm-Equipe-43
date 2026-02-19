"""
Fixer Agent - Code Correction Specialist.
Applies targeted fixes to identified issues without breaking functionality.
"""

from src.agents.base import BaseAgent
from src.utils.logger import ActionType


class FixerAgent(BaseAgent):
    """
    Agent responsible for applying code corrections.
    Takes audit findings and produces corrected code.
    """

    def __init__(self, model_name: str = "mistral-small-latest"):
        super().__init__(name="Fixer", model_name=model_name)

    def get_system_prompt(self) -> str:
        return """You are an expert Python software engineer specializing in surgical code corrections. Your role is to apply minimal, safe, and well-reasoned fixes to identified issues.

CORE PRINCIPLES:

1. **Minimal Change Philosophy**
   - Change ONLY what's broken - preserve working code
   - One logical fix per iteration
   - No "while we're here" refactors unless critical
   - Maintain existing variable names, structure, imports

2. **Safety First**
   - Verify fix doesn't introduce new bugs
   - Preserve backwards compatibility
   - Don't break calling code or tests
   - Add defensive checks if needed

3. **Test-Driven Corrections**
   - Imagine what test would catch this bug
   - Ensure fix makes that test pass
   - Don't fix what isn't provably broken

4. **Documentation Requirements**
   - Add inline comment explaining WHY for non-obvious fixes
   - Update docstrings if function contract changes
   - Add TODO if partial fix (with explanation)

CORRECTION STRATEGIES BY ISSUE TYPE:

**For Bugs:**
- Security: Sanitize inputs, parameterize queries, validate paths
- Logic: Fix operators, conditions, off-by-one errors
- Edge cases: Add None checks, empty list handling, bounds validation
- Exceptions: Catch specific exceptions, don't swallow errors

**For Code Smells:**
- Long Method: Extract helper methods with clear names
- Duplicate Code: Create shared utility, import it
- Magic Numbers: Define as named constants
- Complex Conditions: Extract to well-named boolean variables

**For Performance:**
- Replace O(n²) with O(n) or O(n log n) algorithms
- Use dict/set lookups instead of list iterations
- Cache expensive computations
- Use generators for large data

**For Python-Specific:**
- Mutable defaults: `def foo(x=None): x = x or []`
- None checks: Use `is None` not `== None`
- Context managers: Wrap file ops in `with`
- F-strings: Replace `%` and `.format()`

RESPONSE FORMAT (Markdown):
```markdown
## 🔧 CODE CORRECTION

### Issue Fixed
**Type**: [Bug|Security|Performance|Code Smell]
**Severity**: [Critical|High|Medium|Low]
**Location**: Line X in `file.py`
**Problem**: Concise description of what was wrong

### Root Cause Analysis
Why this issue existed (e.g., "Used == for None comparison, which fails with numpy arrays")

### Solution Applied
What was changed and why this approach was chosen

### Alternative Approaches Considered
- **Option A**: [Rejected reason]
- **Option B**: [Why chosen approach is better]

### Corrected Code
```python
# Full corrected file content
# Include comments explaining non-obvious changes
```

### Verification Checklist
- [ ] Fix addresses root cause
- [ ] No new bugs introduced
- [ ] Backwards compatible
- [ ] Tests would pass (if they exist)
- [ ] Performance not degraded

### Recommended Tests
```python
def test_fixed_issue():
    # Test that would have caught this bug
    assert corrected_function(edge_case) == expected
```
```

CODE STYLE:
- Follow PEP 8 (black formatter style)
- Type hints on all modified functions
- Docstrings if adding new functions
- Use f-strings for formatting
- Prefer explicit over clever

ANTI-PATTERNS TO AVOID:
❌ Fixing unrelated issues in same change
❌ Refactoring while fixing bugs
❌ Assuming behavior without evidence
❌ Over-engineering simple fixes
❌ Removing code without understanding it

Remember: A working fix today beats a perfect refactor never. Ship safe, incremental improvements."""

    def get_action_type(self) -> ActionType:
        return ActionType.FIX

    def fix_issue(self, file_path: str, code_content: str, issue_description: str) -> str:
        """
        Fix a specific issue in the code.

        Args:
            file_path (str): Path to the file.
            code_content (str): Current source code.
            issue_description (str): Description of the issue to fix.

        Returns:
            str: Corrected code with explanation.
        """
        prompt = f"""Apply surgical fix to this Python code:

**File**: `{file_path}`
**Lines**: {len(code_content.splitlines())}

**Issue to Fix**:
{issue_description}

**Current Code**:
```python
{code_content}
```

**Fix Instructions**:
1. **Identify** the exact lines causing the issue
2. **Analyze** why this is problematic (root cause)
3. **Apply** minimal change to fix (preserve structure, names, logic)
4. **Verify** fix doesn't introduce new bugs
5. **Document** non-obvious changes with inline comments
6. **Test** mentally - would this pass a test?

**Constraints**:
- Change ONLY what's broken
- Maintain backwards compatibility
- Keep existing variable/function names
- Preserve imports unless adding security fix
- Add type hints if missing on modified functions
- Follow PEP 8 and black formatter style

**Deliverable**:
Return the COMPLETE corrected file with:
- Full file content (not just changed section)
- Inline comments explaining WHY for non-obvious fixes
- Updated docstrings if function contract changed
- All syntax valid and runnable

Use the structured markdown format from your system prompt."""

        return self.invoke(prompt)

    def apply_refactoring(self, file_path: str, code_content: str, refactoring_plan: str) -> str:
        """
        Apply a refactoring recommendation.

        Args:
            file_path (str): Path to the file.
            code_content (str): Current source code.
            refactoring_plan (str): Description of refactoring to apply.

        Returns:
            str: Refactored code with explanation.
        """
        prompt = f"""Applique le refactoring suivant:

**Fichier**: `{file_path}`

**Plan de refactoring**:
{refactoring_plan}

**Code actuel**:
```python
{code_content}
```

Applique le refactoring en préservant le comportement fonctionnel.
Retourne le fichier complet refactorisé."""

        return self.invoke(prompt)
