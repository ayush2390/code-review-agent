# app/analyzers.py
import ast
import re
from typing import List, Dict, Any
from dataclasses import dataclass

@dataclass
class CodeIssue:
    type: str
    line: int
    description: str
    suggestion: str
    severity: str = "medium"

class BaseAnalyzer:
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        """Base analyze method that all analyzers wil implement."""
        raise NotImplementedError
    
    def _format_issue(self, issue: CodeIssue) -> Dict[str, Any]:
        """Convert CodeIssue to dictionary format."""
        return {
            "type": issue.type,
            "line": issue.line,
            "description": issue.description,
            "suggestion": issue.suggestion,
            "severity": issue.severity
        }

class StyleAnalyzer(BaseAnalyzer):
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[CodeIssue] = []
        
        # Split code into lines for analysis
        lines = code.split('\n')
        
        for i, line in enumerate(lines, start=1):
            # Check line length (PEP 8: 79 characters)
            if len(line.rstrip()) > 79:
                issues.append(CodeIssue(
                    type="style",
                    line=i,
                    description="Line exceeds maximum length of 79 characters",
                    suggestion="Break the line into multiple lines or use line continuation",
                    severity="low"
                ))
            
            # Check indentation (multiple of 4 spaces)
            leading_spaces = len(line) - len(line.lstrip())
            if leading_spaces % 4 != 0 and line.strip():
                issues.append(CodeIssue(
                    type="style",
                    line=i,
                    description="Incorrect indentation. Use multiples of 4 spaces",
                    suggestion="Fix indentation to use 4 spaces per level",
                    severity="low"
                ))
            
            # Check trailing whitespace
            if line.rstrip() != line and line.strip():
                issues.append(CodeIssue(
                    type="style",
                    line=i,
                    description="Line contains trailing whitespace",
                    suggestion="Remove trailing whitespace",
                    severity="low"
                ))
            
            # Check naming conventions
            variable_pattern = r'[a-z_][a-z0-9_]*$'
            class_pattern = r'[A-Z][a-zA-Z0-9]*$'
            
            # Check variable names
            var_matches = re.findall(r'\b(\w+)\s*=', line)
            for var_name in var_matches:
                if not re.match(variable_pattern, var_name) and not re.match(class_pattern, var_name):
                    issues.append(CodeIssue(
                        type="style",
                        line=i,
                        description=f"Variable name '{var_name}' doesn't follow PEP 8 naming convention",
                        suggestion="Use lowercase with underscores for variable names",
                        severity="low"
                    ))
        
        return [self._format_issue(issue) for issue in issues]


