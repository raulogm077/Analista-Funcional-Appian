# Best practices — AI in Appian: agents, AI skills and document processing

> Official Appian doctrine for deciding **whether** to use AI and, when it is used, how to design AI
> agents, AI skills and intelligent document processing so they are reliable, secure and affordable.
> Every rule is anchored to `docs.appian.com/suite/help/latest/…`; verified against the 26.3 and 26.6
> pages and the 26.7–26.9 release notes. AI is the fastest-moving area of the platform, and Agent Studio
> changes almost every release: items marked **ⓥ** depend on the version — **confirm them against the
> environment** before designing around them. (DocCenter pages carry their own product version —
> `…/latest/aidc-4.4/…` —; that is their canonical path, as with RPA.)

Markers: ✅ do · ❌ avoid · ⚠️ trap · ⓥ version-dependent · ⓣ tier-dependent. Each block closes with its source.

**Contents:** 0. Guiding principle: the simplest automation that meets the need
· 1. Agent types and where they run · 2. Instructions (the prompt) · 3. Tools and resources
· 4. Cost: AI actions and the design triangle · 5. Multi-agent designs · 6. Reliability and human oversight
· 7. Security and governance · 8. Testing, monitoring and evolution · 9. Deploying agents
· 10. AI skills and intelligent document processing (IDP) · Sources

---

## 0. Guiding principle: the simplest automation that meets the need

The one question Appian asks first: **is the path to the solution unpredictable?**

| Approach | Use it for | Reliability | Cost |
|---|---|---|---|
| **Rules-based** (expression rules, decisions, process models) | Deterministic, high-volume, stable logic; strict audit; real-time response | 100 % predictable | Very low |
| **AI skill** | **One** well-defined cognitive task inside a flow you control: classify, extract, summarize, generate | High for that task | Low to medium |
| **AI agent** | Multi-step work whose next step depends on what it discovers; flexible handling of exceptions | Probabilistic | Medium (AI actions + tool calls) |

- ✅ If the path is known and repeatable → rules or a process model **with AI skills** for the cognitive steps.
- ✅ If unsure, start with a process model; introduce an agent only for the reasoning-intensive portion.
- ✅ The signal that an agent is justified: you are building complex branching and loops in a process
  model to *simulate* reasoning.
- ✅ Combine them: agents for research and judgement, AI skills for single cognitive steps, rules for
  deterministic execution, humans on exceptions.
- **Why:** an agent pays AI actions to reason on every run, even when the path turns out to be obvious.
  That cost is justified only when the path genuinely varies.

