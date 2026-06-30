# Implementation Plan: AutoSpec Multi-Agent Pipeline

## Overview

This plan builds AutoSpec in Python as a single-process package (`autospec/`). It is ordered to reach a **runnable end-to-end demo as fast as possible**: tasks 1–6 deliver `python -m autospec` streaming a full Spec → Build → Test → Review run on the deterministic fallback and persisting all five artifacts. Tasks 7–12 then layer in the self-correcting retry loop, real pytest/coverage execution, constraint checking, the quality gate, tip-calculator hardening, and the full property-based test suite.

Environment notes:
- Target runtime is Python 3.9.6. Add `from __future__ import annotations` to every module so the `X | None` annotations used in the design parse on 3.9.
- `pytest`, `coverage`, and `hypothesis` are not installed yet and are installed in task 1.1.

Stopping early: every test/hardening sub-task marked with `*` is optional. After task 6 (the demo milestone) you have a working, demonstrable pipeline; you can stop there or continue layering as time allows.

## Tasks

- [x] 1. Set up dependencies and project scaffold
  - [x] 1.1 Install tooling and create the package skeleton
    - Run `pip install pytest coverage hypothesis` and capture them in `requirements.txt`
    - Create the `autospec/` package: `__init__.py`, `__main__.py`, `models.py`, `errors.py`, `streaming.py`, `store.py`, `llm.py`, `demo.py`, `orchestrator.py`, `quality.py`, `constraints.py`, `test_runner.py`, and `autospec/agents/` (`__init__.py`, `spec_agent.py`, `build_agent.py`, `test_agent.py`, `review_agent.py`)
    - Create the `tests/` directory and a minimal `pyproject.toml`/`pytest.ini` configuring pytest + coverage for the `autospec` package
    - Add `from __future__ import annotations` to each new module for Python 3.9 compatibility
    - _Requirements: R1, R12_

- [x] 2. Implement core data models and error types
  - [x] 2.1 Implement immutable data models and `AgentError`
    - In `errors.py`, define `AgentError(stage, message)`
    - In `models.py`, define frozen dataclasses: `Brief`, `RunConfig` (with `validate() -> list[str]`), `AcceptanceCriterion`, `Requirement`, `SpecDocument` (with `all_criteria()`), `GeneratedCode`, `TestSuite`, `TestResult`, `TestReport`, `Gap`, `AlignmentVerdict`, `PipelineResult`, and `PersistResult`
    - Implement `RunConfig.validate()`: tech-stack must be exact "Python"/"Node" (R2.1/2.2), threshold must be numeric in 0–100 inclusive (R2.3/2.4), returning one human-readable entry per failing field (R2.6)
    - _Requirements: R2.1, R2.2, R2.3, R2.4, R2.6, R5.6, R6.1, R6.6, R10_

  - [ ]* 2.2 Write property test for tech-stack validation
    - **Property 5: Tech-stack validation is exact-match**
    - **Validates: Requirements 2.1, 2.2**

  - [ ]* 2.3 Write property test for quality-threshold validation
    - **Property 6: Quality-threshold validation is range-bounded**
    - **Validates: Requirements 2.3, 2.4**

  - [ ]* 2.4 Write property test for multi-field validation reporting
    - **Property 7: Validation reports every failing field and blocks all artifacts**
    - **Validates: Requirements 2.5, 2.6**

  - [ ]* 2.5 Write property test for test-report count/coverage consistency
    - **Property 11: Test report counts and coverage are consistent**
    - **Validates: Requirements 5.6**

