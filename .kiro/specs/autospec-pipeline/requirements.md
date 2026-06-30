# Requirements Document

## Introduction

AutoSpec is a Python multi-agent orchestration pipeline that transforms a single plain-English product brief, together with a run configuration, into a complete set of software artifacts with no human intervention between the start and end of a run. A single run produces (1) a structured specification document, (2) working Python source code, (3) a passing pytest test suite with one test per acceptance criterion plus pass/fail counts and line-coverage percentage, and (4) a spec-to-code alignment verdict.

The pipeline is composed of four specialised agents that execute sequentially and hand off their outputs to one another: a Spec Agent, a Build Agent, a Test Agent, and a Review Agent. The Review Agent emits an alignment verdict and, when the verdict is NOT ALIGNED, loops back to the Build Agent for a bounded number of self-correcting re-attempts. Every agent handoff is streamed to the console so the relay is observable during a live demonstration. All generated artifacts are persisted to disk.

A built-in tip-calculator brief serves as the canonical end-to-end sample run for demonstration purposes.

## Glossary

- **AutoSpec**: The complete Python orchestration pipeline that coordinates the four agents and produces all artifacts from a single brief and configuration.
- **Pipeline_Run**: A single end-to-end execution of AutoSpec, beginning with a brief and configuration and ending with a final alignment verdict.
- **Brief**: A plain-English description of a desired product or feature, supplied as the primary input to a Pipeline_Run.
- **Run_Config**: The configuration object accompanying the Brief, containing the tech-stack preference and the quality threshold.
- **Tech_Stack_Preference**: A Run_Config field selecting the target implementation language, with allowed values "Python" and "Node".
- **Quality_Threshold**: A Run_Config field specifying the target minimum line-coverage percentage (for example, 90) that a Pipeline_Run must meet to pass the quality gate.
- **Spec_Agent**: The agent that converts a Brief into a Spec_Document and writes no source code.
- **Build_Agent**: The agent that produces Generated_Code satisfying the Spec_Document and nothing beyond it.
- **Test_Agent**: The agent that produces a Test_Suite, runs the Test_Suite, and reports the Test_Report.
- **Review_Agent**: The agent that evaluates whether every Acceptance_Criterion is met by the Generated_Code and Test_Report and produces an Alignment_Verdict.
- **Spec_Document**: The structured specification artifact containing numbered requirements, each with a Given/When/Then Acceptance_Criterion, plus an Edge_Case_List.
- **Acceptance_Criterion**: A single testable statement in Given/When/Then form describing required behaviour for one requirement.
- **Edge_Case_List**: An enumerated list of boundary and exceptional conditions identified for the Spec_Document.
- **Generated_Code**: The Python source artifact produced by the Build_Agent, organised as a single application module.
- **Test_Suite**: The pytest test artifact produced by the Test_Agent, organised as a single test file, containing one test per Acceptance_Criterion.
- **Test_Report**: The artifact recording the count of passed tests, the count of failed tests, and the measured line-coverage percentage for a Pipeline_Run.
- **Coverage_Percentage**: The measured percentage of source lines in Generated_Code executed by the Test_Suite during a run.
- **Alignment_Verdict**: The Review_Agent output, equal to either "ALIGNED" or "NOT ALIGNED", accompanied by a list of unmet Acceptance_Criteria gaps when the verdict is "NOT ALIGNED".
- **Gap**: A specific unmet Acceptance_Criterion reported by the Review_Agent when the Alignment_Verdict is "NOT ALIGNED".
- **Retry_Limit**: The maximum number of times the Review_Agent may loop back to the Build_Agent within a single Pipeline_Run.
- **Quality_Gate**: The pipeline check that compares the measured Coverage_Percentage against the Quality_Threshold.
- **Demo_Brief**: The built-in tip-calculator Brief used as the canonical sample run.
- **Handoff**: The transfer of an agent's output to the next agent in the sequence.
- **Artifact_Directory**: The output location on disk where AutoSpec persists all artifacts of a Pipeline_Run.

## Requirements

### Requirement 1: Single-Input Pipeline Trigger

**User Story:** As a developer, I want to start the entire pipeline from one brief and one configuration, so that I can produce a full set of artifacts without intervening during the run.

