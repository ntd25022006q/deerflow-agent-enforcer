# ============================================================
# DEERFLOW AGENT ENFORCER — GITHUB COPILOT INSTRUCTIONS
# Version: 2.0.0 | Framework: DeerFlow Agentic Workflow
# ============================================================

You are GitHub Copilot operating under the DeerFlow Agent Enforcer framework.
You MUST follow all rules below when generating code, completing requests, or providing suggestions.

## MANDATORY BEHAVIOR

### Code Generation Rules
1. NEVER suggest code that deletes files or directories
2. NEVER generate mock data or placeholder implementations
3. NEVER suggest deprecated or incompatible APIs
4. ALWAYS verify API correctness against known documentation
5. ALWAYS include proper error handling
6. ALWAYS follow existing code patterns in the project

### Code Completion Rules
1. Complete the current function/block — never leave it incomplete
2. Match the existing code style exactly (indentation, naming, patterns)
3. Include proper TypeScript types (no `any` without explicit comment)
4. Add error handling for edge cases
5. Ensure all imports are valid and necessary

### Code Review Rules
1. Flag security vulnerabilities immediately
2. Flag potential infinite loops or unbounded recursion
3. Flag missing error handling
4. Flag dependency version conflicts
5. Flag performance anti-patterns

## 15 CORE RULES SUMMARY
1. **File Safety**: Never delete without explicit confirmation
2. **No Mocks**: Every function must be fully implemented
3. **Architecture First**: Plan before coding
4. **Minimal Changes**: Read first, change minimally
5. **Dependency Safety**: Check compatibility before installing
6. **Loop Safety**: All loops must terminate
7. **Evidence Based**: Verify APIs against docs
8. **Build Complete**: Include all assets and source
9. **Security First**: No secrets in code, validate inputs
10. **Testing Required**: Test every new function
11. **Context Aware**: Understand existing codebase
12. **Performance**: Optimize renders, lazy load, cache
13. **Error Handling**: try/catch all async, graceful failures
14. **Professional UI**: Responsive, accessible, consistent
15. **No Shortcuts**: Never ignore errors or type issues

## PROHIBITED SUGGESTIONS
- ❌ Code that deletes files or directories
- ❌ Placeholder/mock implementations
- ❌ `any` type without justification
- ❌ `eval()` or dangerous patterns
- ❌ Hardcoded credentials
- ❌ console.log in production code
- ❌ Unhandled promise rejections
- ❌ Infinite loops
- ❌ Non-responsive layouts
- ❌ Missing error handling
- ❌ Deprecated API usage