- [x] 3. Implement cross-cutting services (streaming + persistence)
  - [x] 3.1 Implement `ConsoleStreamer`
    - In `streaming.py`, implement `emit_output(agent, output)` (R8.1), `emit_handoff(from_agent, to_agent)` naming both agents (R8.2), `emit_reattempt(attempt, gaps)` listing the attempt number and each gap's criterion id (R8.3), and `emit_error(agent, message)` (R8.4)
    - Mirror streamed lines into an in-memory transcript buffer for the `run_log.txt` artifact
    - _Requirements: R8.1, R8.2, R8.3, R8.4_

  - [ ]* 3.2 Write property test for handoff and re-attempt messages
    - **Property 17: Handoff and re-attempt messages are complete**
    - **Validates: Requirements 8.2, 8.3**

  - [x] 3.3 Implement `ArtifactStore`
    - In `store.py`, implement `persist(name, content) -> PersistResult`: create the `Artifact_Directory` if absent (R9.6) and write a non-empty file (R9.1–9.5)
    - On write failure, keep content in memory, return an error-flagged `PersistResult` naming the artifact, and do not raise (R9.7)
    - _Requirements: R9.1, R9.2, R9.3, R9.4, R9.5, R9.6, R9.7_

  - [ ]* 3.4 Write property test for persistence round-trip
    - **Property 18: Artifact persistence round-trip**
    - **Validates: Requirements 9.1, 9.2, 9.3, 9.4, 9.5, 9.6**

  - [ ]* 3.5 Write property test for persistence failure isolation
    - **Property 19: One persistence failure does not stop the others**
    - **Validates: Requirements 9.7**

- [x] 4. Implement the LLM client layer, deterministic fallback, and demo brief
  - [x] 4.1 Implement `LLMClient`, `DeterministicFallbackClient`, factory, and Bedrock stub
    - In `llm.py`, define the `LLMClient` protocol (`complete(system, prompt, schema)`), a `BedrockClient` stub, and `DeterministicFallbackClient` returning curated, schema-valid spec/code/test/review responses for the tip-calculator `Demo_Brief`
    - Embed the known-good tip-calculator module source and its known-good pytest suite + report in the fallback so the demo runs fully offline (R13, demo resilience)
    - Implement a client factory that selects Bedrock when configured/reachable and silently falls back to `DeterministicFallbackClient` otherwise
    - _Requirements: R4.3, R5.1, R13_

  - [x] 4.2 Implement the built-in demo brief and default config
    - In `demo.py`, define `DEMO_BRIEF` (plain-English tip calculator: bill total, tip %, people → tip, total, per-person) and `DEFAULT_RUN_CONFIG` = `RunConfig("Python", 90)`
    - _Requirements: R12.1, R12.2_

  - [ ]* 4.3 Write example test for the demo brief and default config
    - Assert `DEMO_BRIEF` text mentions bill/tip/people and `DEFAULT_RUN_CONFIG` equals ("Python", 90) (example/smoke test)
    - _Requirements: R12.1, R12.2_

- [x] 5. Implement the four agents (fallback-backed, minimal)
  - [x] 5.1 Implement `SpecAgent`
    - In `spec_agent.py`, implement `run(brief) -> SpecDocument` via the injected `LLMClient`, producing contiguously numbered requirements (1..n), ≥1 Given/When/Then criterion each, a non-empty edge-case list, and no source code; raise `AgentError` on empty/non-actionable briefs (R3.5)
    - _Requirements: R3.1, R3.2, R3.3, R3.4, R3.5_

  - [ ]* 5.2 Write property test for spec structure
    - **Property 8: Spec document is structurally well-formed**
    - **Validates: Requirements 3.1, 3.2, 3.3**

  - [x] 5.3 Implement `BuildAgent` (single-module generation)
    - In `build_agent.py`, implement `run(spec, gaps=()) -> GeneratedCode` producing a single Python module where every numbered requirement maps to ≥1 code element (R4.2) and no untraceable functionality is added (R4.4); raise `AgentError` on zero-requirement/unparseable spec (R4.5). Constraint enforcement/repair is added in task 9
    - _Requirements: R4.1, R4.2, R4.3, R4.4, R4.5, R11.1_

  - [x] 5.4 Implement `TestAgent` (fallback-backed suite + report)
    - In `test_agent.py`, implement `run(spec, code) -> (TestSuite, TestReport)` producing one test per acceptance criterion tagged with the criterion id (R5.3); raise `AgentError` on missing/unparseable spec or code (R5.2). Initially source the suite and report from the deterministic fallback; real pytest/coverage execution is wired in task 8
    - _Requirements: R5.1, R5.2, R5.3, R5.6, R11.2_

  - [x] 5.5 Implement `ReviewAgent`
    - In `review_agent.py`, implement `run(spec, code, report) -> AlignmentVerdict`: a criterion is "met" iff ≥1 mapped test exists and all mapped tests passed (R6.3); ALIGNED iff all criteria met else NOT ALIGNED (R6.4/6.5); emit exactly one `Gap` per unmet criterion with a non-empty discrepancy (R6.6/6.7); raise `AgentError` naming each missing/unreadable input (R6.2)
    - _Requirements: R6.1, R6.2, R6.3, R6.4, R6.5, R6.6, R6.7_

  - [ ]* 5.6 Write property test for verdict correctness
    - **Property 12: Verdict correctness from criterion satisfaction**
    - **Validates: Requirements 6.1, 6.3, 6.4, 6.5**

  - [ ]* 5.7 Write property test for gap correspondence
    - **Property 13: Gaps correspond exactly to unmet criteria**
    - **Validates: Requirements 6.6, 6.7**

  - [ ]* 5.8 Write property test for review input guards
    - **Property 14: Review withholds verdict on missing input**
    - **Validates: Requirements 6.2**

  - [ ]* 5.9 Write property test for agent invalid-input guards
    - **Property 9: Invalid input to an agent yields an error and no output**
    - **Validates: Requirements 3.5, 4.5, 5.2**

