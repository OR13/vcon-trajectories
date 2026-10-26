---
title: "An AI Agent Extension for Virtualized Conversations (vCon)"
abbrev: "vCon AI Agent Extension"
category: std

docname: draft-birkholz-vcon-ai-agent-extension-latest

submissiontype: IETF
number:
date:
consensus: true
v: 3
area: "Applications and Real-Time"
workgroup: "Virtualized Conversations"
keyword:
 - conversation
 - vcon
 - AI agent
 - verifiable
 - evidence
 - transparency
 - auditability
venue:
  group: "Virtualized Conversations"
  type: "Working Group"
  mail: "vcon@ietf.org"
  arch: "https://mailarchive.ietf.org/arch/browse/vcon/"

author:
 -
    fullname: Henk Birkholz
    organization: Fraunhofer SIT
    email: henk.birkholz@ietf.contact
 -
    fullname: Daniel G Petrie
    organization: SIPez LLC
    email: dan.ietf@sipez.com
 -
    fullname: Thomas McCarthy-Howe
    organization: VCONIC
    email: ghostofbasho@gmail.com
 -
    fullname: Jonathan Rosenberg
    email: jdrosen@jdrosen.net
 -
    fullname: Orie Steele
    email: orie@or13.io

contributor:
 - name: Tobias Heldt
   organization: XOR
   email: tobias@xor.tech
 - name: Thomas Fossati
   organization: NVIDIA
   email: tfossati@nvidia.com
 - name: Jaime Jimenez
   organization: Ericsson
   email: jaime@iki.fi
 - name: Jari Arkko
   organization: Ericsson
   email: jari.arkko@ericsson.com
 - name: Samuel Waymouth
   organization: AWS
   email: swaym@amazon.co.uk
 - name: Houda Labiod
   organization: Huawei Technologies France S.A.S.U.
   email: houda.labiod@huawei.com

normative:

  JSON: RFC8259
  VCON-CORE: I-D.ietf-vcon-vcon-core

informative:

  CDDL: RFC8610
  RFC9682:
  RFC9393:
  RFC6973:
  STD94:
    -: cbor
    =: RFC8949
  STD96:
    -: cose
    =: RFC9052
  RFC9360:
  RFC9597:
  RFC9334: rats-arch
  RFC9943: scitt-arch
  RFC9942: cose-receipts
  VACR: I-D.birkholz-verifiable-agent-conversations
  HOWE-AGENT-SESSION: I-D.howe-vcon-agent-session
  HOWE-PROVENANCE: I-D.howe-vcon-provenance
  ROSENBERG-RESTRUCTURE: I-D.rosenberg-vcon-restructure
  EU_AI_ACT_2024:
    title: >
      Regulation (EU) 2024/1689 (Artificial Intelligence Act)
    author:
    - org: European Parliament
    - org: Council of the European Union
    date: 2024-07
    seriesinfo:
      Official Journal of the European Union: L 2024/1689
      CELEX:: 32024R1689
    target: https://eur-lex.europa.eu/eli/reg/2024/1689/oj
  EU_CRA_2024:
    title: >
      Regulation (EU) 2024/2847 (Cyber Resilience Act)
    author:
    - org: European Parliament
    - org: Council of the European Union
    date: 2024-11
    seriesinfo:
      Official Journal of the European Union: L 2024/2847
      CELEX:: 32024R2847
    target: https://eur-lex.europa.eu/eli/reg/2024/2847/oj
  EU_NIS2_2022:
    title: >
      Directive (EU) 2022/2555 (NIS 2 Directive)
    author:
    - org: European Parliament
    - org: Council of the European Union
    date: 2022-12
    seriesinfo:
      Official Journal of the European Union: L 333
      CELEX:: 32022L2555
  ETSI_TS_104223_2025:
    title: >
      Securing Artificial Intelligence (SAI); Baseline Cyber Security Requirements for AI Models and Systems
    author:
    - org: European Telecommunications Standards Institute
    date: 2025-04
    seriesinfo:
      ETSI TS: 104 223, V1.1.1
    target: https://www.etsi.org/deliver/etsi_ts/104200_104299/104223/01.01.01_60/ts_104223v010101p.pdf
  AICPA_TSC_2017:
    title: >
      Trust Services Criteria for Security, Availability, Processing Integrity, Confidentiality, and Privacy (With Revised Points of Focus - 2022)
    author:
    - org: American Institute of Certified Public Accountants
    - org: Chartered Institute of Management Accountants
    date: 2017
    seriesinfo:
      AICPA: Trust Services Criteria
    target: https://www.aicpa-cima.com/resources/download/2017-trust-services-criteria-with-revised-points-of-focus-2022
  NIST_SP_800_53_R5:
    title: >
      Security and Privacy Controls for Information Systems and Organizations
    author:
    - org: National Institute of Standards and Technology
    date: 2020-09
    seriesinfo:
      NIST Special Publication: 800-53, Revision 5
    target: https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final
  OMB_M_21_31:
    title: >
      Improving the Federal Government's Investigative and Remediation Capabilities Related to Cybersecurity Incidents
    author:
    - org: Office of Management and Budget
    date: 2021-08
    seriesinfo:
      OMB Memorandum: M-21-31
    target: https://www.whitehouse.gov/wp-content/uploads/2021/08/M-21-31-Improving-the-Federal-Governments-Investigative-and-Remediation-Capabilities-Related-to-Cybersecurity-Incidents.pdf
  PCI_DSS_V4_0_1:
    title: >
      Payment Card Industry Data Security Standard
    author:
    - org: PCI Security Standards Council
    date: 2024-06
    seriesinfo:
      PCI DSS: Version 4.0.1
    target: https://www.pcisecuritystandards.org/document_library/
  ISO_IEC_42001_2023:
    title: >
      Information technology - Artificial intelligence - Management system
    author:
    - org: International Organization for Standardization
    - org: International Electrotechnical Commission
    date: 2023-12
    seriesinfo:
      ISO/IEC: 42001:2023
    target: https://www.iso.org/standard/42001
  FFIEC_IT_HANDBOOK_2024:
    title: >
      Information Technology Examination Handbook
    author:
    - org: Federal Financial Institutions Examination Council
    date: 2024-08
    seriesinfo:
      FFIEC: IT Examination Handbook
    target: https://ithandbook.ffiec.gov/
  BSI_AI_FINANCE_2024:
    title: >
      Test Criteria Catalogue for AI Systems in Finance
    author:
    - org: Bundesamt fuer Sicherheit in der Informationstechnik
    date: 2024
    seriesinfo:
      BSI: AI Finance Test Criteria
    target: https://www.bsi.bund.de/SharedDocs/Downloads/EN/BSI/KI/AI-Finance_Test-Criteria.pdf
  NIST_AI_100_2_E2025:
    title: >
      Adversarial Machine Learning: A Taxonomy and Terminology of Attacks and Mitigations
    author:
    - org: National Institute of Standards and Technology
    date: 2025-03
    seriesinfo:
      NIST AI: 100-2 E2025
    target: https://csrc.nist.gov/pubs/ai/100/2/e2025/final
  EMERGENT_MISALIGNMENT_2025:
    title: >
      Emergent Misalignment: Narrow finetuning can produce broadly misaligned LLMs
    author:
    - name: Jan Betley
    - name: Daniel Tan
    - name: Niels Warncke
    - name: Anna Sztyber-Betley
    - name: Xuchan Bao
    - name: Martin Soto
    - name: Nathan Labenz
    - name: Owain Evans
    date: 2025-02
    seriesinfo:
      arXiv: "2502.17424"
      PMLR: "267:4043-4068"
    target: https://arxiv.org/abs/2502.17424
  ISO_IEC_DIS_24970:
    title: >
      Artificial intelligence - AI system logging
    author:
    - org: International Organization for Standardization
    - org: International Electrotechnical Commission
    date: 2025
    seriesinfo:
      ISO/IEC DIS: "24970"
    target: https://www.iso.org/standard/88723.html

entity:
  SELF: "RFCthis"

--- abstract

A vCon is a container for data and information relating to a conversation.
This document defines an extension to the vCon core specification via the CDDL extension points provided.
The ai agent vCon extension specified in this document is in support of verifiable records of conversations with and between autonomous agents.
Autonomous agents that use large language models increasingly perform consequential tasks on behalf of humans and other agents.
Demonstrating that recorded agent behavior truthfully represents actual behavior is essential for accountability, compliance, and human oversight.
The vCon extension specified in this document captures agent trajectory and agent conversation related records, such as agent metadata, message exchanges, tool invocations, reasoning traces, system events, file attribution, etc.
This data and information about autonomous agent behaviour are recorded as parameters of vCon Objects and as new vCon Event Object types.
The data CDDL definitions originate from the former Verifiable Agent Conversation Records specification and are adapted to the extension points of the current vCon CDDL data defintition.

