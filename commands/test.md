---
description: Write comprehensive tests with TDD or verification approach
---
# Write Tests

Write comprehensive tests for the code. If $ARGUMENTS provided, focus on those files.

## Approach

First, ask me: **TDD** (write tests first) or **Verification** (test existing code)?

Then:
1. Find the implementation files and existing test patterns in the codebase
2. Identify what's not covered
3. Prioritize: happy path → edge cases → error handling → integration

## Test Focus

**Must test:**
- Core business logic
- Public APIs
- Error handling and validation
- Security-critical code

**Should test:**
- Edge cases and boundaries
- Integration points
- Data transformations

**Skip:**
- Trivial getters/setters
- Framework code
- Third-party libraries

## Writing Tests

- Follow project conventions and test framework patterns
- Use clear, descriptive names (what is being tested, not implementation details)
- Structure: Arrange → Act → Assert
- Cover edge cases: null, empty, boundary values, invalid input
- Test error paths and exceptions

After writing, run tests and verify they pass (verification mode) or fail appropriately (TDD mode). Fix any issues found.
