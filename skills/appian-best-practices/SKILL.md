---
name: appian-best-practices
description: Official Appian best practices, solution-design decisions and quality gates for designing, building, reviewing and debugging Appian applications. Use when orienting or designing an Appian solution or architecture, and when creating, changing, reviewing or debugging record types, data models, relationships, sync, record events, SAIL interfaces, expression rules, decisions, process models, integrations, Web APIs, sites, security, performance, deployment packages, test cases, translations, offline forms, AI agents, AI skills or document extraction — via an MCP server or in Appian Designer. Also use when diagnosing an Appian error or production symptom, or maintaining a live application (runbooks and known issues from Appian's Community Knowledge Base). Use before any write to an Appian environment and before declaring an object finished. Not for functional analysis, user stories, a project's technical specification, process diagrams or prototypes: the plugin's analyst, diagram and prototype skills lead those.
---

# Appian development best practices

Official Appian doctrine anchored to `docs.appian.com/suite/help/latest/…`, a decision map for orienting
solutions, and the **quality gates** that separate "the object exists" from "the object is professional."
Tool-agnostic: it applies the same way through an MCP server as in Appian Designer.

**This skill supplies the HOW (how to work well in Appian). The project supplies the WHAT** (which app,
which objects, which conventions, which requirements). Don't mix the two planes: when you need a fact
about the project, discover it (see *Discovering Project Context*); never assume or invent it.

**Markers in the references:** ✅ do · ❌ avoid · ⚠️ trap · ⓥ version-dependent · ⓣ tier-dependent
(Advanced/Premium) · **[engineering]** general engineering doctrine with no Appian page (doc 11). Baseline:
checked against the 26.3 and 26.6 documentation and the release notes up to 26.9; each ⓥ names its release.

## Two modes

| The task is… | Start with | Output |
|---|---|---|
| **Orienting a solution** — "how should we build X", architecture, choosing objects, reviewing a design | `references/00-solution-decisions.md`, then only the domain docs the decisions touch | Each decision with **why (source) · alternative rejected · risk · tier/version dependency · what to verify** |
| **Building or changing objects** | The calibration table below, then the domain doc(s) and the gates | The change plus a verdict per applicable gate |

In both modes, capabilities marked tier- or version-dependent are confirmed against the environment
before a design relies on them (`00` lists them).

## Calibrate the effort to the change

The most expensive mistake in a quality guide is applying all of it to everything.

| The change… | Procedure |
|---|---|
| Is cosmetic or local and touches no data, permissions or queries (text, spacing, a label) | Cardinal Rules + gate 1 (platform correctness) — the only verdict recorded. Don't open the reference docs. |
| Creates or modifies an object without exposing new data or changing authorization | The doc for its domain + the applicable gates (`10`). |
| **Writes data, exposes information, changes permissions, queries at volume, or uses AI** | Domain docs + `10` + `11` (reliability) and full verification. |
| Is architecture, a new data model, an integration with an external system, or an AI design | Add `00` and the documentary validation for high-risk decisions (see *Tools*). |

When in doubt between two rows, go up one. What is **never** graded down: an invalid reference, an
authorization gap and a non-idempotent write block any change. And the effort itself is proportional: an
ordinary change is done inline, without fanning out parallel reviews.

**Not every FAIL blocks the same way.** Platform correctness and security block the close outright.
Functional behavior, interfaces and operations block once and then become recorded debt. Performance and
maintainability are contextual — *measure before optimizing* — and never block: they're recorded with an
owner. The table is in `10`; its point is that a matter of style can't consume a remediation cycle.

## Routing by Domain

Paths relative to this skill. **Open only what the task touches**; a typical change touches 1–3 docs.
To read one section instead of a whole doc: `python3 scripts/seccion.py 06` lists its headings and
`python3 scripts/seccion.py 06 5.3` prints §5.3.

| You are going to… | Read |
|---|---|
| **Orient a solution: which mechanism for which need** | `references/00-solution-decisions.md` |
| Model tables, record types, relationships, sync and sync failures, deletes, custom fields, CDTs, documents, record events, record lists and user filters, views, stored procedures, Cloud database | `references/01-data-model-records.md` |
| Build interfaces: SAIL, forms, inputs, buttons, file upload, record actions, grids, export, charts, layouts, accessibility, translations, offline forms | `references/02-interfaces-sail.md` |
| Build process models: subprocesses, task assignment, exceptions, MNI, email, activity chaining, messaging, timers, instances in flight (process upgrade, edit, pause, cancel) | `references/03-processes.md` |
| Write expression rules, logic, null-safety, `a!match`/`a!forEach`, Decisions, constants, test cases, date and decimal traps | `references/04-expression-rules.md` |
| Touch anything with a performance impact (queries, grids, processes, reports, limits) | `references/05-performance.md` |
| Set groups, object security, record/field-level security, service accounts, portals, AI identity | `references/06-security.md` |
| Connect systems: connected systems, integrations, Web APIs, RPA | `references/07-integrations.md` |
| Name, structure, package, deploy, test, version | `references/08-alm-testing-naming.md` |
| Build sites, pages, navigation, branding | `references/09-sites-navigation.md` |
| **Declare anything finished (Definition of Done)** | `references/10-quality-gates.md` |
| **Anything that writes, calls out or reaches production: concurrency, idempotency, retries, observability, negative security tests, rollback and per-environment configuration, plug-in governance** | `references/11-reliability-operations.md` |
| Decide on or design AI: agents, chat agents, MCP tools, AI skills (execution modes, models), DocCenter, guardrails, AI cost | `references/12-ai-agents-and-skills.md` |
| **Diagnose or maintain a live app: an error message, a symptom, Cloud operations** (symptom → cause → action, from Appian's Community Knowledge Base) | `references/13-maintenance-runbooks.md` |

`10` applies to anything declared finished (in proportion to the change); `11`'s idempotency and
concurrency sections, to anything that writes data or calls out, and its operational-readiness gate to
releases that reach production; `00`, to every design conversation; `13`, whenever something already
fails or a review asks what breaks in production.

## Discovering Project Context

These rules are generic; the project governs its own territory. Before creating or modifying anything,
find out **only what the task needs**, in this order, stopping as soon as you have the answer:

1. **What is already in context** (what the user said, files already read). Don't re-query it.
2. **Project instructions and documentation**, if they exist: `CLAUDE.md`/`AGENTS.md`, README,
   specification, architecture decisions, functional design. Don't assume they exist or how they're named.
   In a project of this plugin they are `analisis/tecnico.md` (*Entorno*, *Convenciones* and the `DT-nn`
   decisions) and `analisis/funcional.md` (the approved requirements `HU-nn` and process steps `ACT-nn`).
3. **The real objects**, when the implementation matters more than the documentation (see *Tools*).

What you almost always need before creating an object: **the naming convention** and **where it fits**
(app, folder, prefix). If it isn't documented, infer it from existing objects of the same type. A
reasonable local convention **overrides the generic preference of these docs** — consistency within an
app is worth more than canonical style. If it conflicts with security or platform validity, say so
instead of perpetuating it.

❌ **Don't explore the entire application "for context."** Modifying an interface doesn't justify
inventorying every record type, process and integration. Widen the context when a real dependency shows up.

## Requirements

Before the first task: `python3 <skill>/../../requisitos.py --skill appian-best-practices` (`<skill>` is this file's
folder; on Windows, `python`). It says what this machine lacks, what is lost and how to install it. If something this task needs is missing, tell the user once and carry on with what there is; if `requisitos.py` is not there (a loose copy of the skill), carry on without it.

## Tools

Check what is available in the session; don't invent tools or assume they exist.

**Design MCP (e.g. `appian-dev`) — "how is this actually implemented?"** Inspect and modify real objects,
dependencies, validate against the environment. Ask for **the specific objects** you need; don't list the
whole application to find one; don't repeat a call whose answer you have. Before modifying an existing
object, check its **dependents**. Without a design MCP the work is the same, described as changes for
Designer: the rules and the gates don't depend on the tool.

**Before writing through a design MCP, the official Appian skill is required.**
[`appian/dev-mcp-skills`](https://github.com/appian/dev-mcp-skills/) carries what the tool schemas can't
express: naming conventions, relationships declared on both sides, the order objects must be created in,
real UUIDs versus invented ones. The gates here check the contract and the evidence, not those mechanics,
so a write issued without it fails in ways nothing here catches. That skill leans on the documentation MCP
for its function-availability checks, so the chain is **design MCP → official skill → documentation
MCP**. If the official skill isn't installed, say so and don't write until the user decides: the
mechanics it covers would go unchecked.

**Documentation MCP (e.g. `appian-docs`) — "how does Appian work?"** Syntax, functions, parameters,
components, limits, version-specific behaviour. It's the source of truth for a **concrete** doubt, not a
mandatory step for every task. The operative question: *is there a doubt whose answer would change what I
am about to write or recommend?* If not, don't query. Proportionality: known capability → no query;
doubtful parameter or unusual function → one query; architecture, security, performance, integration, AI
or platform-limit decision → verify.

How to query it well:

- **One concrete doubt per query, as a complete sentence** ("Does the read-only grid support
  pagination with record data?", not "grids").
- **Match the version.** Results come from several releases (the URL carries it, e.g. `/help/26.6/`). Use
  the chunks that match the environment's version; if only a newer release answers, say the capability
  may not exist in the environment yet.
- **Cite what you used**, with its URL (the `/latest/` form in documents that must not expire).
- If the chunks are only loosely related, reformulate **once**; if still nothing, report it as **not
  verified** instead of filling the gap from memory.

**For writing, the documentation MCP must be connected** (connected, not queried on every write): without
it, the official skill's function checks come back empty — which reads as *"the function doesn't exist"* instead of *"nothing was checked"*. If
it's missing, say so and stop rather than write on an unverified function. **For reading and reviewing**
without it, consult `docs.appian.com/suite/help/latest/…` by whatever means you have; if there is none,
**say explicitly what you couldn't verify**.

⚠️ **Don't invent Appian.** `a!` functions, parameters, components, properties, smart services,
capabilities, limits and tiers: either you know them with certainty or you verify them. The typical
failure is carrying syntax from other languages into SAIL as if the platform had it.

**Community Knowledge Base — "has anyone hit this before?"** For an error message or a production
symptom, look in doc 13 first; for anything newer, search the KB (`site:community.appian.com KB-…` or the
error text) and read the article with a fetch tool. Before applying a workaround, check its *Affected
Versions* and whether the environment's hotfix already contains the fix.

**Version:** the environment can lag behind `latest`. On Appian Cloud the quarterly releases (.3, .6, .9,
.12) are scheduled by Appian and can be rescheduled, and are supported for six months; the monthly releases
in between are optional and supported only until the next release; hotfixes are applied at least every 90
days. If something depends on the version, confirm it against the environment, not only against `latest`.

## Cardinal Rules

The ones that almost never have an exception. For a small, low-risk change they may be enough; as soon as
the change creates, writes or exposes something, also open the doc for its domain.

- **Query with `a!queryRecordType`, asking only for the fields you use.** Never inside a loop; page any
  potentially large collection; don't repeat the same query — cache it.
- **One record type = one business entity.** Model relationships instead of duplicating; any
  denormalization needs a documented reason.
- **Reuse.** One rule per responsibility, typed rule inputs, keyword arguments (by position only where the
  platform requires it: process events, process reports — doc 04 §2). Complex business logic → a Decision
  object, not a giant `a!match`.
- **An expression has no side effects**, and no guaranteed order or number of evaluations. Writing data is
  the job of smart services.
- **Always null-safe.** Null, empty list and "doesn't exist" are different states; an empty list keeps its
  type and **`a!forEach` doesn't evaluate its body** — which is why *testing with empty tables is not
  testing*: a broken screen passes every test case.
- **Short, decoupled processes.** Logic that doesn't persist belongs in a rule or record action, not in a
  process. **Activity chaining is not a transaction.**
- **Security by role, data and action.** Permissions to groups, least privilege. **Hiding UI doesn't
  authorize**: authorization lives in the layer that executes. Test one authorized and one NOT authorized
  role; row/field-level security **doesn't apply in Designer**, so test it with a real user of each role.
- **Credentials live in the connected system**, never in the integration; handle timeouts and errors; no
  integration inside an interface loop.
- **Idempotency** on every write that could be retried, and **optimistic locking** for concurrent editing.
  **Versioning ≠ rollback.**
- **AI only where the path is unpredictable.** Deterministic → rules; one cognitive step → AI skill;
  multi-step reasoning → agent, with human oversight on risky outputs. AI runs with its identity's
  permissions, and a prompt is never an access control.
- **Name by the current convention and deploy with packages** (Dev → Test → Prod, matched by UUID); never
  edit Production by hand.
- **Measure before optimizing** (Health Check / Performance Details). Design Guidance *warnings* are always
  resolved; *recommendations* can be dismissed, but consciously.

## Before Calling It Finished

An object isn't done because it exists and saves. Run it through the applicable gates in `10` (1 platform
correctness · 2 functional behavior with data, empty values, nulls and errors · 3 security by role, data
and action · 4 SAIL interfaces · 5 performance · 6 maintainability · 7 operations and deployment), and
through the operational-readiness gate in `11` if it reaches production.

Meeting the requirements demonstrates **functional** acceptance; the gates demonstrate **technical**
quality. Both are needed. If something is left unverified, **say so** — don't wave it through in silence.

## Which Source Wins

| Source | Wins on | Because |
|---|---|---|
| **Official documentation** (`docs.appian.com`, documentation MCP) | Everything, for the environment's version | It is the platform's own account of itself |
| **Approved requirements and the project's `DT-nn` decisions** (`analisis/funcional.md`, `analisis/tecnico.md`) | What the application must do, and the design choices already made with their reasons | Doc 10 *Hierarchy when requirements conflict*, levels 2–3: they never win over security or platform validity — if one breaks them, say so and propose a new decision |
| **Official Appian skill** ([`dev-mcp-skills`](https://github.com/appian/dev-mcp-skills/)) | Naming (where the project has no convention of its own), both sides of a relationship, creation order, UUID handling, dependency-ordered change planning (`change-planning.md`), post-change verification (`change-review.md`), query recipes (`query-record-type-patterns.md`), null handling (`null-safety-patterns.md`) and accessibility audits | It is the vendor's account of how its own API behaves |
| **Appian Community Knowledge Base** (Solution Engineering KB, Appian Max) | Field-proven patterns, known issues and their workarounds, Appian Cloud operations | Written by Appian's own support and delivery teams — but dated: check *Affected Versions* and the review date, and the docs win on conflict (doc 13 §11) |
| **These `references/`** | Solution decisions, quality gates, outcomes and evidence, when something is finished | That is what this skill is for |
| **The project's local convention** | House style, prefixes, structure | Consistency inside one app beats canonical style — unless it breaks security or platform validity; then say so |

Where they overlap, the higher one wins — except house style, where an existing app's own convention
wins (*Discovering Project Context*) — and a disagreement worth noticing is **said out loud** rather
than resolved quietly. Where the official skill already specifies a mechanic, cite it instead of
restating it here.

## When Doctrine and Official Documentation Conflict

Appian publishes every month. If the official documentation contradicts a `references/` doc:

1. **The official documentation wins** (for the environment's version). Don't apply the stale rule.
2. **Flag the discrepancy**, citing both statements with their source.
3. **Propose the change, don't make it:** updating the doctrine is the user's decision.

Numbers in the limits tables were audited against the official source: change them only with
documentation that contradicts them, never on intuition.

## Common Rationalizations

| The thought | Why it is wrong |
|---|---|
| "It validates, so it's finished" | Validation proves the platform accepts it, not that it is correct or well designed. |
| "The tables are empty but the screen works" | The body of `a!forEach` over an empty list is never evaluated. A broken screen passes every test against empty data. |
| "The test case is green" | A test that never exercises the path proves nothing. A search box is tested by typing something. |
| "The field came back null, so the restriction works" | Absence is indistinguishable from a restriction never applied. Put a real value in before you look. |
| "I only hid the button" | Hiding UI authorizes nothing. Authorization lives in the layer that executes the action. |
| "The API returned 200" | Some surfaces silently downgrade an unrecognized value and still answer 200. Read back what was stored. |
| "This query only returns a few rows today" | Current volume doesn't remove the obligation to page or bound. |
| "The validator reported an error, so I must fix it" | Run it first. A rule with no inputs that queries data reports an error and works; a fake input to silence the validator pollutes its signature. |
| "It's AI, it will work it out" | An agent that follows a predictable path pays reasoning cost on every run for nothing, and its instructions don't restrict what its identity can reach. |
| "The prompt says not to touch that data" | A prompt is behaviour, not access control. Remove the permission instead. |

## Red Flags

- A query inside a loop, or the same query repeated instead of cached.
- A reference to a rule or constant never verified to exist. `rule!Name` alone validates clean; only
  `rule!Name(param: null)`, with parentheses, proves it exists.
- A gate marked PASS whose evidence doesn't cover the gate's criterion.
- A destructive action whose confirmation sits on a component that ignores it.
- A screen whose only path to its data is a chart; a grid without a label or a row header.
- A title rendered as styled rich text instead of a heading component.
- Business validation drawn as a card with the submit button silently disabled.
- A colour used as the sole carrier of meaning.
- Hard-coded user-facing text in an app that must be multilingual.
- A write that isn't idempotent, or a retry issued before checking whether the first attempt persisted.
- An AI agent with overlapping tools, more than two levels of agents, no escalation path, or a path that is
  the same on every run.
- A capability that depends on tier or version recommended without checking the environment.

## Verification

Before calling the work finished, confirm and record:

- [ ] Every applicable gate in `10` has PASS, FAIL, N/A (with a reason about the object) or NOT MEASURED
      with its class — for a cosmetic change, gate 1 only.
- [ ] Every PASS names the evidence that produced it.
- [ ] Every NOT MEASURED · DEFERRED names a criterion **from the closed list in `10`**, a reason, an owner
      and a closing condition. Short of that it isn't a deferral: it's BLOCKING.
- [ ] Behaviour was exercised with populated data, not only with empty tables.
- [ ] If it reaches production, doc 11's operational-readiness gate is recorded, or its gaps are stated.
- [ ] If the change touches data, permissions or actions, one authorized and one unauthorized role were tested.
- [ ] Anything used from the documentation MCP is cited; anything that couldn't be verified is said.
- [ ] Nothing changed outside the agreed scope; anything noticed and left alone is stated explicitly.

---

*Sources: each doc in `references/` cites its own — official pages (`docs.appian.com/suite/help/latest/…`,
release notes) in its Sources list, Community and KB articles inline next to the rule they support. Links
use the `/latest/` alias, which redirects to the current release and never expires.*