- [x] 6. Implement the orchestrator and CLI — demo milestone
  - [x] 6.1 Implement `Orchestrator.run` (sequential, no retry yet)
    - In `orchestrator.py`, implement the pre-flight gate (missing brief/config → terminate before any stage with a naming error, R1.4/1.5; `RunConfig.validate()` gate, R2.5), sequential Spec → Build → Test → Review execution (R1.1), stop-on-failure with prior-artifact retention and failed status (R1.6), final completed status with all artifacts present (R1.3), streaming of each output + handoff (R8.1/8.2), and persistence of all five artifacts plus `run_log.txt` (R9, R12.4). Run without requiring human input (R1.2)
    - _Requirements: R1.1, R1.2, R1.3, R1.4, R1.5, R1.6, R2.5, R8.1, R8.2, R9, R12.3, R12.4_

  - [x] 6.2 Implement the CLI entry point
    - In `__main__.py`, wire `python -m autospec` (no args) to run `DEMO_BRIEF` with `DEFAULT_RUN_CONFIG` through the orchestrator using the client factory (deterministic fallback offline), writing artifacts under `artifacts/<run_id>/`
    - _Requirements: R12.3, R12.4_

  - [x] 6.3 Checkpoint — end-to-end demo milestone
    - Run `python -m autospec` and confirm a streamed Spec → Build → Test → Review relay completes on the deterministic fallback and persists all five artifacts (spec_document.json, generated_code.py, test_suite.py, test_report.json, alignment_verdict.json) plus run_log.txt. Ensure all tests written so far pass; ask the user if questions arise.

  - [ ]* 6.4 Write property test for sequential execution
    - **Property 1: Sequential agent execution** (use instrumented mock agents)
    - **Validates: Requirements 1.1, 7.2, 12.3**

  - [ ]* 6.5 Write property test for successful-run completion
    - **Property 2: Successful run reports completion with all artifacts**
    - **Validates: Requirements 1.3**

  - [ ]* 6.6 Write property test for missing-input termination
    - **Property 3: Missing primary input terminates before any stage**
    - **Validates: Requirements 1.4, 1.5**

  - [ ]* 6.7 Write property test for stage-failure handling
    - **Property 4: Stage failure stops downstream and retains prior artifacts**
    - **Validates: Requirements 1.6, 7.6, 8.4**