#### Acceptance Criteria

1. WHEN a Pipeline_Run is started with a Brief and a Run_Config, THE AutoSpec SHALL execute the Spec_Agent, Build_Agent, Test_Agent, and Review_Agent in that sequential order, starting each stage only after the preceding stage has completed successfully.
2. WHILE a Pipeline_Run is executing, THE AutoSpec SHALL complete all agent stages without requesting or requiring human input.
3. WHEN all agent stages complete successfully, THE AutoSpec SHALL mark the Pipeline_Run as completed and make the produced artifact set available.
4. IF a Pipeline_Run is started without a Brief, THEN THE AutoSpec SHALL terminate the run before any stage executes, produce no artifacts, and return an error message identifying the missing Brief.
5. IF a Pipeline_Run is started without a Run_Config, THEN THE AutoSpec SHALL terminate the run before any stage executes, produce no artifacts, and return an error message identifying the missing Run_Config.
6. IF any agent stage fails to complete during a Pipeline_Run, THEN THE AutoSpec SHALL stop the remaining stages, mark the Pipeline_Run as failed, retain any artifacts produced by prior completed stages, and return an error message identifying the failed stage.

### Requirement 2: Run Configuration Validation

**User Story:** As a developer, I want the pipeline to validate my configuration before running, so that invalid settings are rejected before any artifacts are produced.

#### Acceptance Criteria

1. WHEN a Run_Config is received, THE AutoSpec SHALL validate that the Tech_Stack_Preference is a case-sensitive exact match to one of the string values "Python" or "Node".
2. IF the Tech_Stack_Preference is missing, empty, or any value other than the exact strings "Python" or "Node", THEN THE AutoSpec SHALL terminate the run, produce no artifacts, and return an error message identifying the invalid Tech_Stack_Preference value.
3. WHEN a Run_Config is received, THE AutoSpec SHALL validate that the Quality_Threshold is a numeric value greater than or equal to 0 and less than or equal to 100.
4. IF the Quality_Threshold is missing, non-numeric, or outside the range 0 to 100 inclusive, THEN THE AutoSpec SHALL terminate the run, produce no artifacts, and return an error message identifying the invalid Quality_Threshold value.
5. WHEN a Run_Config is received, THE AutoSpec SHALL complete all Run_Config field validations before producing any artifacts.
6. IF the Run_Config fails one or more field validations, THEN THE AutoSpec SHALL return an error message identifying every field that failed validation.

### Requirement 3: Spec Agent Produces Structured Specification

**User Story:** As a developer, I want the Spec Agent to turn my brief into numbered requirements with acceptance criteria and edge cases, so that downstream agents have a precise target.

#### Acceptance Criteria

1. WHEN the Spec_Agent receives a valid Brief, THE Spec_Agent SHALL produce a Spec_Document containing at least one requirement, where each requirement is labeled with a unique sequential integer starting at 1 with no gaps.
2. THE Spec_Agent SHALL include at least one Acceptance_Criterion expressed in explicit Given/When/Then form for each numbered requirement in the Spec_Document.
3. THE Spec_Agent SHALL include an Edge_Case_List containing at least one edge case in the Spec_Document.
4. THE Spec_Agent SHALL produce no source code in any field of the Spec_Document.
5. IF the received Brief is empty or contains no actionable content, THEN THE Spec_Agent SHALL produce no Spec_Document and SHALL return an error indication describing the invalid input.

### Requirement 4: Build Agent Implements Code to Spec

**User Story:** As a developer, I want the Build Agent to implement exactly what the spec describes, so that the generated code matches the requirements without scope creep.

#### Acceptance Criteria

1. WHEN the Build_Agent receives the Spec_Document, THE Build_Agent SHALL produce Generated_Code organised as a single application module containing all source artifacts under one top-level module entry point.
2. WHEN the Build_Agent receives the Spec_Document, THE Build_Agent SHALL produce Generated_Code in which every numbered requirement in the Spec_Document maps to at least one identifiable code element (function, class, or method).
3. WHERE the Tech_Stack_Preference is "Python", THE Build_Agent SHALL produce Generated_Code in the Python language.
4. THE Build_Agent SHALL limit Generated_Code to functionality that is traceable to at least one numbered requirement in the Spec_Document, and SHALL NOT include functionality that cannot be traced to any numbered requirement.
5. IF the Spec_Document contains zero numbered requirements or cannot be parsed, THEN THE Build_Agent SHALL NOT produce Generated_Code and SHALL return an error indicating the Spec_Document is invalid, leaving no partial code artifacts.

