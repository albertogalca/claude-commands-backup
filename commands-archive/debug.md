---
description: Systematic debugging with root cause analysis and fixes
---
# Debug Issue

Diagnose and fix the bug systematically. If $ARGUMENTS provided, focus on those areas.

## Process

1. **Reproduce** - Confirm the issue:
   - Run failing tests or reproduce the bug
   - Capture full error output and stack traces
   - Ask for reproduction steps if unclear

2. **Investigate** - Find root cause:
   - Examine error messages and logs
   - Check recent changes (`git log`, `git diff`)
   - Read relevant code
   - Trace execution path

3. **Fix** - Apply minimal solution:
   - Make focused changes addressing root cause
   - Keep changes minimal and isolated
   - Update or add tests to prevent regression

4. **Validate** - Verify the fix:
   - Run all tests
   - Verify types pass
   - Test edge cases manually
   - Ensure no regressions

## Debugging Strategies

- **Failing tests** - Read test expectations, run in isolation, check setup/teardown
- **Runtime errors** - Follow stack trace, check variable states at failure point
- **Logic bugs** - Trace data transformations, verify assumptions, check boundary conditions
- **Performance** - Profile hot paths, check for N+1 queries, identify memory leaks
- **Integration** - Verify API contracts, validate data formats, test components in isolation

After fixing, add test cases that would have caught this bug to prevent future regressions.