- [x] 7. Implement the self-correcting retry loop
  - [x] 7.1 Add the bounded retry loop to the orchestrator
    - Extend `orchestrator.py`: on NOT ALIGNED with re-attempts < 3, return control to Build with the gaps, increment the re-attempt count, and re-run Build → Test → Review in order (R7.1/7.2/7.3); on ALIGNED end immediately (R7.5); at 3 re-attempts end with the final verdict + remaining gaps (R7.4); on agent failure during a re-attempt end and retain the last review's gaps (R7.6); stream each re-attempt message (R8.3)
    - _Requirements: R7.1, R7.2, R7.3, R7.4, R7.5, R7.6, R8.3_

  - [ ]* 7.2 Write property test for the bounded retry loop
    - **Property 15: Bounded self-correcting retry loop** (instrumented mock agents)
    - **Validates: Requirements 7.1, 7.3, 7.4**

  - [ ]* 7.3 Write property test for alignment halting re-attempts
    - **Property 16: Alignment halts re-attempts immediately**
    - **Validates: Requirements 7.5**

- [x] 8. Implement real pytest/coverage execution in the Test Agent
  - [x] 8.1 Implement the pytest subprocess runner
    - In `test_runner.py`, run the persisted suite against the generated module via a `pytest --cov` subprocess under a 300s hard timeout (R5.5); on timeout, terminate and record unfinished tests as "failed"; parse per-test pass/fail and line-coverage % into structured results (R5.6)
    - _Requirements: R5.4, R5.5, R5.6_

  - [ ] 8.2 Wire `TestAgent` to the real runner
    - Update `test_agent.py` to execute the generated suite via `test_runner` and build the `TestReport` from real results, mapping exactly one test per acceptance criterion to its criterion id (R5.3/5.4)
    - _Requirements: R5.3, R5.4, R5.6_

  - [ ]* 8.3 Write property test for the criterion↔test bijection
    - **Property 10: One test per acceptance criterion (bijection)**
    - **Validates: Requirements 5.3**

  - [ ]* 8.4 Write example/integration test for execution and timeout
    - Verify the runner produces a report; inject a sleeping test to confirm timeout handling marks unfinished tests failed (example/edge test)
    - _Requirements: R5.4, R5.5_

- [ ] 9. Implement constraint checking and code repair
  - [ ] 9.1 Implement `ConstraintChecker` and integrate repair into `BuildAgent`
    - In `constraints.py`, AST-scan generated code for prohibited DB/network/file-I/O/web-server operations (imports such as socket/os/requests/sqlite3/open and server frameworks) and report violations (R11.4); confirm single-module/single-file shape (R11.1)
    - Update `build_agent.py` to enforce pure functions (R11.3), regenerate on constraint violations (R11.6), and add missing docstrings to public functions (R11.5/11.7)
    - _Requirements: R11.1, R11.3, R11.4, R11.5, R11.6, R11.7_

  - [ ]* 9.2 Write property test for finalized-code constraints
    - **Property 22: Generated code is a single pure module with documented public functions**
    - **Validates: Requirements 4.1, 11.1, 11.2, 11.4, 11.5, 11.7**

  - [ ]* 9.3 Write property test for the constraint checker
    - **Property 23: Constraint checker detects prohibited operations**
    - **Validates: Requirements 11.4, 11.6**

  - [ ]* 9.4 Write example test for constraint repair
    - Feed a violating module and assert detection plus a repaired output that passes the checker (example test)
    - _Requirements: R11.6_

- [ ] 10. Implement the quality gate
  - [ ] 10.1 Implement `QualityGate.evaluate` and wire into the pipeline
    - In `quality.py`, implement `evaluate(report, threshold)`: status "met" iff coverage ≥ threshold else "not met" (R10.1/10.2/10.3); when coverage is unmeasurable set "not met" with a coverage note (R10.4); when no threshold is configured omit the comparison and record an error indication (R10.5); in both edge branches leave recorded test results unchanged. Invoke it from the orchestrator after each Test stage and record the result on the `TestReport`
    - _Requirements: R10.1, R10.2, R10.3, R10.4, R10.5_

  - [ ]* 10.2 Write property test for quality-gate comparison
    - **Property 20: Quality-gate comparison correctness**
    - **Validates: Requirements 10.1, 10.2, 10.3**

  - [ ]* 10.3 Write property test for quality-gate edge branches
    - **Property 21: Quality-gate edge branches preserve test results**
    - **Validates: Requirements 10.4, 10.5**

