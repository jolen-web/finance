"""
LLM-powered error fixer agent for Finance Tracker
Analyzes runtime errors and suggests/applies code fixes using Claude API
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import anthropic

# Load environment variables
load_dotenv()


class ErrorFixerAgent:
    """Agent that uses Claude to analyze and fix code errors"""

    def __init__(self, api_key: str = None):
        """Initialize the error fixer with Claude API"""
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = "claude-3-5-sonnet-20241022"  # Will use Claude Haiku if API key not available
        self.project_root = Path(__file__).parent

    def analyze_error(self, error_message: str, error_type: str = None,
                     file_path: str = None, context: str = None) -> dict:
        """
        Analyze an error and get fix recommendations from Claude

        Args:
            error_message: The error message/traceback
            error_type: Type of error (e.g., "TypeError", "ValueError")
            file_path: Path to the file where error occurred
            context: Additional context about the error

        Returns:
            Dictionary with analysis and suggested fixes
        """

        # Read the problematic file if path provided
        file_content = ""
        if file_path and Path(file_path).exists():
            with open(file_path, 'r') as f:
                file_content = f.read()

        # Construct prompt for Claude
        error_type_str = error_type or 'Unknown'
        file_path_str = file_path or 'Unknown'
        file_content_str = f"FILE CONTENT:\n{file_content}" if file_content else ""
        context_str = f"ADDITIONAL CONTEXT:\n{context}" if context else ""

        prompt = f"""You are an expert Python developer debugging code errors.

ERROR DETAILS:
- Error Type: {error_type_str}
- Error Message: {error_message}
- File: {file_path_str}

{file_content_str}

{context_str}

Please:
1. Analyze the root cause of this error
2. Identify the problematic code section
3. Explain why the error occurs
4. Provide a specific code fix with the exact changes needed
5. Show the before and after code

Format your response as JSON with these keys:
- "root_cause": Brief explanation of the root cause
- "problem_section": The problematic code snippet
- "explanation": Detailed explanation
- "fix_code": The corrected code to replace the problem section
- "import_statements": Any new imports needed (as list)
- "confidence": Your confidence in this fix (0-1)
"""

        message = self.client.messages.create(
            model=self.model,
            max_tokens=2048,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )

        response_text = message.content[0].text

        # Try to parse JSON from response
        try:
            # Extract JSON from response
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                analysis = json.loads(json_match.group())
            else:
                analysis = {"raw_response": response_text}
        except json.JSONDecodeError:
            analysis = {"raw_response": response_text}

        return analysis

    def generate_patch(self, file_path: str, problem_section: str,
                      fix_code: str) -> dict:
        """
        Generate a patch file showing the changes

        Args:
            file_path: Path to the file to fix
            problem_section: The original problematic code
            fix_code: The fixed code

        Returns:
            Dictionary with patch information
        """
        with open(file_path, 'r') as f:
            original_content = f.read()

        # Find the section in the file
        if problem_section not in original_content:
            return {
                "success": False,
                "error": "Problem section not found in file. Code may have changed."
            }

        new_content = original_content.replace(problem_section, fix_code)

        return {
            "success": True,
            "file": file_path,
            "original": problem_section,
            "fixed": fix_code,
            "full_content": new_content,
            "timestamp": datetime.now().isoformat()
        }

    def apply_fix(self, patch: dict, auto_apply: bool = False) -> dict:
        """
        Apply a patch to the file

        Args:
            patch: Patch dictionary from generate_patch()
            auto_apply: If True, apply without confirmation

        Returns:
            Dictionary with result
        """
        if not patch.get("success"):
            return {"success": False, "error": patch.get("error")}

        file_path = patch["file"]

        if not auto_apply:
            # In interactive mode, user would confirm here
            print(f"\n{'='*60}")
            print(f"PATCH FOR: {file_path}")
            print(f"{'='*60}")
            print("ORIGINAL:")
            print(patch["original"])
            print("\nFIXED:")
            print(patch["fixed"])
            print(f"{'='*60}")
            confirm = input("Apply this fix? (y/n): ").strip().lower()
            if confirm != 'y':
                return {"success": False, "error": "User declined"}

        # Create backup
        backup_path = Path(file_path).with_suffix('.bak')
        with open(file_path, 'r') as f:
            backup_content = f.read()
        with open(backup_path, 'w') as f:
            f.write(backup_content)

        # Apply the fix
        with open(file_path, 'w') as f:
            f.write(patch["full_content"])

        return {
            "success": True,
            "file": file_path,
            "backup": str(backup_path),
            "message": f"Fix applied successfully. Backup saved to {backup_path}"
        }

    def fix_error(self, error_message: str, file_path: str = None,
                 auto_apply: bool = False, error_type: str = None,
                 context: str = None) -> dict:
        """
        Complete error fixing workflow

        Args:
            error_message: The error message
            file_path: Path to affected file
            auto_apply: Whether to apply fix automatically
            error_type: Type of error
            context: Additional context

        Returns:
            Complete result with analysis and applied fix
        """
        print(f"Analyzing error in {file_path}...")

        # Step 1: Analyze the error
        analysis = self.analyze_error(
            error_message=error_message,
            file_path=file_path,
            error_type=error_type,
            context=context
        )

        print("Analysis complete!")
        print(f"Root cause: {analysis.get('root_cause', 'N/A')}")

        # Step 2: Generate patch if we have code to fix
        if file_path and "fix_code" in analysis and "problem_section" in analysis:
            patch = self.generate_patch(
                file_path=file_path,
                problem_section=analysis["problem_section"],
                fix_code=analysis["fix_code"]
            )

            if patch.get("success"):
                # Step 3: Apply the fix
                result = self.apply_fix(patch, auto_apply=auto_apply)

                return {
                    "success": True,
                    "analysis": analysis,
                    "patch": patch,
                    "result": result
                }

        return {
            "success": False,
            "analysis": analysis,
            "error": "Could not generate or apply patch"
        }


def main():
    """CLI interface for the error fixer"""
    import argparse

    parser = argparse.ArgumentParser(
        description="LLM-powered error fixer for Finance Tracker"
    )
    parser.add_argument("error_message", help="The error message or traceback")
    parser.add_argument("--file", help="Path to the file with the error")
    parser.add_argument("--type", help="Error type (e.g., TypeError, ValueError)")
    parser.add_argument("--context", help="Additional context about the error")
    parser.add_argument("--auto-apply", action="store_true",
                       help="Automatically apply the fix without confirmation")
    parser.add_argument("--analyze-only", action="store_true",
                       help="Only analyze, don't apply fixes")

    args = parser.parse_args()

    agent = ErrorFixerAgent()

    if args.analyze_only:
        result = agent.analyze_error(
            error_message=args.error_message,
            file_path=args.file,
            error_type=args.type,
            context=args.context
        )
        print("\nANALYSIS RESULT:")
        print(json.dumps(result, indent=2))
    else:
        result = agent.fix_error(
            error_message=args.error_message,
            file_path=args.file,
            auto_apply=args.auto_apply,
            error_type=args.type,
            context=args.context
        )

        if result["success"]:
            print("\n✅ FIX APPLIED SUCCESSFULLY")
            print(f"Message: {result['result']['message']}")
        else:
            print("\n❌ FIX FAILED")
            print(f"Error: {result.get('error', 'Unknown error')}")
            if "analysis" in result:
                print("\nAnalysis:")
                print(json.dumps(result["analysis"], indent=2))


if __name__ == "__main__":
    main()