Source: [About AI Agents — Choosing the right automation approach](https://docs.appian.com/suite/help/latest/about-ai-agents.html#choosing-the-right-automation-approach) · [Understanding cost and reliability trade-offs](https://docs.appian.com/suite/help/latest/about-ai-agents.html#understanding-cost-and-reliability-trade-offs)

### 0.1 When NOT to use an agent

- ❌ The path can be written as "step 1, step 2, step 3" with no branching on discovered context —
  often it only *looks* unpredictable because the stakeholders have not agreed the workflow yet.
- ❌ A single cognitive operation (classify, extract, summarize, generate) → AI skill.
- ❌ High-volume simple tasks (validation, simple routing) → rules.
- ❌ Sub-second response required → run the agent **upstream** so its result is ready when a person needs it.
- ✅ Once in production, if the agent follows the same sequence of tool calls **85 % of the time or more**
  (the threshold in Appian's production design patterns), extract that path into a deterministic
  process model and keep the agent for the edge cases.

Source: [About AI Agents — When not to use an AI agent](https://docs.appian.com/suite/help/latest/about-ai-agents.html#when-not-to-use-an-ai-agent) · [Design Patterns for Production AI Agents — When to evolve your design](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#when-to-evolve-your-design)

---

## 1. Agent types and where they run

- ✅ **Process agent** — runs unattended inside a process model through the **Execute AI Agent** smart
  service. **Chat agent** — converses with a user through the agent chat component (`a!agentChatField`).
- ⚠️ The type is chosen at creation and **cannot be changed**; runtime validation rejects a process agent
  in the chat component and a chat agent in Execute AI Agent. Decide it in design.
- ✅ The agent replaces the **reasoning loop**, not the whole process: the process triggers it, then
  continues with deterministic steps (approvals, writes, notifications).
- ✅ Good candidates hide in **human task nodes** where someone researches several systems, reads
  unstructured text or triages by judgement before deciding.
- ⚠️ **Chat agents:** `debugMode` must be off before production; the agent chat component is **not
  supported in Appian Mobile or Appian for Windows**; conversations are scoped to the user, kept for
  audit (users can't clear them) and not transferred between environments. `showSessionPicker: false`
  limits a user to one session.

Source: [About AI Agents — Agent types](https://docs.appian.com/suite/help/latest/about-ai-agents.html#agent-types) · [Use Cases — Identify AI agent opportunities](https://docs.appian.com/suite/help/latest/agent-studio-use-cases.html#identify-ai-agent-opportunities) · [Agent Chat Component](https://docs.appian.com/suite/help/latest/agent-chat-component.html) · [Conversation persistence for chat agents](https://docs.appian.com/suite/help/latest/conversation-persistence-chat-agents.html)

---

## 2. Instructions (the prompt)

The prompt is the factor that most determines an agent's performance.

- ✅ Structure it in Markdown with four parts: **Persona** (role and tone) · **Goal** (task and expected
  outcome) · **Process guidelines** (business rules, decision criteria) · **Constraints** (what it must
  not do).
- ✅ Concise but complete; plain, direct language; state intent and outcome; numbered steps for longer
  processes.
- ✅ Define **escalation triggers** in the prompt (low confidence, policy exception, high value) and a
  safe output for edge cases — e.g. set the decision to `HOLD` with a note instead of guessing.
- ✅ For scores, use small ranges (0–10) with a qualitative definition per value; few-shot examples or
  asking for step-by-step reasoning improve consistency.
- ❌ Don't rely on the prompt for access control: prompt boundaries are behavioural; enforcement is
  Appian security (§7).

Source: [Best Practices for Designing AI Agents — Write effective instructions](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#write-effective-instructions) · [AI Agents FAQ — Designing AI agents](https://docs.appian.com/suite/help/latest/ai-agents-faq.html#designing-ai-agents) · [Tutorial: Build a Triage Agent — Best practices](https://docs.appian.com/suite/help/latest/build-triage-agent-tutorial.html#best-practices-and-considerations)

---

## 3. Tools and resources

Tools are what the agent can **do** (process models, expression rules, other agents, MCP tools, system
tools); from 26.8 the passive data it can **reference** (record types, documents, folders) is configured
separately as **Resources**, and new agents start with **no tools enabled** ⓥ.

- ✅ **One tool, one job**, and **no overlapping tools**: similar tools make the agent pick the wrong one.
  Search for existing objects before creating a new tool.
- ✅ **Only the tools the task needs.** Each extra tool costs AI actions on every run and raises the
  chance of a wrong choice; remove tools production data shows are never used. Most agents perform best
  with **fewer than 15 tools**, native and MCP counted together.
- ✅ **Dual description:** the tool object's description states technical facts (what it does, what it
  returns); the agent's instructions state **when and why** to use it.
- ✅ **Meaningful names** for tools, inputs and outputs (`customerInvoiceDoc`, `casePriorityLevel`), not
  `id`, `data`, `docID`: the model reasons over the names.
- ✅ **Process model tools:** focused on a single task, without child processes; a **record type input**
  (not a process variable) when writing records; no Write Records nodes for different record types in
  the same model (one process model per record type written); keep deterministic logic (validations, calculations, conditional flows) **inside** the process. Tools that
  read and tools that write are kept separate, so independent reads can run in parallel.
- ✅ Accept and return **arrays**: one call with a list beats N calls.
- ⚠️ **Querying records:** up to 26.6 the record type tool queries **one** record type, so joins and
  aggregations go in an **expression rule** tool; from 26.8 SQL-query and metadata system tools can join
  and aggregate across record types, respecting row- and field-level security ⓥ.
- ⚠️ An AI skill cannot be added directly as a tool; wrap it (e.g. the DocCenter extraction) in a process model.
- ⚠️ ⓥ **MCP tools (26.6):** only developers with Viewer or higher on the MCP connected system can add
  it, and the agent exposes only the tools you select; authentication is API key or OAuth 2.0 client
  credentials, and only the *tools* primitive is supported. Tools renamed or removed on the server need
  manual reconfiguration. The **Appian MCP Server** (Appian exposed to external AI clients) authenticates
  every connection as **one service account** — no per-user identity — so scope that account to the
  minimum; it works on synced record types and logs every call.

Source: [Create and Configure an AI Agent — Prepare your tools and actions](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#before-you-begin-prepare-your-tools-and-actions) · [Create and Configure — Keep it simple](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#4-keep-it-simple) · [Best Practices — Design tools for efficiency](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#design-tools-for-efficiency) · [Release notes 26.8 — tools and resources, system tools](https://docs.appian.com/suite/help/latest/Appian_Release_Notes.html#ai-agents) · [MCP tools in AI agents](https://docs.appian.com/suite/help/latest/mcp-tools-ai-agents.html#mcp-tool-security-and-access-control) · [Appian MCP Server — Security model](https://docs.appian.com/suite/help/latest/appian-mcp-server.html#security-model)

### 3.1 Run limits to design within

| Limit | Value | Source |
|---|---|---|
| Tool calls per run | **30**, then the run is *System Canceled* (adjustable through a support case) | AI Agent Reference |
| Process model tool timeout | **3 min** in 26.3 (support case to change) · **30 min**, fixed, in 26.6 ⓥ | AI Agent Reference |
| Agent node (Execute AI Agent) and sub-agent (AI agent tool) timeout | **60 min** | AI Agent Reference |
| Documents/folders as inputs | **75** per run, **50 MB** cumulative | AI Agent Reference |
| Records/primitives as inputs or outputs | **50** per variable; no nested arrays | AI Agent Reference |
| Parallel tool calls | **5** per reasoning step, extra calls queued; 26.6+, on by default ⓥ | AI Agent Reference |
| Document tools | Read Full Document: 20 pages with images / 50 text-only · Query Document: 100 pages text / 20 with images · Semantic Search: 75 documents, 50 MB, no scanned PDFs | Agent Studio documents |

Source: [AI Agent Reference — Model limitations / Working with documents / Parallel tool execution](https://docs.appian.com/suite/help/latest/ai-agent-reference.html#model-limitations) · [Working with documents in AI agents](https://docs.appian.com/suite/help/latest/agent-studio-documents.html)

---

## 4. Cost: AI actions and the design triangle

- ✅ **Pass known data as inputs** instead of making the agent fetch it with a tool every run.
- ✅ **Return Text (JSON) from process model tools** rather than record types: record metadata inflates
  the context without helping the reasoning. From 26.9 you can also **filter a process model tool's
  output** so only the values the agent needs come back ⓥ.
- ✅ Query through **expression rules** (the agent only supplies filters) rather than giving it a whole
  record type schema; give search-style agents **aggregated inputs** (counts, distributions) to aim
  their search.
- ✅ Prefer **Semantic Search** over the Read Full Document tool unless the whole document is needed.
- ✅ Decide consciously on the **AI design triangle** — accuracy, speed, AI action consumption: pick the
  primary driver, set "good enough" thresholds for the other two, then measure all three. Reserve
  extended thinking for reasoning-heavy tasks.
- ✅ Appian recommends **prioritizing accuracy over AI action cost** when in doubt: the business value of
  a correct answer usually exceeds the extra consumption. Estimate consumption per end-to-end transaction
  by summing every AI node.

Source: [Best Practices — Optimize AI action consumption](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#optimize-ai-action-consumption) · [AI Agents FAQ — Performance and cost](https://docs.appian.com/suite/help/latest/ai-agents-faq.html#ai-agent-performance-and-cost) · [Balance AI Performance and Cost](https://docs.appian.com/suite/help/latest/design-considerations.html) · [Estimating AI Action Usage](https://docs.appian.com/suite/help/latest/estimate-token-usage.html)

---

## 5. Multi-agent designs

- ✅ **Orchestrator pattern:** one agent interprets the request and delegates to specialized agents
  (research, extraction, validation), then assembles the result. Calls to other agents through the AI
  agent tool **always run one after another**, never in parallel.
- ❌ **Never more than two levels.** No child calling another child, no child calling its parent, no
  agent calling itself: infinite loops, runaway concurrency and untraceable failures. If you need more,
  the orchestrator calls each specialist directly.
- ✅ **Context passing:** start by passing **structured fields**; move to full context only if the child's
  accuracy suffers (summary-only is cheapest but loses detail).
- ✅ Within one agent, **independent** tool calls run in parallel (§3.1); design tools without shared
  state so the model can recognise them as independent. Where the order matters, say so in the instructions.

Source: [Design Patterns for Production AI Agents — Multi-agent architectures](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#main_content) · [Best Practices — Design modular AI agents for collaboration](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#design-modular-ai-agents-for-collaboration) · [AI Agent Reference — Parallel tool execution](https://docs.appian.com/suite/help/latest/ai-agent-reference.html#parallel-tool-execution)

---

## 6. Reliability and human oversight

- ⚠️ An agent **cannot pause mid-run to wait for a person**, and its tools have timeouts (§3.1). Design
  hand-offs between the agent and reviewers in the process, not inside a tool call.
- ✅ **Watchdog timer:** run Execute AI Agent in one branch and a timer in a parallel branch with the
  maximum acceptable duration; on expiry, escalate to a human queue, log, or run a simplified fallback.
- ✅ **Self-healing:** process model tools capture errors in an output variable (instead of terminating)
  and return them to the agent; the prompt says how to react to common errors.
- ✅ **Graceful degradation:** an output such as `completion_status` (complete / partial / could not
  proceed) plus what was done and why; the parent process routes partial results to a person.
- ✅ **Human oversight:** the output explains its steps and reasoning for review; route low-confidence
  or high-risk decisions to a user task.
- ✅ Call agents **synchronously** by default; asynchronous only for work that genuinely runs in parallel.
- ⚠️ **Validate what Execute AI Agent returns.** Appian doesn't check that required outputs are present;
  an output that can't be cast to its type fails the node; the node doesn't support MNI and Agent Inputs
  don't accept a list of maps. ⓥ Up to 26.6 the node returns only Agent Outputs, Run Summary and Run ID;
  from 26.8 it adds success status, error message and AI actions consumed — route on them when available.
- ⚠️ **Stop** doesn't interrupt a tool that is already running: it completes, then no further model
  calls are made (*User Canceled*). Tools with side effects must be safe to finish after a stop.
- ✅ **Retry around the agent, not only inside tools.** Intermittent `EVENT_NOT_FOUND` or `INVALID_TOOL_RESPONSE` errors come from model non-determinism, and "Input is too long" from oversized requests: give the calling process a bounded retry path, sharpen the prompt and tool names, and limit document inputs and `extraInstructions` ([KB-2396](https://community.appian.com/application-design-33/kb-2396-ai-agent-intermittently-fails-with-event-not-found-invalid-tool-response-and-input-too-long-errors-15892)).

Source: [Execute AI Agent Smart Service](https://docs.appian.com/suite/help/latest/Execute_AI_Agent_Smart_Service.html) · [Create and Configure — Stop a running AI agent](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#stop-a-running-ai-agent) · [Design Patterns — Error handling and resilience](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#error-handling-and-resilience) · [Best Practices — Design for human-in-the-loop handoffs](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#design-for-human-in-the-loop-handoffs) · [AI Agents FAQ — oversight and sync vs async](https://docs.appian.com/suite/help/latest/ai-agents-faq.html)

---

## 7. Security and governance

- ✅ **The agent runs with the initiator's permissions** (or those of the service account configured in
  the process): it only reaches records, rules and processes that identity can use, and **record-level
  security applies** to its queries. Process model tools run as the process's configured run-as user;
  sub-agents run as the main agent's initiator.
- ✅ The initiator needs permissions on **every** tool; a missing one blocks the run before it starts.
  ⚠️ The docs disagree on the level: *Create and Configure an AI Agent* asks for at least **Viewer** on
  all tools; *Deploy AI Agents* lists Viewer on record types, **Initiator** on process models and
  **Editor** on documents. Grant the stricter set and test a run in the target environment.
- ✅ In production, prefer a **dedicated service account** with exactly the permissions the agent needs:
  consistent access and an audit trail that separates agent actions from people's.
- ✅ **AI Guardrails (26.6) ⓥ:** environment-wide input/output policies in the Admin Console (AI
  Guardrails tab) against prompt injection, PII exposure and toxic content, with violation logging.
  ⚠️ **Disabled by default** — an administrator must enable them and activate each configuration. They
  don't cover Enterprise Copilot, `a!documentsChat()` or spreadsheet extraction AI skills, and they
  **complement, never replace**, object, record and field security.
- ✅ **Audit:** the AI Input/Output log (prompts and responses) is **off by default** and enabled by an
  administrator; turn it on only if the audit requirement justifies storing that content — it does
  **not mask PII**, and keeps at most **7 days** within a **100 MB** cap for all AI logs (oldest removed
  first), so export what must be kept longer.
- ✅ ⓥ **Usage Groups (26.6):** an optional list of groups (up to 100) on the Execute Generative AI Skill,
  Advanced IDP Tools and Extract from Document nodes that attributes AI action consumption to teams. It
  is for **cost attribution only** — it doesn't cap or throttle anything.
- ✅ **Model governance** (administrator) ⓥ: disable a model provider/family for compliance (26.5), route
  AI through the organization's LLM gateway (26.4), Azure OpenAI accounts for AI skills (26.6); agents
  used Appian-managed models only until 26.6 and can use linked external provider accounts from 26.7.
- ✅ Data stays in the designated region unless cross-region inference is configured, and Appian doesn't
  train models on customer data — state this in the solution's compliance section rather than assuming it.

Source: [Auditing AI agent usage](https://docs.appian.com/suite/help/latest/auditing-ai-agent-usage.html) · [Execute Generative AI Skill — Usage considerations](https://docs.appian.com/suite/help/latest/Execute_Generative_AI_Skill_Smart_Service.html#usage-considerations) · [Design Patterns — Security and permissions](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#security-and-permissions) · [Deploy AI Agents — Before you deploy](https://docs.appian.com/suite/help/latest/deploy-ai-agents.html#before-you-deploy) · [Create and Configure an AI Agent — Check access](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#before-you-begin-prepare-your-tools-and-actions) · [AI Guardrails](https://docs.appian.com/suite/help/latest/ai-guardrails.html) · [AI Agent Reference — Logging and auditing](https://docs.appian.com/suite/help/latest/ai-agent-reference.html#ai-agent-tool-behavior) · [Security and Compliance](https://docs.appian.com/suite/help/latest/security-compliance.html) · [Release notes — AI governance](https://docs.appian.com/suite/help/latest/Appian_Release_Notes.html#ai-governance)

---

## 8. Testing, monitoring and evolution

Agents are non-deterministic: the goal is **consistent quality**, not identical outputs.

- ✅ Keep a **test case library** of representative inputs with expected results, including edge cases;
  save useful runs with **Save as Test Case** and re-run the library after every prompt or tool change.
  Use repeat-safe inputs for agents with side effects.
- ✅ **Evaluate tab (26.6) ⓥ:** run the test cases in bulk, rate runs consistently (thumbs-down = not
  acceptable in production), tick the failure categories (*Wrong output, Made up information, Too many
  steps, Got stuck, Took too long, Failed to recover from error, Other*), mark several strong examples and
  compare **Overall Accuracy** between versions — a drop is a regression. Before 26.6, keep the same
  discipline with saved test cases in the Test tab.
- ✅ Build **user feedback** (thumbs up/down, comments) into the interface around agent outputs: it is the
  most valuable production signal.
- ✅ Watch the **Monitor** tab: tool calls per run, AI actions, duration, errors. Rising cost without rising
  complexity means over-reasoning; a jump in tool calls after a prompt change means ambiguity.

Source: [Best Practices — Test and iterate](https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html#test-and-iterate) · [Evaluate AI Agents](https://docs.appian.com/suite/help/latest/evaluate-ai-agents.html) · [Design Patterns — When to evolve your design](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#when-to-evolve-your-design) · [Monitor AI Agents](https://docs.appian.com/suite/help/latest/monitor-ai-agents.html)

---

## 9. Deploying agents

- ⚠️ The agent's configuration (instructions, inputs, outputs, tool list) travels with the object; **its
  tools do not** — package the process models, rules, decisions, record types, documents, folders and,
  for MCP tools, the MCP connected system.
- ✅ Remove duplicate or overlapping tools before packaging; confirm the **initiator's permissions in the
  target** for every tool; keep input/output names aligned with the consuming objects.
- ✅ After deployment: run the saved test cases and watch the first runs in Monitor.
- ✅ Tag the version in the package description (e.g. `AI agent: CaseTriage v14`) to speed up comparison
  and rollback. Agents don't retrain on deployment: their reliability is prompt, tools and testing.

- ⚠️ **AI objects in packages:** each AI skill took ~4 minutes to export when KB-2298 was written (2024), so a package with several can hit the 5-minute request limit — deploy AI skills in their own package. ⓥ From 26.6, referencing a semantic search `similarityScore` directly in a script task output breaks deployment; call the search through an expression rule. Check the DocCenter version (`AIA_VERSION` constant) on both sides before deploying DocCenter models ([KB-2298](https://community.appian.com/infrastructure-37/kb-2298-ai-skill-fails-to-import-and-or-export-1355), [KB-2395](https://community.appian.com/application-design-33/kb-2395-error-when-deploying-a-process-model-with-semantic-search-similarity-score-field-in-expression-node-output-15871), [KB-2378](https://community.appian.com/how-to-36/kb-2378-how-to-view-doccenter-version-in-appian-designer-1415)).

Source: [Deploy AI Agents Between Environments](https://docs.appian.com/suite/help/latest/deploy-ai-agents.html)

---

## 10. AI skills and intelligent document processing (IDP)

### 10.0 Running AI skills in processes

- ✅ **Execution mode:** *Standard* (default) waits up to **4.5 min** and supports activity chaining;
  *Long Running* polls instead of holding the node, allows up to **60 min** and doesn't chain. The AI skill
  **Test** button always runs Standard, so a skill that passes there can still need Long Running for real
  volumes. ⚠️ In autoscaled processes the docs give **1.5 min**, and they disagree on whether Long Running
  lifts it — verify in the environment before designing long skills into autoscale.
- ✅ ⓥ **Auto model (26.7):** `<provider>/auto` picks the model at run time, survives model deprecations
  and is the only way to get automatic fallback with third-party providers. Whatever the model, **enable
  it in the target environment before importing** the skill (the ID must match exactly; Appian only
  checks at run time).
- ⚠️ **Throughput** is managed at platform level, with no configurable concurrency: under load a node can
  get *"The AI model is currently processing too many other requests"*. For volume, use Long Running +
  autoscale, stagger process starts, and route that error to a retry.
- ✅ **Other languages:** write the core instructions in English, state the output language explicitly,
  and test with native speakers for "language bleed" (Spanish is in the best-supported tier).

Source: [Execute Generative AI Skill — Execution modes](https://docs.appian.com/suite/help/latest/Execute_Generative_AI_Skill_Smart_Service.html#execution-modes) · [AI Skill — Throughput and scaling](https://docs.appian.com/suite/help/latest/ai-skill-object.html#ai-skill-throughput-and-scaling) · [Generative AI skills — Auto model selection](https://docs.appian.com/suite/help/latest/gen-ai-skills.html#auto-model-selection) · [AI Services — Considerations when enabling AI models](https://docs.appian.com/suite/help/latest/ai-services.html#considerations-when-enabling-ai-models) · [Multiple languages](https://docs.appian.com/suite/help/latest/multiple-languages.html)

### 10.1 Choose the extraction approach, cheapest first

- ✅ Appian recommends **DocCenter** for intelligent document processing use cases.
- ✅ **In DocCenter, escalate the configuration only as far as accuracy requires:**
  1. **Text extraction** — the recommended starting point and lowest consumption, for fields that are
     plain text values (names, dates, amounts).
  2. **Visual extraction** — when any field depends on a visual element (checkboxes, signatures, stamps,
     complex tables, layout). ❌ Don't mix Visual and Text fields: it sends the document twice and
     **doubles consumption** — if one field needs Visual, use it for all.
  3. **Advanced Layout** — **a last resort**, only if Visual doesn't reach the target after prompt and
     model iteration: its consumption scales with every page, blank pages included.
- ✅ **With AI skills directly:** a Generative AI skill for simple text-heavy documents (Text only or
  Visual elements & text mode, chosen by content, not page count); the Advanced IDP Tools skill for
  structure-only tasks — indexing for smart search, signature/checkbox detection, fixed forms, and
  **confidence scores** for straight-through processing.
- ✅ Structured vs unstructured extraction differs in **language support** and **regional availability**:
  check both for the environment (Spanish is supported by both). In DocCenter, EN/FR/DE/IT/PT/ES work in
  every configuration; other languages need the Generative AI method with Visual, without bounding boxes.
- ⚠️ DocCenter (4.2+) fixes the **LLM provider per model** (extraction, classification, AI Reviewer) and
  does **not fail over** to another provider: plan for that provider's availability and limits.

Source: [DocCenter Design Considerations — Visual extraction vs Advanced Layout](https://docs.appian.com/suite/help/latest/aidc-4.4/design-considerations.html#choose-between-visual-extraction-and-advanced-layout) · [AI Skills Best Practices — Choosing the right pattern for document extraction](https://docs.appian.com/suite/help/latest/prompt-builder-best-practices.html#choosing-the-right-pattern-for-document-extraction) · [Create a Document Extraction AI Skill](https://docs.appian.com/suite/help/latest/create-skill-doc-extraction.html)

### 10.2 Build confidence and human review into the flow

- ✅ **Classify → route → extract:** Classify Documents saves type and confidence to process variables, an
  XOR routes each type to its own extraction skill, and **low confidence or failed classification goes to
  a user task** for manual review.
- ✅ **Capture rules:** set the `Confidence Threshold` input and use the `Confidence Score` output;
  verify values near the threshold with rules or a user task. Validate required fields after extraction.
- ✅ Document packets: split into pages, classify each page, then merge or send each part to its
  extraction skill; tables spanning pages are extracted per page and recombined.
- ⚠️ **DocCenter straight-through processing:** field confidence thresholds (10–90) require **Bounding
  Boxes or Advanced Layout** and aren't available for large tables; **AI Review** (moderate consumption)
  isn't available for large tables and, when looping, only checks the first 20 or 100 pages depending on
  the LLM. **Reconciliation** by users updates the accuracy metrics per field, document and model
  version; **AI-Suggested Improvements** proposes prompt changes from those outcomes at **high**
  consumption (requires Log AI Usage) — you still apply and test them.

Source: [Combine Classification and Extraction](https://docs.appian.com/suite/help/latest/combine-classification-extraction.html) · [Intelligent Document Processing — Implementation patterns](https://docs.appian.com/suite/help/latest/document-processing.html#implementation-patterns) · [DocCenter Extraction — Straight-through processing / AI Review](https://docs.appian.com/suite/help/latest/aidc-4.4/extraction.html#straight-through-processing)

### 10.3 Control DocCenter consumption and deployment

- ✅ Use **sections** for long documents, **remove unused fields**, add field instructions only where they
  measurably help, choose a fast model for high-volume structured documents and a reasoning model for
  complex ones, and enable **AI Review** only when targeting straight-through processing.
- ✅ Reach the accuracy target on representative test documents **before** processing production volume;
  monitor AI actions per instance.
- ⚠️ **Deployment:** source and target must be on the **same Appian platform version** — DocCenter doesn't
  support cross-version deployments, which matters when environments upgrade on different dates. The
  target needs DocCenter's required plug-ins and AI skills. Snapshot the models on the DocCenter
  Deployment page and include the **`AIA deployment`** document in the package; a post-deployment process
  applies it. With manual deployment that process doesn't run — trigger **RUN DEPLOYMENT** in the target.
  Model version numbers are independent per environment.
- ✅ **Limits to design within:** up to **100 fields** per model; **100 MB** per file (from DocCenter 4.3);
  **500 pages** with reconciliation, **1,000** without (Visual extraction: 100 pages before DocCenter 4.4).
- ✅ **Calling it from your app:** the `AIA Extraction Run Model Version` subprocess with `document` and
  `modelKey` (empty version = latest published). With MNI pass `pv!document[tp!instanceIndex]` and query
  the extraction results afterwards rather than relying on the subprocess output. The Subprocess node
  isn't autoscale-compatible (synchronous or asynchronous) and runs on the parent's engine: for volume or
  in autoscaled models, start it with **Start Process** (doc 03 §2).
- ✅ **Roles:** give custom apps the **AIA Initiator** role (4.3+: triggers classification, extraction and
  verification, completes reconciliation, can't edit models); **AIA Operations** to monitor; keep **AIA
  Administrators** (model editing) out of production.
- ⚠️ **Upgrades:** don't customize the DocCenter application (upgrades can overwrite it); upgrade its
  **plug-ins together with the app** (versions must match); existing model versions keep their processing
  version — validate with the test suites before moving them to the new one.

Source: [DocCenter Design Considerations — Manage AI action consumption](https://docs.appian.com/suite/help/latest/aidc-4.4/design-considerations.html#manage-doccenter-ai-action-consumption) · [DocCenter — Deploy](https://docs.appian.com/suite/help/latest/aidc-4.4/deployment.html) · [DocCenter Extraction — Model limits](https://docs.appian.com/suite/help/latest/aidc-4.4/extraction.html#extraction-model-limits) · [DocCenter — Use models in a process](https://docs.appian.com/suite/help/latest/aidc-4.4/use-models.html#add-extraction-as-a-subprocess) · [DocCenter — Install (application security)](https://docs.appian.com/suite/help/latest/aidc-4.4/install.html#step-6-configure-application-security) · [DocCenter — Upgrade](https://docs.appian.com/suite/help/latest/aidc-4.4/upgrade.html)

### 10.4 Prompts for AI skills

- ✅ Define the use case and what the model must **not** do; describe the input; specify the output format
  (JSON, list, tags); give examples; state length, tone and audience; put the most important instruction
  (output format, final question) **at the end**.
- ⚠️ LLMs are not deterministic: validate the output structure before using it downstream.

Source: [AI Skills Best Practices — Write an effective prompt](https://docs.appian.com/suite/help/latest/prompt-builder-best-practices.html#main_content)

### 10.5 Designing DocCenter extraction fields

- ✅ **Type every field** that always holds one kind of value (Number, Date, Boolean…); Text is only the
  default.
- ✅ Use an **Options Rule** for closed value sets: it constrains the output, prevents invented values and
  becomes the reconciliation dropdown. Not for free text or very large value sets.
- ✅ For complex fields and bilingual documents, let the model reason in a **scratchpad** before answering,
  combined with value options and an output schema.

Source: [DocCenter — Prompt engineering](https://docs.appian.com/suite/help/latest/aidc-4.4/prompt-engineering.html)

---

## Sources

- About AI Agents — https://docs.appian.com/suite/help/latest/about-ai-agents.html
- Use Cases (AI agents) — https://docs.appian.com/suite/help/latest/agent-studio-use-cases.html
- Best Practices for Designing AI Agents — https://docs.appian.com/suite/help/latest/agent-studio-best-practices.html
- Design Patterns for Production AI Agents — https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html
- AI Agent Reference (limits, parallel tools, logging) — https://docs.appian.com/suite/help/latest/ai-agent-reference.html
- Create and Configure an AI Agent — https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html
- AI Agents FAQ — https://docs.appian.com/suite/help/latest/ai-agents-faq.html
- Tutorial: Build a Triage Agent — https://docs.appian.com/suite/help/latest/build-triage-agent-tutorial.html
- Evaluate AI Agents — https://docs.appian.com/suite/help/latest/evaluate-ai-agents.html
- Monitor AI Agents — https://docs.appian.com/suite/help/latest/monitor-ai-agents.html
- Deploy AI Agents Between Environments — https://docs.appian.com/suite/help/latest/deploy-ai-agents.html
- AI Guardrails — https://docs.appian.com/suite/help/latest/ai-guardrails.html
- Security and Compliance (AI) — https://docs.appian.com/suite/help/latest/security-compliance.html
- Release notes (AI agents, AI governance) — https://docs.appian.com/suite/help/latest/Appian_Release_Notes.html
- Balance AI Performance and Cost (AI design triangle) — https://docs.appian.com/suite/help/latest/design-considerations.html
- Estimating AI Action Usage — https://docs.appian.com/suite/help/latest/estimate-token-usage.html
- AI Skills Best Practices & Recipes — https://docs.appian.com/suite/help/latest/prompt-builder-best-practices.html
- Create a Document Extraction AI Skill — https://docs.appian.com/suite/help/latest/create-skill-doc-extraction.html
- Combine Classification and Extraction — https://docs.appian.com/suite/help/latest/combine-classification-extraction.html
- Intelligent Document Processing — https://docs.appian.com/suite/help/latest/document-processing.html
- DocCenter Design Considerations — https://docs.appian.com/suite/help/latest/aidc-4.4/design-considerations.html
- DocCenter Deploy — https://docs.appian.com/suite/help/latest/aidc-4.4/deployment.html
- DocCenter Extraction, Use Models, Install, Upgrade, Prompt engineering — https://docs.appian.com/suite/help/latest/aidc-4.4/extraction.html · …/aidc-4.4/use-models.html · …/aidc-4.4/install.html · …/aidc-4.4/upgrade.html · …/aidc-4.4/prompt-engineering.html
- Execute AI Agent Smart Service — https://docs.appian.com/suite/help/latest/Execute_AI_Agent_Smart_Service.html
- Execute Generative AI Skill Smart Service (execution modes, usage groups) — https://docs.appian.com/suite/help/latest/Execute_Generative_AI_Skill_Smart_Service.html
- AI Skill object (throughput and scaling) — https://docs.appian.com/suite/help/latest/ai-skill-object.html
- Generative AI skills (Auto model) — https://docs.appian.com/suite/help/latest/gen-ai-skills.html · AI Services — https://docs.appian.com/suite/help/latest/ai-services.html
- Multiple languages — https://docs.appian.com/suite/help/latest/multiple-languages.html
- Agent Chat Component — https://docs.appian.com/suite/help/latest/agent-chat-component.html · Conversation persistence — https://docs.appian.com/suite/help/latest/conversation-persistence-chat-agents.html
- Working with documents in AI agents — https://docs.appian.com/suite/help/latest/agent-studio-documents.html
- MCP tools in AI agents — https://docs.appian.com/suite/help/latest/mcp-tools-ai-agents.html · Appian MCP Server — https://docs.appian.com/suite/help/latest/appian-mcp-server.html
- Auditing AI agent usage — https://docs.appian.com/suite/help/latest/auditing-ai-agent-usage.html
