---
description: Large-scale refactoring with phased execution and validation
---
# Refactor Code

Refactor code systematically with minimal risk. If $ARGUMENTS provided, focus on those areas.

## Strategy

Minimize risk through:
- Small phases (change one thing at a time)
- Continuous testing (validate after each phase)
- Type-driven (let compiler catch breaks)
- Reversible (each phase can be rolled back independently)

## Process

1. **Analyze scope** - Understand what's affected:
   - Find all affected files and dependencies
   - Check test coverage
   - Map integration points and risks

2. **Plan phases** - Break into incremental steps:
   - Each phase should be independently validatable
   - Each phase should be reversible
   - Present phased plan before starting
   - Get confirmation to proceed

3. **Establish baseline** - Ensure tests exist:
   - Write characterization tests for existing behavior if missing
   - Run tests to establish baseline
   - This proves refactor doesn't change behavior

4. **Execute each phase**:
   - Make focused changes for one phase
   - Run tests immediately (fix if failing)
   - Type check and fix
   - Manual validation
   - Commit with clear message
   - Report progress
   - If phase fails repeatedly: break into smaller phases or reassess

5. **Cleanup**:
   - Remove scaffolding and temporary code
   - Final validation (tests pass, types valid, no dead code)
   - Final review of all changes

6. **Report**:
   - What was refactored
   - Phases completed
   - Issues encountered
   - Follow-up recommendations

After each phase, validate: tests pass, types valid, manual testing done, changes committed.