--- middle

# Introduction

This document adds parameters and Event Object types for autonomous agents to the vCon CDDL definition as described in {{VCON-CORE}}.
The general framework and requirements for defining an extension to vCon CDDL definition are defined in {{VCON-CORE}}.

The question of whether the recorded output of an autonomous agent faithfully represents an agent's actual behavior has found new urgency as the number of consequential tasks that are delegated to agents increases rapidly.
Autonomous Agents--typically workload instances of agentic artificial intelligence (AI) based on large language models (LLM)--interact with other actors by design.
This creates an interconnected web of agent interactions and conversations that is currently rarely supervised or recorded in a systemic manner.
In essence, the two main types of actors interacting with autonomous agents are humans and machines (e.g., other autonomous agents), or a mix of them.
In agentic AI systems, machine actors interact with other machine actors.
The number of interactions between machine actors grows significantly more than the number of interactions between human actors and machine actors.
While the responsible parties for agent actions ultimately are humans--whether a natural legal entity or an organization--agents act on behalf of humans and on behalf of other agents.
To demonstrate due diligence, responsible human parties require records of agent behavior to demonstrate policy compliant behavior for agents acting under their authority.
These increasingly complex interactions between multiple actors that can also be triggered by machines (recursively) increase the need to understand decision making and the chain of thoughts (CoT) of autonomous agents, retroactively (i.e., accountability and auditability after the fact).

The verifiable records of agent conversations that are specified in this document provide an essential basis for operators to detect divergences between intended and actual agent behavior after the interaction has concluded.

For example:

* An agent authorized to read files might invoke tools to modify production systems or exfiltrate sensitive data beyond its authorization scope.

* An agent's visible CoT output might diverge from the reasoning that actually produced its actions.

* An agent might deliberately underperform during capability evaluations while performing at full capacity during deployment.

This document defines conversation records extensions for vCon representing activities of autonomous agents such that long-term preservation of the evidentiary value of such records across chains of custody (CoC) is possible.

This document defines vCon extensions that integrate verifiable records of agent conversations as a building block into vCon towards seven dedicated goals:

1. The first goal is to assure that the recording of an agent conversation (a distinct segment of the interaction with an autonomous agent) being proffered is the same as the agent conversation that actually occurred.

2. The second goal is to provide a general structure of agent conversations that can represent most common types of agent conversation frames, is extensible, and allows for future evolution of agent conversation complexity and corresponding actor interaction.

3. The third goal is to use existing IETF building blocks to present believable evidence about how an agent conversation is recorded utilizing Evidence generation as laid out in the Remote ATtestation ProcedureS architecture {{-rats-arch}}.

4. The fourth goal is to use existing IETF building blocks to render conversation records auditable after the fact and enable non-repudiation as laid out in the Supply Chain Integrity, Transparency, and Trust architecture {{-scitt-arch}}.

5. The fifth goal is to enable detection of behavioral anomalies in agent interactions, including unauthorized tool invocations, inconsistencies between reasoning traces and actions, and performance modulation across evaluation and deployment contexts, through structured, comparable conversation records.

6. The sixth goal is to enable cross-vendor interoperability by defining a common representation for agent conversations that can be translated from multiple existing agent implementations with distinct native formats.

7. The seventh goal is to produce records suitable for demonstrating compliance with emerging regulatory requirements for AI system documentation, traceability, and human oversight.

Most agent conversations today are represented in "human-readable" text formats.
For example, JSON {{JSON}} is considered to be "human-readable" as it can be presented to humans in human-computer-interfaces (HCI) via off-the-shelf tools, e.g., pre-installed text editors that allow such data to be consumed or modified by humans.
A vCon is a JSON document, and so are the agent conversation records extensions defined in this document.
The signed and the encrypted forms of a vCon defined in {{VCON-CORE}} apply unchanged.
The application of COSE {{-cose}} to vCons that carry agent conversation vCon records is described in the SCITT architecture {{scitt-cose}}.

## Transition from Verifiable Agent Conversation Records to a vCon extension

The data definitions in this document originate from the stand-alone Verifiable Agent Conversation Records specification {{VACR}}.
This Internet-Draft rebuilds them as an extension of the vCon CDDL definition.
Each high level part of a Verifiable Agent Conversation Record is assigned to one of the extension points that {{VCON-CORE}} defines as CDDL {{CDDL}} sockets, and the sections of this document follow these extension points.
CDDL definitions that are used by more than one extension point are collected in {{reusable}} after the sections for the extension points.
{{mapping}} maps each data item of {{VACR}} to its place in this document.

The vCon concepts of Session and Event that this extension builds upon were proposed to accommodate AI agent conversations in {{ROSENBERG-RESTRUCTURE}}.
{{HOWE-AGENT-SESSION}} and {{HOWE-PROVENANCE}} describe related approaches that carry agent session data and generation provenance in a vCon.

Editor's Note:
: The assignment of each part of a Verifiable Agent Conversation Record to a vCon extension point is preliminary.
Each section that defines parameters for an extension point lists alternatives that are still open for discussion.

Editor's Note:
: This document is based on the editor's copy of {{VCON-CORE}} (CDDL syntax version 0.5.0), which introduces the Session Object and the Event Object.
Sections of {{VCON-CORE}} are therefore referenced by name and not by number.

# Conventions and Definitions

{::boilerplate bcp14-tagged}

In this document, CDDL {{CDDL}} {{RFC9682}} is used to describe the data formats of agent conversations in the JSON form accodring to vCon CDDL definitions.

## Terminology

See the Terminology section of {{VCON-CORE}} for terminology used in this document.

The following terms are used in this document:

Agent:
: An autonomous software system, typically based on a large language model, that is represented by a Party Object and that produces messages, invokes tools, and produces reasoning.

Agent Session:
: A session of an agent, represented by a Session Object.

Entry:
: A discrete, system-recorded event of an agent session in the native format of an agent implementation, such as a message, a tool call, a tool result, a reasoning step, or a system event.
In a vCon, an entry is represented by a Dialog Object or by an Event Object.

Recording Agent:
: The tool or agent that generates the vCon, as distinct from the agent that conducted the conversation.

# Extension Name {#extension-name}

The extension name for this document is "ai_agent".

The string token "ai_agent" SHOULD be included in the extensions parameter of a vCon that contains any of the parameters or Event Object types defined in this document.
As described in {{compatibility}} and {{incompatibility}}, this extension is intended to be fully interoperable with the vCon definitions and the name "ai_agent" is not inlcuded as a critical parameter.

# Parameter Definitions

This section defines the parameters and Event Object types of the "ai_agent" extension.
There is one subsection for each extension point of {{VCON-CORE}} that this extension uses.
Each subsection contains the CDDL that plugs into the corresponding socket of the vCon CDDL.
New Objects are defined in the subsection of the extension point at which they are introduced.

The Verifiable Agent Conversation Record of {{VACR}} is a top-level container for all data produced by or about an agent conversation.
In this extension, the vCon Object is that container.
The uuid parameter of the vCon Object identifies the record, and the created_at parameter of the vCon Object provides the time the record was generated.
The extension name in the extensions parameter replaces the schema version string, as the extension mechanism of {{VCON-CORE}} replaces schema versioning.
The record unifies two complementary perspectives: the agent session captures how code was produced (the full conversation replay), while file attribution captures what code was produced (which files were modified and by whom).

## Extension Points Defined by this Document {#extension-points}

Each Object defined in this document that does not allow arbitrary additional members ends with a CDDL group socket, so that other extensions can add parameters to it.
Each Event Object type defined in this document also ends with a CDDL group socket.
The following CDDL group sockets are defined in this document.