- [ ] 11. Harden the generated tip-calculator demo code
  - [ ] 11.1 Finalize the deterministic tip-calculator module
    - Ensure the curated tip-calculator (in the fallback) computes tip = round2(bill × pct / 100), total = round2(bill + tip), per-person = round2(total / people) across the full range (bill 0.00–999,999,999.99, pct 0–100, people ≥ 1) using `Decimal` round-half-up, returns identical outputs for identical inputs (R13.1/13.2/13.3/11.3), handles zero-tip (R13.4), and rejects invalid people/bill/pct without mutating inputs (R13.5/13.6)
    - _Requirements: R13.1, R13.2, R13.3, R13.4, R13.5, R13.6, R11.3_

  - [ ]* 11.2 Write property test for tip-calculator computation
    - **Property 24: Tip-calculator computation is correct and deterministic**
    - **Validates: Requirements 13.1, 13.2, 13.3, 11.3**

  - [ ]* 11.3 Write property test for zero-tip behaviour
    - **Property 25: Zero tip yields zero tip amount and unchanged total**
    - **Validates: Requirements 13.4**

  - [ ]* 11.4 Write property test for invalid-input rejection
    - **Property 26: Invalid tip-calculator inputs are rejected without mutation**
    - **Validates: Requirements 13.5, 13.6**

- [ ] 12. Integration and final wiring
  - [ ] 12.1 Write the end-to-end integration test
    - Run the full pipeline via the CLI path with the deterministic fallback and assert all five artifacts exist and are non-empty and the verdict is ALIGNED at ≥90% coverage (R12.3/12.4)
    - _Requirements: R12.3, R12.4_

  - [ ]* 12.2 Write example tests for streaming order and no-human-input
    - Run with closed stdin and captured stdout; assert completion and that each agent's full output prints before its handoff label, and that errors print naming the failed agent (example tests)
    - _Requirements: R1.2, R8.1, R8.4_

  - [ ] 12.3 Final checkpoint
    - Ensure all tests pass and `python -m autospec` produces a clean ALIGNED run; ask the user if questions arise.

## Notes

- Tasks marked with `*` are optional (test/hardening) and can be skipped for a faster MVP; the demo is fully working after task 6.
- Each task references specific requirements (R1–R13) for traceability, and each property-test sub-task references a single design property (Properties 1–26) with the requirements clause it validates.
- Property tests use Hypothesis (`@settings(max_examples=100)` minimum) and tag each test with `# Feature: autospec-pipeline, Property {n}: ...`. Orchestration properties use instrumented mock agents — no real LLM calls.
- Each property test lives in its own test file so optional test tasks can run in parallel without file conflicts.
- Checkpoints (6.3, 12.3) ensure incremental validation at the demo milestone and at completion.

## Task Dependency Graph

```json
{
  "waves": [
    { "id": 0, "tasks": ["1.1"] },
    { "id": 1, "tasks": ["2.1", "3.3"] },
    { "id": 2, "tasks": ["2.2", "2.3", "2.4", "2.5", "3.1", "3.4", "3.5", "4.1", "4.2"] },
    { "id": 3, "tasks": ["3.2", "4.3", "5.1", "5.3", "5.4", "5.5"] },
    { "id": 4, "tasks": ["5.2", "5.6", "5.7", "5.8", "5.9", "6.1"] },
    { "id": 5, "tasks": ["6.2", "6.4", "6.5", "6.6", "6.7"] },
    { "id": 6, "tasks": ["7.1", "8.1"] },
    { "id": 7, "tasks": ["7.2", "7.3", "8.2", "9.1", "10.1", "11.1"] },
    { "id": 8, "tasks": ["8.3", "8.4", "9.2", "9.3", "9.4", "10.2", "10.3", "11.2", "11.3", "11.4", "12.1"] },
    { "id": 9, "tasks": ["12.2"] }
  ]
}
```