class BugAnalyzer(BaseAnalyzer):
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[CodeIssue] = []
        print("Inside Analyze Function Entry Point : ")
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return [self._format_issue(CodeIssue(
                type="bug",
                line=e.lineno or 1,
                description=f"Syntax error: {str(e)}",
                suggestion="Fix the syntax error to ensure code can be executed",
                severity="critical"
            ))]
        
        class BugFinder(ast.NodeVisitor):
            def __init__(self):
                self.issues = []
                self.scope_stack = [set()]  # Stack of sets for variable scoping
                self.defined_functions = set()
                # Add Python built-ins
                self.built_ins = set(dir(__builtins__))
                # Add commonly used modules that might be imported
                self.common_modules = {
                    'os', 'sys', 're', 'math', 'random', 'datetime', 
                    'json', 'collections', 'itertools', 'functools',
                    'analyze_code'  # Add any known global functions
                }
            
            def enter_scope(self):
                self.scope_stack.append(set())
            
            def exit_scope(self):
                self.scope_stack.pop()
            
            def add_to_current_scope(self, name):
                self.scope_stack[-1].add(name)
            
            def is_defined(self, name):
                # Check in all scopes from inner to outer
                print("This is the right time")
                return (name in self.built_ins or
                       name in self.common_modules or
                       name in self.defined_functions or
                       any(name in scope for scope in reversed(self.scope_stack)))
            
            def visit_Module(self, node):
                self.enter_scope()  # Global scope
                self.generic_visit(node)
                self.exit_scope()
            
            def visit_FunctionDef(self, node):
                self.defined_functions.add(node.name)
                self.enter_scope()
                # Add arguments to the new scope
                for arg in node.args.args:
                    self.add_to_current_scope(arg.arg)
                self.generic_visit(node)
                self.exit_scope()
            
            def visit_ClassDef(self, node):
                self.defined_functions.add(node.name)
                self.enter_scope()
                self.generic_visit(node)
                self.exit_scope()
            
            def visit_Import(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.add_to_current_scope(name)
                self.generic_visit(node)
            
            def visit_ImportFrom(self, node):
                for alias in node.names:
                    name = alias.asname if alias.asname else alias.name
                    self.add_to_current_scope(name)
                self.generic_visit(node)
            
            def visit_Name(self, node):
                print("This is node : ",node)
                if isinstance(node.ctx, ast.Store):
                    self.add_to_current_scope(node.id)
                elif isinstance(node.ctx, ast.Load):
                    if not self.is_defined(node.id):
                        self.issues.append(CodeIssue(
                            type="bug",
                            line=node.lineno,
                            description=f"Potential use of undefined variable '{node.id}'",
                            suggestion=f"Ensure '{node.id}' is defined before use",
                            severity="high"
                        ))
                self.generic_visit(node)
            
            def visit_Attribute(self, node):
                # Skip undefined variable checks for attributes
                self.generic_visit(node)
        
        bug_finder = BugFinder()
        bug_finder.visit(tree)
        issues.extend(bug_finder.issues)
        
        return [self._format_issue(issue) for issue in issues]
    

class PerformanceAnalyzer(BaseAnalyzer):
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[CodeIssue] = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Let BugAnalyzer handle syntax errors
        
        class PerformanceFinder(ast.NodeVisitor):
            def __init__(self):
                self.issues = []
            
            def visit_For(self, node):
                # Check for list comprehension opportunities
                if isinstance(node.body, list) and len(node.body) == 1:
                    if isinstance(node.body[0], ast.Append):
                        self.issues.append(CodeIssue(
                            type="performance",
                            line=node.lineno,
                            description="For loop could be replaced with list comprehension",
                            suggestion="Consider using a list comprehension for better performance",
                            severity="low"
                        ))
                self.generic_visit(node)
            
            def visit_Call(self, node):
                # Check for inefficient list operations
                if isinstance(node.func, ast.Name):
                    if node.func.id == 'range' and len(node.args) == 1:
                        if isinstance(node.args[0], ast.Call):
                            if getattr(node.args[0].func, 'id', None) == 'len':
                                self.issues.append(CodeIssue(
                                    type="performance",
                                    line=node.lineno,
                                    description="Inefficient range(len()) pattern detected",
                                    suggestion="Use 'enumerate()' instead of range(len())",
                                    severity="low"
                                ))
                self.generic_visit(node)
            
            def visit_ListComp(self, node):
                # Check for nested list comprehensions
                if any(isinstance(gen.iter, ast.ListComp) for gen in node.generators):
                    self.issues.append(CodeIssue(
                        type="performance",
                        line=node.lineno,
                        description="Nested list comprehension detected",
                        suggestion="Consider using regular loops for better readability and possibly better performance",
                        severity="medium"
                    ))
                self.generic_visit(node)
        
        performance_finder = PerformanceFinder()
        performance_finder.visit(tree)
        issues.extend(performance_finder.issues)
        
        return [self._format_issue(issue) for issue in issues]

class BestPracticesAnalyzer(BaseAnalyzer):
    def analyze(self, code: str) -> List[Dict[str, Any]]:
        issues: List[CodeIssue] = []
        
        try:
            tree = ast.parse(code)
        except SyntaxError:
            return []  # Let BugAnalyzer handle syntax errors
        
        class BestPracticesFinder(ast.NodeVisitor):
            def __init__(self):
                self.issues = []
                self.function_lines = {}
                self.docstring_count = 0
            
            def visit_FunctionDef(self, node):
                # Check function length
                end_line = max(child.lineno for child in ast.walk(node) if hasattr(child, 'lineno'))
                func_length = end_line - node.lineno + 1
                
                if func_length > 50:
                    self.issues.append(CodeIssue(
                        type="best_practice",
                        line=node.lineno,
                        description=f"Function '{node.name}' is too long ({func_length} lines)",
                        suggestion="Consider breaking down the function into smaller, more focused functions",
                        severity="medium"
                    ))
                
                # Check for docstring
                if not ast.get_docstring(node):
                    self.issues.append(CodeIssue(
                        type="best_practice",
                        line=node.lineno,
                        description=f"Function '{node.name}' lacks a docstring",
                        suggestion="Add a docstring to document the function's purpose, parameters, and return value",
                        severity="low"
                    ))
                
                # Check number of parameters
                if len(node.args.args) > 5:
                    self.issues.append(CodeIssue(
                        type="best_practice",
                        line=node.lineno,
                        description=f"Function '{node.name}' has too many parameters ({len(node.args.args)})",
                        suggestion="Consider grouping related parameters into a class or using keyword arguments",
                        severity="medium"
                    ))
                
                self.generic_visit(node)
            
            def visit_ClassDef(self, node):
                # Check for class docstring
                if not ast.get_docstring(node):
                    self.issues.append(CodeIssue(
                        type="best_practice",
                        line=node.lineno,
                        description=f"Class '{node.name}' lacks a docstring",
                        suggestion="Add a docstring to document the class's purpose and usage",
                        severity="low"
                    ))
                
                # Check inheritance depth
                inheritance_depth = len(node.bases)
                if inheritance_depth > 2:
                    self.issues.append(CodeIssue(
                        type="best_practice",
                        line=node.lineno,
                        description=f"Class '{node.name}' has deep inheritance ({inheritance_depth} levels)",
                        suggestion="Consider composition over inheritance or simplify the class hierarchy",
                        severity="medium"
                    ))
                
                self.generic_visit(node)
            
            def visit_Import(self, node):
                # Check for wildcard imports
                for name in node.names:
                    if name.name == '*':
                        self.issues.append(CodeIssue(
                            type="best_practice",
                            line=node.lineno,
                            description="Wildcard import used",
                            suggestion="Explicitly import only the needed names",
                            severity="medium"
                        ))
                self.generic_visit(node)
        
        best_practices_finder = BestPracticesFinder()
        best_practices_finder.visit(tree)
        issues.extend(best_practices_finder.issues)
        
        return [self._format_issue(issue) for issue in issues]