| Object | CDDL Socket | Defined in |
| --- | --- | --- |
| File_Attribution | `$$file-attribution-ext` | {{file_attribution}} |
| File | `$$file-ext` | {{file_attribution}} |
| File_Conversation | `$$file-conversation-ext` | {{file_attribution}} |
| Range | `$$range-ext` | {{file_attribution}} |
| Contributor | `$$contributor-ext` | {{file_attribution}} |
| Resource | `$$resource-ext` | {{file_attribution}} |
| "tool-call" type Event Object | `$$tool-call-event-ext` | {{event-type-tool-call}} |
| "tool-result" type Event Object | `$$tool-result-event-ext` | {{event-type-tool-result}} |
| "reasoning" type Event Object | `$$reasoning-event-ext` | {{event-type-reasoning}} |
| "system-event" type Event Object | `$$system-event-ext` | {{event-type-system-event}} |
{: #tbl-extension-points title="CDDL Group Extension Points Defined by this Document"}

Editor's Note:
: The Recording_Agent, Agent_Meta, Environment, Token_Usage, and VCS_Context Objects allow arbitrary additional members (`* tstr => any`), as in {{VACR}}.
Whether these Objects get a CDDL group socket in addition to or instead of this wildcard is for further discussion.

## vCon Object Parameters {#vcon-object-parameters}

This extension adds the following parameters to the vCon Object, using the vcon-ext socket:

~~~ cddl
{::include cddl/ai-agent-vcon.cddl}
~~~
{: #fig-cddl-vcon title="CDDL for the ai_agent Parameters of the vCon Object"}

Editor's Note:
: Alternative placements for recording_agent are a Party Object that represents the recording tool and the Attachment Object.
An alternative placement for file_attribution is the Attachment Object, as proposed in {{HOWE-AGENT-SESSION}}.

### recording_agent {#recording_agent}

The recording_agent parameter identifies the tool or agent that generated this vCon, as distinct from the agent that conducted the conversation.
This distinction matters for provenance chains: the recording tool's version affects how native data is translated into the canonical data definition specified in this document.

* recording_agent: "Recording_Agent" (optional)

The Recording_Agent Object contains the following members:

name:
: The name of the recording tool or agent.

version:
: The version of the recording tool.

### vcs {#vcs}

The vcs parameter provides version control metadata at the record level (repository, branch, revision).

* vcs: "VCS_Context" (optional)

The VCS_Context Object is defined in {{vcs_context}}.

### file_attribution {#file_attribution}

NOTE: This section is specified but not yet validated against real session data.
Implementation or validation against a healthy example corpus is pending.

File attribution captures what code was produced: which files were modified, which line ranges were changed, and who authored them.

* file_attribution: "File_Attribution" (optional)

The File_Attribution Object is the top-level container for file attribution data.
It holds an array of files, each with their attributed line ranges and contributor information.

files:
: Array of File Objects with attributed ranges.

`$$file-attribution-ext`:
: A CDDL socket that can be used to extend the File_Attribution Object.
  See {{extension-points}}.

A File Object represents a single source file that was modified during the conversation.
It groups all conversations that contributed changes to this file.

path:
: The file path relative to the repository root.

conversations:
: The conversations that contributed modifications to this file, as an array of File_Conversation Objects.

`$$file-ext`:
: A CDDL socket that can be used to extend the File Object.
  See {{extension-points}}.

A File_Conversation Object links a specific session to the line ranges it produced in a file.
This enables tracing from a line of code back to the conversation that generated it.

url:
: A URL pointing to the conversation source (e.g., a web UI permalink).

contributor:
: The default contributor for all ranges in this conversation.
  Can be overridden per-range.

ranges:
: The line ranges in the file that were produced by this conversation.

related:
: External resources related to this conversation (e.g., issue trackers, documentation).

`$$file-conversation-ext`:
: A CDDL socket that can be used to extend the File_Conversation Object.
  See {{extension-points}}.

A Range Object identifies a contiguous block of lines in a file that were produced by a specific conversation.
Line numbers are 1-indexed and inclusive.
The optional content hash enables position-independent tracking when lines move due to later edits.

start_line:
: The first line of the range (1-indexed).

end_line:
: The last line of the range (1-indexed, inclusive).

content_hash:
: A hash of the range content for position-independent identification.

content_hash_alg:
: The hash algorithm used (default: "sha-256").

contributor:
: Overrides the conversation-level contributor for this specific range.

`$$range-ext`:
: A CDDL socket that can be used to extend the Range Object.
  See {{extension-points}}.

A Contributor Object identifies who authored a range of code.
The type member distinguishes between human-authored, AI-generated, mixed, and unknown authorship.

type:
: The authorship category.

model_id:
: The model identifier for AI-authored ranges.

`$$contributor-ext`:
: A CDDL socket that can be used to extend the Contributor Object.
  See {{extension-points}}.

A Resource Object represents an external reference related to a conversation, such as an issue tracker entry, a pull request, or a documentation page.

type:
: The resource type (e.g., "issue", "pr", "documentation").

url:
: The URL of the resource.

`$$resource-ext`:
: A CDDL socket that can be used to extend the Resource Object.
  See {{extension-points}}.

Editor's Note:
: The content_hash member of the Range Object is not a ContentHash as defined in {{VCON-CORE}}.
Aligning both is for further discussion.

## Party Object Parameters {#party-object-parameters}

This extension adds the following parameter to the Party Object, using the party-ext socket:

~~~ cddl
{::include cddl/ai-agent-party.cddl}
~~~
{: #fig-cddl-party title="CDDL for the ai_agent Parameters of the Party Object"}

Editor's Note:
: Alternative placements for agent_meta are the Session Object and the generation provenance of {{HOWE-PROVENANCE}}.

### agent_meta {#agent_meta}

The agent_meta parameter identifies the coding agent and language model that a Party Object represents.
Agent identification is essential for provenance tracking: knowing which model produced which output enables auditing, capability assessment, and compliance verification.
The type parameter of a Party Object that contains agent_meta SHOULD be "bot".

* agent_meta: "Agent_Meta" (optional)

The Agent_Meta Object contains the following members:

model_id:
: The primary language model identifier, using the naming convention of the provider (e.g., "claude-opus-4-5-20251101", "gemini-2.0-flash").

model_provider:
: The provider of the primary model (e.g., "anthropic", "google", "openai").

models:
: List of all model identifiers used during the session.
  Relevant for multi-model sessions where the agent switches between models.

cli_name:
: The name of the CLI tool or agent framework (e.g., "claude-code", "gemini-cli", "codex-cli").

cli_version:
: The version of the CLI tool.

## Session Object Parameters {#session-object-parameters}

An agent session is represented by a Session Object.
It captures the full conversation between a user and an autonomous agent.
The Dialog Objects and Event Objects that are part of the Session Object represent messages, tool invocations, reasoning steps, and system events.
Together, they preserve the complete interaction history including all native agent metadata, enabling both replay and audit of the conversation.
The start parameter of the Session Object provides the time the agent session began, and the duration parameter provides the time until the agent session ended.
An agent that spawns sub-agents is represented by a Session Object that references the Session Objects of the sub-agents using the Session_Reference type "child", as described for AI agents in {{VCON-CORE}}.

This extension adds the following parameters to the Session Object, using the session-ext socket:

~~~ cddl
{::include cddl/ai-agent-session.cddl}
~~~
{: #fig-cddl-session title="CDDL for the ai_agent Parameters of the Session Object"}

### agent_session_id {#agent_session_id}

The agent_session_id parameter contains an opaque string uniquely identifying the agent session in the native format of the agent implementation.
Values may be UUID v4, UUID v7, SHA-256 hashes, or other formats.
The agent_session_id parameter is distinct from the session_id parameter of the Session Object, which contains a SessionId Object.

* agent_session_id: "String" (optional)

### format {#format}

The format parameter classifies the session style, such as "interactive" (human-in-the-loop) or "autonomous" (fully automated).
Informative only; does not change the structure.

* format: "String" (optional)

### environment {#environment}

The environment parameter captures execution context for the conversation: where the agent was running, what version control state was active, and whether sandboxing was in effect.
This context is important for reproducibility and for understanding the scope of file modifications.

* environment: "Environment" (optional)

The Environment Object contains the following members:

working_dir:
: The primary working directory path.
  File paths in tool calls are typically relative to this directory.

vcs:
: Version control state at the time of the session (branch, revision, etc.), as a VCS_Context Object ({{vcs_context}}).

sandboxes:
: Paths to sandbox mount points.
  Some agents run in sandboxed environments where the working directory is a temporary mount.

## Dialog Object Parameters {#dialog-object-parameters}

A message of an agent session represents a conversational turn: either human input or agent response.
This is the most common entry type, carrying the primary dialog content of a session.
A message is represented by a "text" type Dialog Object.
The parties parameter of the Dialog Object references the Party Object of the contributor of the message.
Human (or upstream agent) input is contributed by the Party Object of the user, and an agent response is contributed by the Party Object of the agent.
The message body is contained in the Dialog Content.
For assistant messages, additional metadata may be present: the model that generated the response and token usage statistics.

This extension adds the following parameters to the Dialog Object, using the dialog-ext socket:

~~~ cddl
{::include cddl/ai-agent-dialog.cddl}
~~~
{: #fig-cddl-dialog title="CDDL for the ai_agent Parameters of the Dialog Object"}

Editor's Note:
: An alternative placement for model_id and token_usage is the generation provenance of {{HOWE-PROVENANCE}}.

### model_id {#model_id}

The model_id parameter identifies the model that generated this response.
Present on assistant messages, absent on user messages.

* model_id: "String" (optional)

### token_usage {#token_usage}

The token_usage parameter captures token consumption metrics for a model response.
Token usage data is essential for cost tracking, quota management, and understanding model behavior.
All members are optional because different agents report different subsets of token metrics.

* token_usage: "Token_Usage" (optional)

Editor's Note: add a non-empty generic here

The Token_Usage Object contains the following members:

input:
: The number of input tokens consumed by this response.

output:
: The number of output tokens generated.

cached:
: The number of input tokens served from cache rather than reprocessed.

reasoning:
: Tokens consumed by chain-of-thought or reasoning computation.

total:
: The total token count.

cost:
: The monetary cost in US dollars for this response.

### entry_id and parent_id

The entry_id parameter contains the unique identifier of this entry within the session.
The parent_id parameter references the parent entry, enabling tree-structured conversations.
Both are defined in {{agent_entry_reference}}.

* entry_id: "String" (optional)
* parent_id: "String" (optional)

## Event Object Types and Parameters {#event-object-types}

This extension defines four Event Object types representing the kinds of entries in an agent conversation that are not messages.
They are added using the event-type-ext socket.
Each type ends with a socket of its own, so that other extensions can add parameters to it.

~~~ cddl
{::include cddl/ai-agent-event.cddl}
~~~
{: #fig-cddl-event title="CDDL for the ai_agent Event Object Types"}

For all four types, the time parameter provides when the entry occurred, the session parameter references the Session Object of the agent session, and the party parameter references the Party Object of the agent.
The entry_id and parent_id parameters ({{agent_entry_reference}}) preserve the native entry identifiers and the tree structure of the agent trace.

Editor's Note:
: An alternative placement for the agent trace is a single Analysis Object that carries the trace, as proposed in {{HOWE-AGENT-SESSION}}.
It is also an open question whether the "tool-call" and "reasoning" Event Object types apply to human parties.

### tool-call {#event-type-tool-call}

A "tool-call" type Event Object represents a tool invocation: which tool was called and with what arguments.
Tool calls are central to agent conversation records because tool use is the primary mechanism by which agents interact with external environment.

tool_name:
: The tool name (e.g., "Bash", "Edit", "Read", "apply_patch").

input:
: The arguments passed to the tool, preserved in their native structure.

call_id:
: Links this call to its corresponding result.

`$$tool-call-event-ext`:
: A CDDL socket that can be used to extend the "tool-call" type Event Object.
  See {{extension-points}}.

### tool-result {#event-type-tool-result}

A "tool-result" type Event Object represents the output returned by a tool after execution.
It is linked to its corresponding "tool-call" type Event Object via the call_id parameter.
The result carries the tool's response data and optional status metadata indicating success or failure.

output:
: The tool's response, preserved in native structure.

call_id:
: Links this result to its corresponding call.

status:
: Outcome status of the tool execution, such as "success", "error", or "completed".

is_error:
: Boolean error flag, present when the tool execution failed.

`$$tool-result-event-ext`:
: A CDDL socket that can be used to extend the "tool-result" type Event Object.
  See {{extension-points}}.

### reasoning {#event-type-reasoning}

A "reasoning" type Event Object captures CoT, thinking, or internal reasoning content from the agent.
Not all agents expose reasoning traces.
When they do, the content may be plaintext, structured blocks, or encrypted.
Reasoning entries are valuable for auditing decision-making processes and understanding why an agent took particular actions.

content:
: The reasoning text or structured content.
  May be an empty string when only encrypted content is available.

encrypted:
: Encrypted reasoning content.
  Used where the model provider encrypts chain-of-thought output.

subject:
: A topic label for the reasoning block.

`$$reasoning-event-ext`:
: A CDDL socket that can be used to extend the "reasoning" type Event Object.
  See {{extension-points}}.

### system-event {#event-type-system-event}

A "system-event" type Event Object records system lifecycle events that are not part of the conversation dialog but are relevant for understanding the session context.
Examples include session start and end markers, token usage summaries, permission changes, and configuration events.

event_type:
: Classifies the event, such as "session-start", "session-end", "token-count", or "permission-change".
  The values are not enumerated in the schema to accommodate vendor-specific event types.

data:
: Event-specific payload.
  The structure varies by event type.

`$$system-event-ext`:
: A CDDL socket that can be used to extend the "system-event" type Event Object.
  See {{extension-points}}.

### Event Object Parameter Applicability by Type

The following table summarizes which Event Object parameters apply to each Event Object type defined in this document.
The symbols used in the table are the ones used in {{VCON-CORE}}: M the parameter MUST be present, O the parameter is optional, X the parameter MUST NOT be present.

| Parameter | tool-call | tool-result | reasoning | system-event |
| --- | --- | --- | --- | --- |
| type | M | M | M | M |
| time | M | M | M | M |
| session | M | M | M | M |
| party | M | M | M | M |
| dialog | X | X | X | X |
| button, transferee, transfer_target, consultation, target_session | X | X | X | X |
| tool_name | M | X | X | X |
| input | M | X | X | X |
| call_id | O | O | X | X |
| output | X | M | X | X |
| status | X | O | X | X |
| is_error | X | O | X | X |
| content | X | X | M | X |
| encrypted | X | X | O | X |
| subject | X | X | O | X |
| event_type | X | X | X | M |
| data | X | X | X | O |
| entry_id | O | O | O | O |
| parent_id | O | O | O | O |
{: #tbl-event-applicability title="Event Object Parameter Applicability for the ai_agent Event Object Types"}

## Reusable Definitions {#reusable}

The CDDL definitions in this section are used by more than one of the extension points above.

~~~ cddl
{::include cddl/ai-agent-common.cddl}
~~~
{: #fig-cddl-common title="CDDL for Definitions Used by More Than One Extension Point"}

### VCS_Context Object {#vcs_context}

The VCS_Context Object captures version control metadata for reproducibility.
Knowing the exact repository, branch, and commit at the time of a conversation enables consumers to reconstruct the codebase state and verify file attributions.
It is used by the vcs parameter of the vCon Object ({{vcs}}) and by the Environment Object of the Session Object ({{environment}}).

type:
: The version control system type (e.g., "git", "jj", "hg", "svn").

revision:
: The commit SHA or change identifier at session time.

branch:
: The active branch name.

repository:
: The repository URL.

### Agent Entry Reference {#agent_entry_reference}

Agent implementations identify each entry of their native trace and arrange entries in a tree.
The entry_id and parent_id parameters preserve this structure in the Dialog Objects ({{dialog-object-parameters}}) and the Event Objects ({{event-object-types}}) of an agent session.

entry_id:
: A per-entry unique reference within a session, enabling parent-child linking.

parent_id:
: References the parent entry, enabling tree-structured conversations.
  Entries that the native format nests inside another entry reference that entry in parent_id.

# Compatibility Considerations {#compatibility}

This extension is Compatible as defined in {{VCON-CORE}}.

The parameters added by this extension to the vCon Object (recording_agent, vcs, file_attribution), to the Party Object (agent_meta), to the Session Object (agent_session_id, format, environment), and to the Dialog Object (model_id, token_usage, entry_id, parent_id) are new and optional.
None of them changes the meaning, structure, or permitted values of any parameter defined in {{VCON-CORE}}.
An implementation that does not recognize these parameters can therefore continue to process the vCon correctly by ignoring them.

The Event Object types added by this extension ("tool-call", "tool-result", "reasoning", "system-event") are values that an implementation that does not support this extension does not recognize.
As defined in {{VCON-CORE}}, such an implementation ignores these Event Objects, and they remain in the events array so that indexes are not changed.
The effect is that the agent trace is not processed, while the messages of the agent session, which are Dialog Objects, are processed as usual.
This does not make the extension Incompatible.

# Incompatibility Considerations {#incompatibility}

This extension introduces no incompatibilities.
All parameters and Event Object types defined in this document are new and additive.
None of them changes the semantics, structure, or permitted values of any parameter defined in {{VCON-CORE}}.
Because no incompatibility is introduced, the "ai_agent" extension name is not required to appear in the critical parameter.

A redactor that does not support this extension cannot assess the content of the parameters and Event Object types defined in this document, which can carry PII (see {{privacy}}).
As described in {{VCON-CORE}}, such a redactor may reject a vCon that lists "ai_agent" in the extensions parameter.

# Privacy and Integrity Considerations {#privacy}

Verifiable agent conversation records reveal substantial information about agent behavior, system state, and user interactions.
The privacy considerations of {{RFC6973}} apply.

## Information Disclosure

User prompts captured in Dialog Objects may contain personal identifiers, business confidential information, credentials inadvertently included in prompts, or behavioral patterns.
Agent responses and reasoning traces may reveal inference results that expose information about users not explicitly provided, confidential information retrieved by tools, or system architecture details through tool names and parameters.
Implementations MUST treat user-provided content as potentially containing personally identifiable information.

Record metadata exposes operational details that may have privacy implications.
Model identifiers reveal AI capabilities, CLI versions enable targeted attacks against known vulnerabilities, working directories expose file system structure, and VCS context discloses repository names and commit timing.
Token usage patterns may enable inference about conversation content even when the content itself is protected.

## Sensitive Content in Records

Reasoning entries may contain inferences that constitute special category data, including health-related inferences from user queries, political opinions derived from conversation context, or biometric data processed by AI systems.
The encrypted parameter of the "reasoning" Event Object type reflects that some model providers encrypt chain-of-thought content; when reasoning is encrypted, audit capabilities depend on the provider's cooperation.

Tool inputs and outputs warrant particular attention.
Tool call inputs may contain credentials, API keys, or file contents.
Tool results may contain query results with personal data from databases or external services.
Implementations SHOULD provide configurable redaction rules for common patterns and support selective entry type recording based on deployment requirements.

## Redaction and De-identification

The input parameter of "tool-call" type Event Objects, the output parameter of "tool-result" type Event Objects, the content and encrypted parameters of "reasoning" type Event Objects, and the data parameter of "system-event" type Event Objects can carry party-identifying data or PII.
The same applies to the Dialog Content of the Dialog Objects that represent messages, to the working_dir and sandboxes members of the Environment Object, and to the path and url members of the File_Attribution Object.
A redactor is expected to handle these parameters like Dialog Content, using the redacted parameter of {{VCON-CORE}}.
A redactor that removes an Event Object entirely leaves a placeholder in the events array, so that indexes in other Objects do not change.

## External References

This extension does not add url and content_hash parameters for externally referenced files as defined in {{VCON-CORE}}, and therefore introduces no new externally referenced content.
The url members of the File_Conversation Object and of the Resource Object are references to related resources and not content of the vCon.
They are not protected by a content_hash.

## Retention Considerations

Multiple frameworks impose retention requirements that may conflict with data minimization principles.
Organizations must balance compliance obligations requiring extended retention against privacy principles requiring timely deletion.

Compliant data management may require separating raw personal data from audit trail metadata, implementing automated deletion for personal data after compliance-minimum periods, and maintaining cryptographic commitments enabling verification without retaining content.

## Correlation and Inference

Presentations of the same record to multiple parties can be correlated by matching on the signature component.
Session identifiers enable linking of records across time, potentially revealing long-term behavioral patterns or organizational structure.
Implementations SHOULD use unlinkable session identifiers where correlation is not required.

Without accessing record content, observers may infer conversation frequency and duration patterns, types of tools used, error rates, or timing correlations with external events.
Metadata exposure in unprotected headers warrants careful consideration; the trace-metadata in the COSE unprotected header ({{scitt-cose}}) reveals session identifiers, agent vendor, and timestamps even when the payload is encrypted.

## Authority Access

Regulatory frameworks may require provision of records to authorities upon request.
Access to records has to be logged, capturing who accessed which records, when access occurred, what legal basis justified access, and what data was disclosed.
This creates a recursive consideration: access logs may themselves contain personal data requiring protection.

# Security Considerations

The security considerations of {{VCON-CORE}} apply.

## Record Integrity

The signed form of a vCon {{VCON-CORE}} and the signed-agent-record envelope ({{scitt-cose}}) provide cryptographic integrity protection for the serialized record payload.
A valid signature establishes that the claimed signer produced the record but does not guarantee the truthfulness of its contents.
Modifications to the record structure after signing invalidate the signature, but modifications before signing cannot be detected.
Implementations generating records incrementally during a conversation MUST sign only after the conversation concludes or at defined checkpoints.

## Signing Key Protection

The security of signed records depends critically on the protection of private signing keys.
If an attacker obtains a signing key, they can forge records indistinguishable from genuine ones.
Protection mechanisms range from operating system process isolation in development environments to hardware security modules with physical tampering resistance in high-assurance deployments.
Compromised signing keys require rejection of records signed after the compromise date and notification to Relying Parties.

Key provisioning processes must guarantee that exclusively valid attestation key material is established.
Off-device key generation requires confidentiality protection during transmission, creating recursive security dependencies.
On-device key generation eliminates transmission risks but requires chain-of-custody integrity to prevent attackers from obtaining endorsement for keys they control.

## Timestamp Integrity

Timestamps establish temporal ordering of events within records.
Attackers who can manipulate timestamps can backdate records, freeze participants in chosen time periods to evade freshness checks, or manipulate perceived temporal relationships between entries.
Timestamps within records are attested by the signer, not independently verified.
Implementations requiring independent timestamp verification SHOULD use external timestamping services or transparency logs such as those defined in {{-scitt-arch}}.

## Adversarial Content

Processing verifiable agent conversation records involves parsing content that may be produced by adversaries.
This applies both to user-supplied prompts and to model outputs that may have been influenced by adversarial inputs.
The open extensibility (`* tstr => any`) in the Objects defined in this document allows arbitrary additional fields; implementations MUST NOT assume that unrecognized fields are safe to process or display.

Records may contain content designed to exploit downstream systems.
Malicious prompts preserved in records may execute if records are subsequently processed by AI systems.
Tool results may contain executable content that executes if rendered unsafely in web interfaces.
File paths in tool calls or file attribution entries may attempt directory traversal.
Implementations MUST apply appropriate sanitization before rendering content, executing it in agent contexts, or using paths for file system operations.

## Non-Repudiation

The signed form of a vCon and the signed-agent-record envelope alone provide authenticity and integrity, not non-repudiation.
A signer can claim key compromise or dispute the signing time without independent evidence.
Non-repudiation requires additional infrastructure such as transparency services {{-scitt-arch}} that provide independent timestamp proof via registration receipts, append-only logs preventing retroactive denial, and third-party witnesses to the signing event.

## Detection and Trust Boundaries

Verifiable agent conversation records primarily enable detection of anomalous behavior rather than prevention.
Detection requires that records accurately reflect actual agent behavior; an agent that controls its own recording can omit or falsify entries.
The recording_agent parameter distinguishes the recording tool from the conversing agent, enabling Relying Parties to assess trust in the recording process.

Trust boundaries exist between the agent runtime and recording system, between the recording system and storage, between storage and verification, and between verification and decision-making.
Attacks at any boundary may compromise record integrity or confidentiality.

# IANA Considerations

## vCon JSON Registry Additions

### vCon Extensions Names Registry

The following extension name is added to the vCon Extensions Names Registry.

| Extension Name | Extension Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| ai_agent | AI Agent conversation records | IESG | [](#extension-name) RFC XXXX |

### vCon Object Parameter Names Registry

The following defines additional values for the vCon Object Parameter Names Registry.

| Parameter Name | Parameter Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| recording_agent | tool that generated the record | IESG | [](#recording_agent) RFC XXXX |
| vcs | record-level version control context | IESG | [](#vcs) RFC XXXX |
| file_attribution | attribution of modified files | IESG | [](#file_attribution) RFC XXXX |

### Party Object Parameter Names Registry

The following defines additional values for the Party Object Parameter Names Registry.

| Parameter Name | Parameter Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| agent_meta | agent and model metadata | IESG | [](#agent_meta) RFC XXXX |

### Session Object Parameter Names Registry

The following defines additional values for the Session Object Parameter Names Registry.

| Parameter Name | Parameter Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| agent_session_id | native agent session identifier | IESG | [](#agent_session_id) RFC XXXX |
| format | agent session style | IESG | [](#format) RFC XXXX |
| environment | agent execution environment | IESG | [](#environment) RFC XXXX |

### Dialog Object Parameter Names Registry

The following defines additional values for the Dialog Object Parameter Names Registry.

| Parameter Name | Parameter Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| model_id | model that generated the response | IESG | [](#model_id) RFC XXXX |
| token_usage | token consumption metrics | IESG | [](#token_usage) RFC XXXX |
| entry_id | native agent entry identifier | IESG | [](#agent_entry_reference) RFC XXXX |
| parent_id | native agent parent entry identifier | IESG | [](#agent_entry_reference) RFC XXXX |

### Event Object Parameter Names Registry

The following defines additional values for the Event Object Parameter Names Registry.

| Parameter Name | Parameter Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| tool_name | name of the invoked tool | IESG | [](#event-type-tool-call) RFC XXXX |
| input | tool arguments | IESG | [](#event-type-tool-call) RFC XXXX |
| call_id | tool call and result correlation | IESG | [](#event-type-tool-call) RFC XXXX |
| output | tool output | IESG | [](#event-type-tool-result) RFC XXXX |
| status | tool execution status | IESG | [](#event-type-tool-result) RFC XXXX |
| is_error | tool execution error flag | IESG | [](#event-type-tool-result) RFC XXXX |
| content | reasoning content | IESG | [](#event-type-reasoning) RFC XXXX |
| encrypted | encrypted reasoning content | IESG | [](#event-type-reasoning) RFC XXXX |
| subject | reasoning topic label | IESG | [](#event-type-reasoning) RFC XXXX |
| event_type | system event classifier | IESG | [](#event-type-system-event) RFC XXXX |
| data | system event payload | IESG | [](#event-type-system-event) RFC XXXX |
| entry_id | native agent entry identifier | IESG | [](#agent_entry_reference) RFC XXXX |
| parent_id | native agent parent entry identifier | IESG | [](#agent_entry_reference) RFC XXXX |

### Event Type Name Registry

The following defines additional values for the Event Type Name Registry.

| Event Type Name | Event Type Description | Change Controller | Specification Document(s) |
| --- | --- | --- | --- |
| tool-call | agent tool invocation | IESG | [](#event-type-tool-call) RFC XXXX |
| tool-result | agent tool result | IESG | [](#event-type-tool-result) RFC XXXX |
| reasoning | agent reasoning | IESG | [](#event-type-reasoning) RFC XXXX |
| system-event | agent system lifecycle event | IESG | [](#event-type-system-event) RFC XXXX |

### New Object Parameter Names Registries

Editor's Note:
: {{VCON-CORE}} recommends requesting a parameter names registry for each new Object.
This extension defines the Recording_Agent, File_Attribution, File, File_Conversation, Range, Contributor, Resource, Agent_Meta, Environment, Token_Usage, and VCS_Context Objects.
The registries will be requested once the assignment of these Objects to extension points is settled.

--- back

# Compliance Requirements for AI Agent Conversation Records

This section identifies the intersection of logging, traceability, and record-keeping requirements across major compliance frameworks applicable to AI systems.
The verifiable agent conversation format defined in this document addresses these requirements by providing a standardized, cryptographically verifiable record of AI agent interactions.

## Applicable Requirement Frameworks

The following frameworks were analyzed for their requirements on AI agent traceability and session logging:

| Framework | Jurisdiction | Sector | Status |
|-----------|-------------|--------|--------|
| EU AI Act {{EU_AI_ACT_2024}} | EU | Cross-sector | In force Aug 2024 |
| Cyber Resilience Act {{EU_CRA_2024}} | EU | Products with digital elements | In force Dec 2024 |
| NIS2 Directive {{EU_NIS2_2022}} | EU | Essential/important entities | Transposed Oct 2024 |
| ETSI TS 104 223 {{ETSI_TS_104223_2025}} | EU/International | AI systems | Published Apr 2025 |
| SOC 2 Trust Services Criteria {{AICPA_TSC_2017}} | US/International | Service organizations | Active |
| FedRAMP {{NIST_SP_800_53_R5}} {{OMB_M_21_31}} | US | Federal cloud services | Active |
| PCI DSS {{PCI_DSS_V4_0_1}} | International | Payment card industry | Mandatory Mar 2025 |
| ISO/IEC 42001 {{ISO_IEC_42001_2023}} | International | AI management systems | Published 2023 |
| FFIEC IT Handbook {{FFIEC_IT_HANDBOOK_2024}} | US | Financial institutions | Updated 2024 |
| BSI AI Finance Test Criteria {{BSI_AI_FINANCE_2024}} | Germany | Financial sector AI | Published 2024 |
| NIST AI 100-2 {{NIST_AI_100_2_E2025}} | US | Cross-sector | Published 2025 |

## Common Requirements Intersection

The analysis of the frameworks listed above results in eleven categories of requirements that appear across ALL or MOST frameworks.
These categories frame and represent a minimum baseline that verifiable agent conversation records MUST support.

### REQ-1: Automatic Event Logging

All frameworks require automatic, system-generated logging of events without reliance on manual recording.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12 | "High-risk AI systems shall technically allow for the automatic recording of events (logs)" |
| ETSI TS 104223 5.4.2-1 | "System Operators shall log system and user actions" |
| SOC 2 CC7.2 | "Complete and chronological record of all user actions and system responses" |
| FedRAMP AU-12 | "Audit Record Generation" control requirement |
| PCI DSS 4.0 Req 10 | "Audit logs implemented to support detection of anomalies" |
| ISO 42001 A.6.2.8 | "AI system recording of event logs" |

Mapping to this specification:
The Dialog Objects and Event Objects of a Session Object capture all events automatically.
Each of them represents a discrete, system-recorded event with structured metadata.

### REQ-2: Timestamp Requirements

Most frameworks require precise temporal information for each logged event.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12(2) | "Precise timestamps for each usage session" (biometric systems) |
| PCI DSS 4.0 Req 10.6 | "Time-synchronization mechanisms support consistent time settings" |
| SOC 2 | "When the activity was performed via timestamp" |
| NIS2 | "Precise logging of when an incident was first detected" |

Mapping to this specification:
The start parameter of each Dialog Object and the time parameter of each Event Object use the Date type of {{VCON-CORE}}, which is an RFC 3339 string, ensuring interoperability across implementations.

### REQ-3: Actor Identification

Most frameworks require some attribution of actions to identifiable actors (human or system).
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12(3)(d) | "Identification of the natural persons involved in the verification of results" |
| SOC 2 | "The process or user who initiated the activity (Who)" |
| PCI DSS 4.0 | Attribution to "Who" performed each action |
| FedRAMP AC-2 | Account management and identification |

Mapping to this specification:
The `contributor` type captures actor attribution with `type` (human/ai/mixed/unknown) and optional `model_id`.
The `agent_meta` parameter of the Party Object identifies the AI system.

### REQ-4: Action/Event Type Recording

All frameworks require recording of what action or event occurred.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12 | "Events relevant for identifying situations that may result in...risk" |
| ETSI TS 104223 5.2.4-3 | "Audit log of changes to system prompts or other model configuration" |
| SOC 2 | "The action they performed such as file transferred, created, or deleted (What)" |
| PCI DSS 4.0 | "What" component of audit trail |

Mapping to this specification:
The `type` parameter of Dialog Objects and Event Objects discriminates event types: `text` (messages), `tool-call`, `tool-result`, `reasoning`, `system-event`.

### REQ-5: Input/Output Recording (AI-Specific)

All AI-specific frameworks require recording of inputs (prompts) and outputs (responses).
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12(3)(c) | "The input data for which the search has led to a match" |
| PCI DSS AI Guidance | "Logging should be sufficient to audit the prompt inputs and reasoning process" |
| ETSI TS 104223 5.1.2-3 | "Operation, and lifecycle management of models, datasets and prompts" |
| FFIEC VII.D | "Lack of explainability...unclear how inputs are translated into outputs" |

Mapping to this specification:

- `text` Dialog Object contributed by the user: User/system input (prompt)
- `text` Dialog Object contributed by the agent: Model response
- `tool-call` Event Object `input`: Tool invocation parameters
- `tool-result` Event Object `output`: Tool execution results
- `reasoning` Event Object `content`: Chain-of-thought (where available)

### REQ-6: Retention Period Requirements

Most frameworks specify minimum retention periods for audit logs.
Explicit requirements are listed as follows:

| Framework | Minimum Retention |
|-----------|-------------------|
| EU AI Act Art. 19 | 6 months (longer for financial services) |
| FedRAMP (M-21-31) | 12 months active + 18 months cold storage |
| PCI DSS 4.0 | 12 months total, 3 months immediate access |
| NIS2 | Per member state law |

Recommendation:
Implementations SHOULD retain verifiable agent conversation records for at least 12 months to satisfy the most common requirement threshold.

### REQ-7: Tamper-Evidence and Integrity Protection

All frameworks require some protection against unauthorized modification of logs.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| PCI DSS 4.0 Req 10.5 | "Tamper-proof audit trails...logs cannot be altered retroactively" |
| FedRAMP | "Effective chain of evidence to ensure integrity" |
| SOC 2 | Log integrity as security control |
| CRA | "Tamper-proof SBOMs and vulnerability disclosures" |

Mapping to this specification:
The signed form of a vCon and the `signed-agent-record` type (COSE_Sign1 envelope, {{scitt-cose}}) provide cryptographic integrity protection.
The `content-hash` field in `trace-metadata` enables verification of payload integrity.

### REQ-8: Incident Response Support

All frameworks require some logs to support incident investigation and response.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| NIS2 Art. 23 | 24-hour initial notification, 72-hour assessment |
| CRA | 24-hour vulnerability notification to ENISA |
| ETSI TS 104223 5.4.2-1 | Logs for "incident investigations, and vulnerability remediation" |
| FedRAMP | Incident reporting and continuous monitoring |

Mapping to this specification:
The structured format enables rapid extraction of relevant entries by timestamp range, event type, or tool invocation for incident reconstruction.

### REQ-9: Anomaly and Risk Detection Support

All frameworks require some logs to enable detection of anomalous or risky behavior.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12(2)(a) | "Identifying situations that may result in...risk" |
| ETSI TS 104223 5.4.2-2 | "Detect anomalies, security breaches, or unexpected behaviour" |
| FedRAMP SI-4 | "Anomaly detection" |
| SOC 2 | "Anomaly detection" for security monitoring |

Mapping to this specification:
The standardized entry types and structured `tool-call`/`tool-result` pairs enable automated analysis for detecting:

- Unusual tool invocation patterns
- Failed operations (via `status` and `is_error` fields)
- Unexpected reasoning patterns
- Token usage anomalies

### REQ-10: Human Oversight Enablement

All AI-specific frameworks require logs to support human review and oversight.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 26(5) | "Monitoring the operation of high-risk AI systems" |
| ETSI TS 104223 5.1.4-1 | "Capabilities to enable human oversight" |
| ISO 42001 | Human responsibility and accountability |
| FFIEC VII.D | "Dynamic updating...challenges to monitoring and independently reviewing AI" |

Mapping to this specification:
The `reasoning` Event Object type captures chain-of-thought content (where available), enabling human reviewers to understand AI decision-making processes.
The `entry_id` and `parent_id` fields and the hierarchy of Session Objects preserve conversation structure.

### REQ-11: Traceability and Reproducibility

All frameworks require some ability to trace system behavior and reconstruct events.
Explicit requirements are listed as follows:

| Framework | Requirement |
|-----------|-------------|
| EU AI Act Art. 12 | "Level of traceability of the functioning...appropriate to the intended purpose" |
| ISO 42001 | "Traceability" as key factor including "data provenance, model traceability" |
| CRA | "Traceability in the software supply chain" |
| ETSI TS 104223 5.2.1-2 | "Track, authenticate, manage version control" |

Mapping to this specification:

- Session Object and `agent_session_id`: Links entries to sessions
- `entry_id` and `parent_id`: Enables conversation tree reconstruction
- `vcs_context`: Git commit/branch for code state
- `agent_meta`: Model version and CLI version
- `file_attribution`: Code provenance tracking

## Framework-Specific Requirements

### EU AI Act (High-Risk Systems) {#eu-ai-act-high-risk}

For AI systems classified as high-risk under Annex III of the EU AI Act {{EU_AI_ACT_2024}}, additional requirements apply:

1. Biometric identification systems (Annex III, 1(a)) require logging of:
   - Precise timestamps for start/end of each usage session
   - Reference database used during input data validation
   - Input data leading to matches
   - Natural persons involved in result verification

2. Log retention: Minimum 6 months; financial services may require longer per sector-specific regulation.

3. Authority Access: Art. 19 of {{EU_AI_ACT_2024}} requires provision of logs to competent authorities upon reasoned request.

### ETSI TS 104 223 Session Logging Requirements {#etsi-logging}

ETSI TS 104 223 {{ETSI_TS_104223_2025}} provides the most detailed AI-specific logging requirements:

| Provision | Requirement | This Spec Mapping |
|-----------|-------------|-------------------|
| 5.1.2-3 | Audit trail for "operation, and lifecycle management of models, datasets and prompts" | Session Object, `agent_meta` |
| 5.2.4-1 | "Document and maintain a clear audit trail of their system design" | `recording_agent`, open maps |
| 5.2.4-3 | "Audit log of changes to system prompts or other model configuration" | `system-event` Event Object with prompt changes |
| 5.4.2-1 | "Log system and user actions to support security compliance, incident investigations" | Dialog Objects and Event Objects |
| 5.4.2-2 | "Analyse their logs to ensure...desired outputs and to detect anomalies" | Structured format enables analysis |
| 5.4.2-3 | "Monitor internal states of their AI systems" | `reasoning` Event Object, `token_usage` |

### PCI DSS AI-Specific Guidance {#pci-dss-ai}

The PCI Security Standards Council has published guidance on AI in payment environments {{PCI_DSS_V4_0_1}}:
"Where possible, logging should be sufficient to audit the prompt inputs and reasoning process used by the AI system that led to the output provided."

This specification directly addresses this requirement through:

- `text` Dialog Object contributed by the user: Captures prompt inputs
- `reasoning` Event Object: Captures chain-of-thought (where available)
- `text` Dialog Object contributed by the agent: Captures model outputs
- `tool-call` / `tool-result` Event Objects: Captures agentic actions

### Financial Sector Requirements (FFIEC, BSI) {#financial-sector}

Financial institutions face additional scrutiny for AI systems per {{FFIEC_IT_HANDBOOK_2024}} and {{BSI_AI_FINANCE_2024}}:

| Requirement Area | FFIEC | BSI AI Finance |
|------------------|-------|----------------|
| Explainability | "Lack of transparency or explainability" risk | Test criteria for explainability |
| Dynamic updating | "Challenges to monitoring and independently reviewing AI" | Continuous validation |
| Audit trail | Log management (VI.B.7) | Complete audit trail |

## Compliance Mapping Table

The following table maps this specification's data elements to compliance requirements:

| Data Element | EU AI Act | ETSI 104223 | SOC 2 | FedRAMP | PCI DSS | ISO 42001 | NIS2 |
|--------------|-----------|-------------|-------|---------|---------|-----------|------|
| `start` / `time` | Art. 12(2) | 5.4.2-1 | CC7.2 | AU-8 | 10.6 | A.6.2.8 | Art. 23 |
| `agent_session_id` | Art. 12 | 5.2.4-1 | CC7.2 | AU-3 | 10.2 | A.6.2.8 | - |
| `type` | Art. 12(2) | 5.4.2-1 | CC7.2 | AU-3 | 10.2 | A.6.2.8 | - |
| `contributor` | Art. 12(3)(d) | 5.1.4 | CC6.1 | AC-2 | 10.2 | A.6.2.8 | - |
| Dialog Content | Art. 12(3)(c) | 5.1.2-3 | - | - | AI Guide | - | - |
| `reasoning` | Art. 12 | 5.4.2-3 | - | - | AI Guide | A.7.1 | - |
| `tool-call` / `tool-result` | Art. 12 | 5.4.2-1 | CC7.2 | AU-12 | 10.2 | A.6.2.8 | - |
| `signed-agent-record` | Art. 19 | 5.2.4-1.2 | CC6.1 | AU-9 | 10.5 | - | - |
| `vcs_context` | - | 5.2.1-2 | - | CM-3 | - | A.6.2.8 | - |
| `token_usage` | - | 5.4.2-4 | - | - | - | - | - |

## Security Requirements addressing Regulatory Compliance

### Log Integrity

Per PCI DSS {{PCI_DSS_V4_0_1}} Req 10.5 and FedRAMP {{NIST_SP_800_53_R5}} AU-9, logs MUST be protected against modification.
Implementations SHOULD:

1. Use the signed form of the vCon or the `signed-agent-record` envelope ({{scitt-cose}}) for cryptographic integrity
2. Store the `content-hash` for offline verification
3. Implement write-once storage for log archives

### Access Control

Per FedRAMP {{NIST_SP_800_53_R5}} AC-3 and ETSI {{ETSI_TS_104223_2025}} 5.2.2-1, access to logs MUST be controlled:

1. Logs containing sensitive prompts or outputs require access control
2. Reasoning content may contain confidential information
3. Authority access (EU AI Act Art. 19) requires audit of log access itself

### Data Protection

Logs may contain personal data subject to GDPR/privacy regulations:

1. Dialog Content of `text` Dialog Objects may contain PII
2. `output` of `tool-result` Event Objects may contain query results with PII
3. Retention periods must balance compliance requirements with data minimization

## Related Standards and Emerging Work

The ISO/IEC JTC 1/SC 42 committee is developing {{ISO_IEC_DIS_24970}}, a draft international standard specifically addressing AI system logging requirements.
This work aligns with and complements the verifiable agent conversation format defined in this document.

Research on emergent misalignment {{EMERGENT_MISALIGNMENT_2025}} demonstrates that narrow fine-tuning can produce broadly misaligned LLMs, underscoring the importance of comprehensive conversation logging for detecting behavioral anomalies that may not be apparent from individual interactions.

# Application of SCITT and COSE for Transparency and Authenticity {#scitt-cose}

The signed form of a vCon {{VCON-CORE}} uses JWS.
This appendix describes a signing envelope that provides cryptographic integrity protection for vCons that carry agent conversation records using COSE_Sign1 ({{STD96}}), which is encoded in CBOR {{STD94}}.
The vCon is the payload of the envelope, and the content type header parameter carries the media type "application/vcon" defined in {{VCON-CORE}}.
This makes a signed agent record a Signed Statement that can be registered with a SCITT Transparency Service {{-scitt-arch}}.
No extension point of the vCon schema is used by the envelope.
The reader is assumed to be familiar with the vocabulary and concepts defined in {{-rats-arch}} and {{-scitt-arch}}.

Editor's Note:
: The use of COSE and SCITT for vCons is expected to progress together with the SCITT related vCon work.

The collated CDDL definition for the envelope is specified as follows:

~~~ cddl
{::include-fold cddl/ai-agent-cose.cddl}
~~~
{: #fig-cddl-cose title="CDDL for the Signed Agent Record Envelope"}

## The signed-agent-record Structure

A `signed-agent-record` is a COSE_Sign1 envelope (CBOR Tag 18) that wraps a vCon with a cryptographic signature.
Signing provides data provenance and tamper evidence, satisfying some requirements of RATS Evidence generation ({{-rats-arch}}) and SCITT auditability ({{-scitt-arch}}) requirements.
The payload may be included or detached (null); in detached mode, the vCon is supplied separately during verification.

The following describes each element of this structure.

protected:
: The serialized protected header containing the algorithm identifier, content type, and CWT claims {{RFC9597}}.

unprotected:
: The unprotected header carrying trace metadata at label 100 and, after registration, the receipts {{-cose-receipts}} of a SCITT Transparency Service.

payload:
: The serialized vCon bytes, or null for detached payloads.

signature:
: The cryptographic signature over the protected header and payload.

The x5chain and x5t header parameters are defined in {{RFC9360}}.

## The trace-metadata Map {#trace-metadata}

The `trace-metadata` type carries summary information about the signed record in the COSE_Sign1 unprotected header.
This enables consumers to inspect key properties of a signed record without deserializing the full payload.

The following describes each member of this map.

session-id:
: The session identifier from the signed record.

agent-vendor:
: The agent provider name (e.g., "anthropic", "google").

trace-format:
: Identifies the format of the signed payload (e.g., "ietf-vac-v3.0" for canonical records).

timestamp-start:
: When the session began.

timestamp-end:
: When the session ended.

content-hash:
: SHA-256 hex digest of the payload bytes, enabling integrity checking independent of the COSE signature.

content-hash-alg:
: The hash algorithm used (default: "sha-256").

Editor's Note:
: The label 100 for trace-metadata is a placeholder.
A COSE Header Parameter registration is for further discussion.

# Mapping of Verifiable Agent Conversation Record Data Items {#mapping}

The following table maps the data items of {{VACR}} to their representation in this document.

| VACR data item | vCon representation | Extension point |
| --- | --- | --- |
| verifiable-agent-record | vCon Object | (core) |
| version | extensions parameter, "ai_agent" | (core) |
| id | uuid parameter | (core) |
| created | created_at parameter | (core) |
| recording-agent | recording_agent parameter | vcon-ext |
| vcs | vcs parameter | vcon-ext |
| file-attribution | file_attribution parameter | vcon-ext |
| session-trace | Session Object | (core) |
| session-id | agent_session_id parameter | session-ext |
| format | format parameter | session-ext |
| session-start | start parameter | (core) |
| session-end | duration parameter | (core) |
| environment | environment parameter | session-ext |
| agent-meta | agent_meta parameter of the agent Party Object | party-ext |
| entries | Dialog Objects and Event Objects of the Session Object | (core) |
| message-entry | "text" type Dialog Object | (core) |
| message-entry model-id | model_id parameter | dialog-ext |
| token-usage | token_usage parameter | dialog-ext |
| tool-call-entry | "tool-call" type Event Object | event-type-ext |
| tool-call-entry name | tool_name parameter | event-type-ext |
| tool-result-entry | "tool-result" type Event Object | event-type-ext |
| reasoning-entry | "reasoning" type Event Object | event-type-ext |
| event-entry | "system-event" type Event Object | event-type-ext |
| timestamp | start (Dialog Object) or time (Event Object) parameter | (core) |
| id, parent-id | entry_id, parent_id parameters | dialog-ext, event-type-ext |
| children | parent_id parameter of the nested entries | dialog-ext, event-type-ext |
| abstract-timestamp | Date ({{VCON-CORE}}) | (core) |
| signed-agent-record | {{scitt-cose}} | (none) |
| trace-metadata | {{scitt-cose}} | (none) |
{: #tbl-mapping title="Mapping of VACR Data Items"}

All other member names of {{VACR}} are converted from kebab-case to snake_case, as required by {{VCON-CORE}}.
The CDDL in {{scitt-cose}} is not part of the vCon schema and is used as in {{VACR}}.
The media type "application/agent-conversation", the CoAP Content-Format, and the CBOR Tag requested by {{VACR}} are not needed, as a vCon uses the media type "application/vcon".

Editor's Note:
: The Event Object of {{VCON-CORE}} requires the time parameter, while the timestamp of an entry in {{VACR}} is optional.
The epoch milliseconds form of abstract-timestamp is not supported by the Date type of {{VCON-CORE}}.

# Example vCons

The following (artificailly created) example is an unsigned vCon of a short coding agent session.
A user asks a question, the agent reasons, reads a file using a tool, and answers.

~~~ json
{::include-fold examples/ai-agent-session.vcon.json}
~~~
{: #fig-example title="Example vCon with an Agent Session"}

# CDDL for the ai_agent Extension

This appendix provides a {{CDDL}} definition for the parameters defined by the ai_agent extension.
The text in the preceding sections of this document defines the normative definition of these parameters.
If the CDDL provided below differs from that in the text of the preceding sections, the text is the definitive definition and the CDDL below is to be considered incorrect.

This CDDL extends the vcon-ext, party-ext, session-ext, dialog-ext, and event-type-ext sockets of the vCon CDDL of {{VCON-CORE}}.
It is to be used together with the vCon CDDL, which comes first so that its first rule is the root of the combined definition.
The fragments below are the same ones that are included in the preceding sections, in the order in which they are included by the main CDDL file of this extension, which starts with the root rule "vcon-with-ai-agent = vcon" and includes the vCon CDDL first.

~~~ cddl
{::include-fold cddl/ai-agent-vcon.cddl}

{::include-fold cddl/ai-agent-party.cddl}

{::include-fold cddl/ai-agent-session.cddl}

{::include-fold cddl/ai-agent-dialog.cddl}

{::include-fold cddl/ai-agent-event.cddl}

{::include-fold cddl/ai-agent-common.cddl}
~~~
{: #fig-cddl-collated title="Collated CDDL for the ai_agent Extension"}

Editor's Note:
: A JSON schema for the ai_agent extension will be added.

# Acknowledgments
{:numbered="false"}