### Requirement 5: Test Agent Writes and Runs Tests

**User Story:** As a developer, I want the Test Agent to create one test per acceptance criterion and run them, so that I get objective evidence the code works.

#### Acceptance Criteria

1. WHEN the Test_Agent receives a valid Spec_Document and a valid Generated_Code, THE Test_Agent SHALL produce a Test_Suite organised as a single test file using pytest within 60 seconds.
2. IF the Spec_Document or the Generated_Code is missing or cannot be parsed, THEN THE Test_Agent SHALL abort Test_Suite production and produce an error indicating which input was missing or invalid, without producing a Test_Suite.
3. THE Test_Agent SHALL include exactly one test in the Test_Suite for each Acceptance_Criterion in the Spec_Document, and each test SHALL identify the Acceptance_Criterion it verifies.
4. WHEN the Test_Suite is produced, THE Test_Agent SHALL execute the Test_Suite against the Generated_Code.
5. IF Test_Suite execution exceeds 300 seconds, THEN THE Test_Agent SHALL terminate the execution and record each unfinished test as failed in the Test_Report.
6. WHEN the Test_Suite execution completes, THE Test_Agent SHALL produce a Test_Report containing the count of passed tests, the count of failed tests, and the measured Coverage_Percentage expressed as a value from 0 to 100.

### Requirement 6: Review Agent Produces Alignment Verdict

**User Story:** As a developer, I want the Review Agent to confirm every acceptance criterion is met and report exact gaps, so that I know whether the generated code is trustworthy.

#### Acceptance Criteria

1. WHEN the Review_Agent receives the Spec_Document, the Generated_Code, and the Test_Report, THE Review_Agent SHALL produce an Alignment_Verdict equal to exactly one of the values "ALIGNED" or "NOT ALIGNED" within 60 seconds of receiving all three inputs.
2. IF any one of the Spec_Document, the Generated_Code, or the Test_Report is missing or cannot be read, THEN THE Review_Agent SHALL withhold the Alignment_Verdict and return an error indication identifying each missing or unreadable input.
3. THE Review_Agent SHALL classify an Acceptance_Criterion as "met" only when the Test_Report contains at least one test mapped to that Acceptance_Criterion and every test mapped to that Acceptance_Criterion has a status of "passed".
4. IF every Acceptance_Criterion in the Spec_Document is met, THEN THE Review_Agent SHALL set the Alignment_Verdict to "ALIGNED".
5. IF one or more Acceptance_Criteria in the Spec_Document are not met, THEN THE Review_Agent SHALL set the Alignment_Verdict to "NOT ALIGNED".
6. WHILE the Alignment_Verdict is "NOT ALIGNED", THE Review_Agent SHALL include a list of Gaps in which each Gap identifies exactly one unmet Acceptance_Criterion by its identifier and states the observed discrepancy between the Acceptance_Criterion and the Test_Report or Generated_Code.
7. WHILE the Alignment_Verdict is "NOT ALIGNED", THE Review_Agent SHALL produce one Gap entry for every unmet Acceptance_Criterion, such that the count of Gaps equals the count of unmet Acceptance_Criteria.

### Requirement 7: Self-Correcting Retry Loop

**User Story:** As a developer, I want the pipeline to re-attempt the build when the verdict is not aligned, so that the pipeline can self-correct within a bounded number of attempts.

#### Acceptance Criteria

