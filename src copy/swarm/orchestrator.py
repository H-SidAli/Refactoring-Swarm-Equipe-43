"""
Refactoring Swarm Orchestrator - LangGraph-based workflow.
Coordinates agents through a structured refactoring pipeline.
"""

import os
import subprocess
import sys
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END

from src.agents import AuditorAgent, FixerAgent, GeneratorAgent
from src.utils.logger import log_experiment, ActionType


class SwarmState(TypedDict):
    """State shared across all nodes in the swarm."""
    target_dir: str
    files: dict[str, str]  # {file_path: content}
    audit_report: str
    fixes_applied: list[str]
    tests_generated: list[str]
    current_phase: str
    errors: list[str]
    tests_output: str


class RefactoringSwarm:
    """
    LangGraph-based orchestrator for the Refactoring Swarm.
    
    Pipeline:
    1. SCAN: Load target files
    2. AUDIT: Analyze code with AuditorAgent
    3. FIX: Apply corrections with FixerAgent
    4. GENERATE: Create tests with GeneratorAgent
    5. REPORT: Summarize results
    """

    def __init__(self, model_name: str = "mistral-small-latest"):
        """
        Initialize the swarm with all agents.

        Args:
            model_name (str): LLM model for all agents.
        """
        self.auditor = AuditorAgent(model_name=model_name)
        self.fixer = FixerAgent(model_name=model_name)
        self.generator = GeneratorAgent(model_name=model_name)
        self.graph = self._build_graph()

    def _build_graph(self) -> StateGraph:
        """Build the LangGraph workflow."""
        
        # Create graph with state schema
        workflow = StateGraph(SwarmState)

        # Add nodes
        workflow.add_node("scan", self._scan_node)
        workflow.add_node("audit", self._audit_node)
        workflow.add_node("fix", self._fix_node)
        workflow.add_node("generate", self._generate_node)
        workflow.add_node("report", self._report_node)

        # Define edges
        workflow.set_entry_point("scan")
        workflow.add_edge("scan", "audit")
        workflow.add_edge("audit", "fix")
        workflow.add_edge("fix", "generate")
        workflow.add_edge("generate", "report")
        workflow.add_edge("report", END)

        return workflow.compile()

    def _scan_node(self, state: SwarmState) -> SwarmState:
        """Load Python files from target directory."""
        target_dir = state["target_dir"]
        files = {}
        errors = []

        if not os.path.exists(target_dir):
            errors.append(f"Directory not found: {target_dir}")
            return {**state, "files": files, "errors": errors, "current_phase": "SCAN_FAILED"}

        for root, _, filenames in os.walk(target_dir):
            for filename in filenames:
                if filename.endswith(".py"):
                    file_path = os.path.join(root, filename)
                    try:
                        with open(file_path, "r", encoding="utf-8") as f:
                            files[file_path] = f.read()
                    except Exception as e:
                        errors.append(f"Failed to read {file_path}: {e}")

        print(f"📂 SCAN: Loaded {len(files)} Python file(s)")
        return {**state, "files": files, "errors": errors, "current_phase": "SCANNED"}

    def _audit_node(self, state: SwarmState) -> SwarmState:
        """Run code audit on all files."""
        if not state["files"]:
            return {**state, "audit_report": "No files to audit", "current_phase": "AUDIT_SKIPPED"}

        print(f"🔍 AUDIT: Analyzing {len(state['files'])} file(s)...")
        
        try:
            report = self.auditor.analyze_directory(state["files"])
            print("✅ AUDIT: Complete")
            return {**state, "audit_report": report, "current_phase": "AUDITED"}
        except Exception as e:
            error_msg = f"Audit failed: {e}"
            return {
                **state,
                "audit_report": error_msg,
                "errors": state["errors"] + [error_msg],
                "current_phase": "AUDIT_FAILED"
            }

    def _fix_node(self, state: SwarmState) -> SwarmState:
        """Apply fixes based on audit report."""
        if "FAILED" in state.get("current_phase", ""):
            return {**state, "fixes_applied": [], "current_phase": "FIX_SKIPPED"}

        print("🔧 FIX: Applying corrections...")
        fixes_applied = []

        # For each file, attempt fixes based on audit
        for file_path, content in state["files"].items():
            try:
                # Extract relevant issues for this file from audit
                fixed_code = self.fixer.fix_issue(
                    file_path=file_path,
                    code_content=content,
                    issue_description=f"Based on audit report:\n{state['audit_report']}\n\nFix any issues found in this file."
                )
                fixes_applied.append(f"Fixed: {file_path}")
                
                # Save fixed file to sandbox
                sandbox_path = file_path.replace(state["target_dir"], "sandbox")
                os.makedirs(os.path.dirname(sandbox_path), exist_ok=True)
                
                # Extract code block from response
                if "```python" in fixed_code:
                    code_start = fixed_code.find("```python") + 9
                    code_end = fixed_code.find("```", code_start)
                    if code_end > code_start:
                        extracted_code = fixed_code[code_start:code_end].strip()
                        with open(sandbox_path, "w", encoding="utf-8") as f:
                            f.write(extracted_code)
                        fixes_applied.append(f"Saved to: {sandbox_path}")
                        
            except Exception as e:
                state["errors"].append(f"Fix failed for {file_path}: {e}")

        print(f"✅ FIX: Applied {len(fixes_applied)} correction(s)")
        return {**state, "fixes_applied": fixes_applied, "current_phase": "FIXED"}

    def _generate_node(self, state: SwarmState) -> SwarmState:
        """Generate tests for the code."""
        if "FAILED" in state.get("current_phase", ""):
            return {**state, "tests_generated": [], "current_phase": "GENERATE_SKIPPED"}

        print("🧪 GENERATE: Creating tests...")
        tests_generated = []

        for file_path, content in state["files"].items():
            if "__init__" in file_path or "test_" in file_path:
                continue

            try:
                tests = self.generator.generate_tests(file_path, content)
                
                # Save tests to sandbox
                test_filename = f"test_{os.path.basename(file_path)}"
                test_path = os.path.join("sandbox", "tests", test_filename)
                os.makedirs(os.path.dirname(test_path), exist_ok=True)
                
                # Extract code block
                if "```python" in tests:
                    code_start = tests.find("```python") + 9
                    code_end = tests.find("```", code_start)
                    if code_end > code_start:
                        extracted_tests = tests[code_start:code_end].strip()
                        with open(test_path, "w", encoding="utf-8") as f:
                            f.write(extracted_tests)
                        tests_generated.append(test_path)

            except Exception as e:
                state["errors"].append(f"Test generation failed for {file_path}: {e}")

        print(f"✅ GENERATE: Created {len(tests_generated)} test file(s)")
        return {**state, "tests_generated": tests_generated, "current_phase": "GENERATED"}

    def _report_node(self, state: SwarmState) -> SwarmState:
        """Generate final summary report."""
        print("\n" + "=" * 60)
        print("📊 REFACTORING SWARM - RAPPORT FINAL")
        print("=" * 60)
        
        report_lines = [
            f"📂 Fichiers analysés: {len(state['files'])}",
            f"🔧 Corrections appliquées: {len(state['fixes_applied'])}",
            f"🧪 Tests générés: {len(state['tests_generated'])}",
            f"❌ Erreurs: {len(state['errors'])}",
            "",
            "📝 RAPPORT D'AUDIT:",
            "-" * 40,
            state.get("audit_report", "N/A")[:500] + "..." if len(state.get("audit_report", "")) > 500 else state.get("audit_report", "N/A"),
        ]

        if state["errors"]:
            report_lines.extend([
                "",
                "⚠️ ERREURS RENCONTRÉES:",
                "-" * 40,
                *state["errors"]
            ])

        report = "\n".join(report_lines)
        print(report)
        print("=" * 60)

        # Log final report
        log_experiment(
            agent_name="Orchestrator",
            model_used="N/A",
            action=ActionType.ANALYSIS,
            details={
                "input_prompt": f"Swarm execution on {state['target_dir']}",
                "output_response": report
            },
            status="SUCCESS" if not state["errors"] else "PARTIAL"
        )

        return {**state, "current_phase": "COMPLETED"}

    def _run_tests(self, target_dir: str) -> tuple[bool, str]:
        """Run pytest on the target directory and return (passed, output)."""
        try:
            env = os.environ.copy()
            # Ensure the target dir is importable (e.g., sandbox contains modules under test)
            existing_path = env.get("PYTHONPATH", "")
            env["PYTHONPATH"] = os.pathsep.join(
                [target_dir, existing_path] if existing_path else [target_dir]
            )

            result = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", target_dir],
                capture_output=True,
                text=True,
                check=False,
                env=env,
            )
            passed = result.returncode == 0
            output = result.stdout + result.stderr
            return passed, output
        except Exception as exc:  # defensive: surface unexpected runner failures
            return False, f"Test runner error: {exc}"

    def run(self, target_dir: str, max_iterations: int = 10) -> SwarmState:
        """
        Execute the refactoring swarm with a test/fix loop.

        The loop stops early when tests pass, or after max_iterations.

        Args:
            target_dir (str): Path to directory containing Python files.
            max_iterations (int): Max iterations of (refactor + test).

        Returns:
            SwarmState: Final state with all results.
        """

        latest_state: SwarmState = {
            "target_dir": target_dir,
            "files": {},
            "audit_report": "",
            "fixes_applied": [],
            "tests_generated": [],
            "current_phase": "INITIALIZED",
            "errors": [],
            "tests_output": "",
        }

        print(f"\n🚀 REFACTORING SWARM - Démarrage sur: {target_dir}\n")

        for iteration in range(1, max_iterations + 1):
            print(f"\n=== ITERATION {iteration}/{max_iterations} ===")

            # Execute the refactoring pipeline
            latest_state = self.graph.invoke(latest_state)

            # Run tests after fixes/generation
            tests_passed, test_output = self._run_tests(target_dir)
            latest_state["tests_output"] = test_output

            if tests_passed:
                print("✅ Tests passed. Stopping loop.")
                break

            print("❌ Tests failed. Attempting another fix cycle...")

            # If the pipeline already failed critically, stop early
            if "FAILED" in latest_state.get("current_phase", ""):
                latest_state["errors"].append("Pipeline failed before tests could pass.")
                break

        else:
            latest_state["errors"].append(
                f"Reached max iterations ({max_iterations}) without passing tests."
            )

        return latest_state