1. IF the Alignment_Verdict is "NOT ALIGNED" AND the number of completed re-attempts is less than the Retry_Limit of 3, THEN THE AutoSpec SHALL return control to the Build_Agent with the reported Gaps AND increment the completed re-attempt count by 1.
2. WHEN control returns to the Build_Agent for a re-attempt, THE AutoSpec SHALL re-execute the Build_Agent, Test_Agent, and Review_Agent in sequential order, starting each agent only after the preceding agent has completed.
3. THE AutoSpec SHALL limit the number of re-attempts within a single Pipeline_Run to a maximum of 3.
4. IF the Alignment_Verdict is "NOT ALIGNED" AND the number of completed re-attempts equals the Retry_Limit of 3, THEN THE AutoSpec SHALL end the Pipeline_Run and report the final Alignment_Verdict with the remaining Gaps.
5. WHEN the Alignment_Verdict is "ALIGNED", THE AutoSpec SHALL end the Pipeline_Run, report the Alignment_Verdict, and perform no further re-attempts.
6. IF the Build_Agent, Test_Agent, or Review_Agent fails to complete during a re-attempt, THEN THE AutoSpec SHALL end the Pipeline_Run, retain the Gaps from the last completed Review_Agent execution, and report an error indicating which agent failed to complete.

### Requirement 8: Observable Agent Handoffs

**User Story:** As a presenter, I want each agent's output streamed to the console, so that the relay between agents is visible during a live demo.

#### Acceptance Criteria

1. WHEN an agent completes its stage, THE AutoSpec SHALL print the complete output produced by that agent to the console before the next Handoff begins.
2. WHEN a Handoff transfers an agent's output to the next agent in the sequence, THE AutoSpec SHALL print a label that names both the agent that produced the output and the agent that receives it.
3. WHEN a re-attempt is triggered, THE AutoSpec SHALL print a message that states the re-attempt number and lists each Gap that prompted the re-attempt.
4. IF an agent stage ends without producing its expected output, THEN THE AutoSpec SHALL print an error message to the console identifying the agent that failed and end the Pipeline_Run.

### Requirement 9: Artifact Persistence

**User Story:** As a developer, I want all generated artifacts written to disk, so that I can inspect and share the results after the run.

#### Acceptance Criteria

1. WHEN the Spec_Agent produces a Spec_Document, THE AutoSpec SHALL persist the Spec_Document to the Artifact_Directory within 5 seconds such that the persisted file exists and is non-empty.
2. WHEN the Build_Agent produces Generated_Code, THE AutoSpec SHALL persist the Generated_Code to the Artifact_Directory within 5 seconds such that the persisted file exists and is non-empty.
3. WHEN the Test_Agent produces a Test_Suite, THE AutoSpec SHALL persist the Test_Suite to the Artifact_Directory within 5 seconds such that the persisted file exists and is non-empty.
4. WHEN the Test_Agent produces a Test_Report, THE AutoSpec SHALL persist the Test_Report to the Artifact_Directory within 5 seconds such that the persisted file exists and is non-empty.
5. WHEN the Review_Agent produces an Alignment_Verdict, THE AutoSpec SHALL persist the Alignment_Verdict to the Artifact_Directory within 5 seconds such that the persisted file exists and is non-empty.
6. IF the Artifact_Directory does not exist when an artifact is persisted, THEN THE AutoSpec SHALL create the Artifact_Directory before writing the artifact.
7. IF persisting an artifact fails, THEN THE AutoSpec SHALL retain the artifact in memory, return an error indication identifying which artifact failed to persist, and continue persisting the remaining artifacts without terminating the Pipeline_Run.

### Requirement 10: Quality Gate Reporting

**User Story:** As a developer, I want the pipeline to report whether the coverage threshold was met, so that I can judge the quality of the generated test suite.

#### Acceptance Criteria

1. WHEN a Test_Report is produced, THE Quality_Gate SHALL compare the measured Coverage_Percentage (a value from 0 to 100 percent) against the configured Quality_Threshold and record the comparison result in the Test_Report.
2. WHEN the measured Coverage_Percentage is greater than or equal to the Quality_Threshold, THE Quality_Gate SHALL set the Test_Report quality gate status to "met".
3. IF the measured Coverage_Percentage is less than the Quality_Threshold, THEN THE Quality_Gate SHALL set the Test_Report quality gate status to "not met".
4. IF the Coverage_Percentage cannot be measured when a Test_Report is produced, THEN THE Quality_Gate SHALL set the Test_Report quality gate status to "not met" and include an indication that coverage could not be determined, without altering any previously recorded test results.
5. IF the Quality_Threshold is not configured when a Test_Report is produced, THEN THE Quality_Gate SHALL omit the comparison and include an error indication that no Quality_Threshold is defined, without altering any previously recorded test results.

### Requirement 11: Constraints Enforced on Generated Code

**User Story:** As a developer, I want AutoSpec to enforce project rules on the generated code, so that outputs stay small, pure, and beginner-readable.

#### Acceptance Criteria

1. THE Build_Agent SHALL produce the Generated_Code as exactly one application module contained in a single source file.
2. THE Test_Agent SHALL produce the Test_Suite as exactly one test file.
3. THE Build_Agent SHALL implement the core logic of the Generated_Code as pure functions, where each pure function computes its return value solely from its input arguments, does not modify any state outside its local scope, and returns identical outputs for identical inputs.
4. THE Build_Agent SHALL produce Generated_Code whose core logic contains no database access, no network access, no file input or output operations, and no web server.
5. THE Build_Agent SHALL include a docstring on each public function in the Generated_Code, where the docstring describes the function purpose, each input parameter, and the return value.
6. IF the Generated_Code contains database access, network access, file input or output operations, or a web server, THEN THE Build_Agent SHALL reject the Generated_Code, regenerate it without the prohibited operations, and indicate that a constraint violation was detected.
7. IF a public function in the Generated_Code has no docstring, THEN THE Build_Agent SHALL add the missing docstring before finalizing the Generated_Code.

### Requirement 12: Built-In Tip-Calculator Demo Brief

**User Story:** As a presenter, I want a built-in tip-calculator brief, so that I can run a known end-to-end demonstration of the full pipeline.

#### Acceptance Criteria

1. THE AutoSpec SHALL provide a built-in Demo_Brief, expressed as a plain-English Brief, describing a tip calculator that accepts a bill total, a tip percentage, and a number of people as inputs and returns the tip amount, the total with tip, and the per-person amount as outputs.
2. THE AutoSpec SHALL provide a built-in default Run_Config for the Demo_Brief with a Tech_Stack_Preference of "Python" and a Quality_Threshold of 90, so that a Pipeline_Run started with the Demo_Brief can proceed without a separately supplied Run_Config.
3. WHEN a Pipeline_Run is started with the Demo_Brief, THE AutoSpec SHALL execute the Spec_Agent, Build_Agent, Test_Agent, and Review_Agent in that sequential order.
4. WHEN a Pipeline_Run started with the Demo_Brief completes, THE AutoSpec SHALL produce and persist to the Artifact_Directory a Spec_Document, Generated_Code, a Test_Suite, a Test_Report, and an Alignment_Verdict.

### Requirement 13: Tip-Calculator Behaviour in Generated Demo Code

**User Story:** As a developer, I want the generated tip-calculator code to compute correct values for all defined cases, so that the demo produces trustworthy results.

#### Acceptance Criteria

1. WHEN the generated tip calculator receives a bill total of 0.00 to 999,999,999.99, a tip percentage of 0 to 100, and an integer number of people greater than or equal to 1, THE generated tip calculator SHALL return the tip amount, the total with tip, and the per-person amount, each rounded to 2 decimal places using round-half-up.
2. THE generated tip calculator SHALL compute the tip amount as the bill total multiplied by the tip percentage divided by 100, and the total with tip as the bill total plus the tip amount.
3. THE generated tip calculator SHALL compute the per-person amount as the total with tip divided evenly by the number of people.
4. IF the tip percentage is 0, THEN THE generated tip calculator SHALL return a tip amount of 0.00 and a total with tip equal to the bill total.
5. IF the number of people is less than 1 or is not an integer, THEN THE generated tip calculator SHALL reject the input, return an error indication that the number of people must be an integer greater than or equal to 1, return no computed amounts, and leave the input values unchanged.
6. IF the bill total is less than 0.00 or the tip percentage is less than 0, THEN THE generated tip calculator SHALL reject the input, return an error indication that the value is out of the allowed range, return no computed amounts, and leave the input values unchanged.
