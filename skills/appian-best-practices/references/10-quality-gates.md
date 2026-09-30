# Quality gates — Definition of Done for an Appian object

> These gates **complement** the functional criteria of the project's approved requirements (its
> specification, user stories or acceptance criteria). An object is only **done** when it meets that
> functional criteria **and** the applicable gates in this document: the requirements demonstrate
> **functional** acceptance, the gates demonstrate **technical** quality. Both are needed.

## Apply the gates in proportion to the change

**"Applicable" does not mean "all, always."** A gate applies when the change can break what that gate
protects. Fixing a text literal does not need a role matrix or a performance measurement; creating a
record type that exposes compensation data does. The practical rule, for anything beyond a cosmetic change: **run through the list of
gates** (it's cheap) and **thoroughly execute the ones the change could break** (that's the expensive
part). A new object that writes data or exposes information touches almost all of them; a layout tweak,
two or three. A **cosmetic or local change** (text, spacing, a label — SKILL.md's first calibration row)
records **gate 1 only**; the other gates are not walked and get no verdict.

What **never** scales down: an invalid reference, an authorization gap and a non-idempotent write are
FAIL in any change, no matter how small.

## How it's recorded

For each applicable gate, record one outcome with its evidence, wherever the project tracks progress
(its status file, the ticket or the PR):

- **PASS** — checked, with evidence (UUID, validator output, test result, screenshot). A PASS whose
  evidence doesn't cover the gate's criterion is not a PASS.
- **FAIL** — the effect depends on the gate's class (table below).
- **NOT MEASURED** — the gate applies and no evidence covers it, including a gate nobody checked. It is
  never a pass.
- **N/A** — the gate doesn't apply to this object at all, because the condition it protects against isn't
  present (e.g. field-level security on an object with no protected fields). It needs **a concrete
  justification about the object** ("N/A: the object exposes no data"), **never** one about the process,
  the schedule or the time available. "N/A: I didn't get to it" is a NOT MEASURED under another name.

### NOT MEASURED has two classes

| Class | What it is | Effect |
|---|---|---|
| `NOT MEASURED · BLOCKING` | It could have been measured with the tools at hand and wasn't | Blocks the task. It's a process failure, not a limitation |
| `NOT MEASURED · DEFERRED` | The criterion structurally needs a person or a capability the tools don't expose | Doesn't block the task. **Blocks phase closure and deployment** until it has an owner and a closing condition |

A deferral is a named debt, not a permission: it is recorded with **criterion, reason, owner and closing
condition**. A deferral missing any of them is **rejected** — the gate stays shut — and it is not quietly
rewritten as something else.

**Only these criteria may be deferred.** The list is closed: a criterion can't be declared deferrable to
unblock a task. A deferral names the id it invokes.

| Id | Why it can't be measured by the builder |
|---|---|
| `screen-reader-testing` | Needs a person with a real screen reader |
| `design-guidance-warnings` | Design Guidance warnings aren't exposed by the API; someone must open the object in Designer |
| `row-and-field-level-security-with-a-real-user` | Row/field security doesn't apply in Designer; needs a login per role |
| `contrast-against-theme-supplied-colors` | Colors come from the environment's theme, not from the SAIL |
| `process-model-connection-routing` | Connection waypoints aren't exposed by the API |
| `visual-judgement-on-rendered-screen` | A person has to look at the rendered screen (not valid before the screen exists) |
| `instrument-limit-known` | The tool that should measure it failed for a reason unrelated to this change and no alternative evidence exists |

## The seven gates do not block alike

A matter of style must not be able to consume a remediation cycle. Three classes:

| Gate | Class | Effect of a FAIL |
|---|---|---|
| 1. Platform correctness | CARDINAL | **Blocks the close.** No exception |
| 3. Security | CARDINAL | **Blocks the close.** No exception |
| 2. Functional behavior | RECOMMENDED | **Blocks once:** fix it, or record it as debt with an owner and closing condition |
| 4. SAIL interfaces | RECOMMENDED | **Blocks once**, then closes with recorded debt |
| 7. Operations and deployment | RECOMMENDED | **Blocks once**, then closes with recorded debt |
| 5. Performance | CONTEXTUAL | **Doesn't block.** Recorded with its owner |
| 6. Maintainability | CONTEXTUAL | **Doesn't block.** Recorded with its owner |

The three that are **never graded down** — an invalid reference, an authorization gap, a non-idempotent
write — are CARDINAL wherever they are found, including inside a CONTEXTUAL gate.

The reason is in the doctrine itself: maintainability and performance are **contextual** judgements —
*measure before optimizing*, *a reasonable local convention overrides the generic preference of these
docs* — and the point is to favour good Appian development, not to build ceremony around every
recommendation.

**Contents:** Apply the gates in proportion to the change · How it's recorded
· The seven gates do not block alike · 1. Platform correctness · 2. Functional behavior
· 3. Security (by role, data and action) · 4. SAIL interfaces (full gate) · 5. Performance
· 6. Maintainability · 7. Operations and deployment · Quick gates by object type
· Review stages across a delivery (Appian Max) · Hierarchy when requirements conflict

---

## 1. Platform correctness

> **Before adding a check of your own, read the official one.** The official Appian skill specifies
> post-change verification in `references/change-review.md`. **Those are the mechanics; this section is
> the gate** — what must pass before a change can close, and what counts as evidence. Without that skill
> installed, this section stands on its own.

- ✅ The object **saves and validates without errors**. With a design MCP (e.g. `appian-dev`):
  `validateDesignObject`, and for interfaces `validateExpression` **with `isInterface: true`** (without
  that flag a correct interface fails with *"Could not find variable 'env!features'"*). Without MCP: save
  in Designer without errors and review its Design Guidance.
- ✅ Expressions, references, constants, record fields and rule inputs **exist and are of the expected
  type**. Known blind spot: validation **doesn't see a nonexistent rule invoked inside an `a!forEach` over
  an empty list** — catch it by evaluating the call to that rule separately, with its parentheses
  (`rule!Name(param: null)`).
- ❌ No **invented UUIDs, names, fields or references** remain. Identifiers come from reading the
  environment or the project's documentation, never from memory or from another environment.
- ✅ No broken dependencies or duplicate objects. Before **modifying** an existing object, check its
  **dependents** (`getObjectDependents` via MCP, or Designer's dependencies panel) and confirm they still work.

## 2. Functional behavior

Test, when applicable, these paths — not just the happy one:

- ✅ nominal path with **populated representative data** (the project's minimum dataset; if it doesn't
  exist, create it — it's the only way for the test to mean anything);
- ✅ **empty set** and **null values** (use an identifier that deliberately doesn't exist);
- ✅ invalid input and boundary values;
- ✅ dependency/integration error;
- ✅ **repeated** operation (detect duplicates / lack of idempotency).

> The key blind spot: the body of an `a!forEach` over an empty list **is not evaluated**, so a broken
> screen or rule **passes all its test cases with empty tables**. The case with real data **is not optional**.

Test data: representative, controlled, **no personal data or production secrets**.

> **Test case quality, not just its existence:** each case tests **only your logic** (not the platform),
> **one per expected result**, no trivial *"tests 1=1"* and **no dates or live data in value
> assertions** (controlled inputs, not `now()`/`today()`). A rule that queries live transactional data
> gets a smoke case instead — the query completes and returns the expected types (`typeof()`, doc 04 §8).
> A fragile or tautological case does not count as coverage.
> Source: [Expression Rule Testing — general guidance](https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html#general-guidance)

## 3. Security (by role, data and action)

If the change exposes objects, data or actions, define/update a **matrix**:

| Role/group | Visible objects | Accessible data | Allowed actions | Expected result |
|---|---|---|---|---|

- ✅ Permissions to **groups**, least privilege; review the **Application Security Summary**.
- ✅ Check separately: object security · **row-level** (record-level) and **field-level** security ·
  **action** authorization · access to processes/tasks/reports/integrations · **site/navigation** security ·
  the identity **AI agents** run as, if any.
- ❌ **Hiding a button or component in SAIL authorizes nothing.** Authorization lives in the layer that
  executes the action/query.
- ✅ Test **at least one authorized role and one NOT authorized** (and a partial one if the model covers it).
  Row/field security **doesn't apply in Appian Designer**: test it by logging in with a real user for each role.
- ⚠️ Field with **field-level security**: arrives **null** in the interface / **isn't returned** in a query /
  filtering or sorting by it errors out / **sync-time** custom fields **skip it**. No user filters on a
  protected field. When testing it: if the column is empty, the null you see is the data's, not the
  security's — a **false positive**. Put a real value in before you look.

Detail: doc **06-security**.

## 4. SAIL interfaces (full gate)

Every new or modified interface passes, **in order**:

1. **Syntax validation** — `validateExpression` with `isInterface: true` (or save in Designer without errors).
2. **Static analysis**, if the environment offers SAIL validators (linters or agents covering
   schema/parameters, icon keys and structure). They apply **in addition** to environment validation. If
   none is available, review by hand what they cover: existing functions and parameters, valid icon keys,
   correct enumerations.
3. Fix **every blocking finding** and re-validate what you touched.
4. **Render twice** (`testInterface` or open the interface): once with **populated real data** and once
   with **null data / a nonexistent identifier**. The second render alone proves nothing — see the
   `a!forEach` blind spot in gate 2.
5. **Runtime checks.** The ones the official skill's `change-review.md` defines (these five when this was
   written), on the populated render:
   - `diagnostics.error` is null — any value is a runtime rendering failure.
   - No `-1` in rendered text (a broken `totalCount`).
   - Count/alert cards show non-negative integers.
   - A filtered grid returns **fewer** rows than the unfiltered total.
   - No serialized `[@attributes=` inside a cell: grid columns carry strings or proper components.

   And three this skill adds, because the populated/empty pair is what exposes them:
   - A render that timed out or came back truncated is not a render.
   - The **populated render carries more nodes with a non-empty value than the empty one**. That
     inequality, not "it rendered", is what proves the loops iterated.
   - The empty render shows a **useful empty state**, not a blank gap.
6. **Don't read a large evaluated tree whole.** A medium screen's tree runs to hundreds of KB; reading a
   slice and judging the whole is a truncated verdict that looks complete. Search it for the checks above
   and **say which fragment you inspected**.

> **Why two layers of validation:** environment validation checks that the expression evaluates; static
> analysis catches what evaluation doesn't — an invalid icon key, a nonexistent `color` in rich text or a
> misspelled enumeration can pass validation and break (or render wrong) at runtime.

And a **manual review** (syntax validation doesn't replace it):

- ✅ **loading, empty, error and success** states with a useful message and next step;
- ✅ visual hierarchy, spacing, density and legibility; consistency with the rest of the app;
- ✅ accessible labels/instructions/validations; **contrast** and **not relying on color alone** (WCAG 2.2 AA);
- ✅ behavior at the **screen sizes** the requirements demand;
- ✅ **confirmation** on destructive/irreversible actions, on a component that actually honours it;
- ✅ user-facing text through the **translation set** if the app is multilingual;
- ❌ no UUIDs, indexes or technical text visible to the user.

> **Accessibility is TESTED, not just reviewed.** For critical screens, verify it as its own activity with
> **screen reader + keyboard navigation** (focus, reading order, error messages, zoom/reflow), not just by
> checking the SAIL. Source: [DevOps with Appian — accessibility testing](https://docs.appian.com/suite/help/latest/devops-with-appian.html) · [Building accessible applications](https://docs.appian.com/suite/help/latest/building_accessible_applications.html)

> Design Guidance is a gate, and its two alert types are **not** treated the same: **warnings (yellow
> triangle) can't be dismissed** and must **always be resolved** (they flag patterns that cause errors or
> unexpected behavior at runtime); only **recommendations (lightbulb) can be dismissed**, and dismissing
> one is a justified, conscious decision. Never close an interface with open warnings.
> Source: [Design guidance — warnings vs. recommendations](https://docs.appian.com/suite/help/latest/appian-recommendations.html#warnings-vs-recommendations)

Detail: docs **02-interfaces-sail**, **04-expression-rules**, **05-performance**.

## 5. Performance

- ✅ Queries request **only the fields needed**; every potentially large collection is **paginated or
  bounded** (remember the 5,000-row cap for records-powered components).
- ❌ No query **inside a loop** (N+1); no expensive expression/query repeated — cache it in a local variable.
- ✅ Refresh and SAIL re-evaluations **justified** (expensive work in `a!localVariables`, not in parameters).
- ✅ Don't invent a performance threshold: use the agreed requirement or record a **baseline measurement**
  (Performance Details / Health Check). Document sync, volume and concurrency risks if relevant.
- ✅ With AI: an **AI action estimate** per end-to-end transaction and the chosen accuracy/speed/cost priority.

Detail: docs **05-performance**, **12-ai-agents-and-skills**.

## 6. Maintainability

- ✅ **Naming** conforms to the current convention: the project's if it's documented, or the one existing
  objects already follow; failing that, the official standard (Standard Object Names, doc 08).
- ✅ **Typed** rule inputs with clear names; each rule, **one responsibility**.
- ❌ No duplicated business logic or embedded environment values (use constants; complex logic → Decision object).
- ✅ Comments that explain **non-obvious decisions**, not that repeat the code, and **not the object's
  change history** — what changed and when belongs to the project's documentation, not inside the object.
  Errors turned into controlled results/messages.

Detail: docs **04-expression-rules**, **08-alm-testing-naming**.

## 7. Operations and deployment

- ✅ Dependencies and per-environment configuration **identified**; the package contains the expected
  objects and **no accidental changes**.
- ✅ **Inspect the package before deploying.** Review **security warnings**, **failing test cases** and
  **missing precedents**. Warnings alert but let you continue; **deployment errors block** it (references
  to deleted objects or invalid record fields). Don't deploy with deployment errors.
  Source: [Inspect deployment packages](https://docs.appian.com/suite/help/latest/inspect-deployment-packages.html) · [Deploy to target environments — inspect the package](https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html#inspect-the-package)
- ✅ **Compare the package against the target** before deploying: which objects **exist, change or
  conflict** there, so you don't overwrite someone else's changes in a shared environment.
  Source: [Prepare the Deployment — Comparing across environments](https://docs.appian.com/suite/help/latest/prepare-deployment.html#comparing-across-environments) · [Prepare deployment packages](https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html)
- ✅ **Full regression before a major deployment:** run **all** the application's rule/interface test
  cases (Start Rule Tests → Applications/All) and confirm they pass.
  Source: [Automated Testing for Expression Rules](https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html) · [Expression Rule Testing](https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html)
- ✅ **Watch coverage, not just the result:** use **Manage Test Cases** to find rules **without** a test and
  prioritize the reused/critical ones; for critical flows, consider **UI automation** (FitNesse/Cucumber or
  the Appian Selenium API).
  Source: [Expression Rule Testing — test case management](https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html#test-case-management) · [Testing Applications — UI testing](https://docs.appian.com/suite/help/latest/testing-applications.html#user-interface-ui-testing)
- ✅ Objects with their own deployment rules (AI agents and their tools, DocCenter models, translation
  sets) checked as doc 08 §3 describes.
- ✅ Processes and integrations with **exception handling** matched to their impact; defined **which
  operations are safe to retry** (idempotency).
- ✅ If a build is left **partial**, document **what was created** and **how to resume it without
  duplicating** objects.

> **Health Check as a cadenced gate:** run it **at least once per sprint** and review its **four areas**
> (Infrastructure, Configuration, Design, UX), not only when chasing a performance number.
> Source: [Continuous improvements to your application](https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html) · [Health Check](https://docs.appian.com/suite/help/latest/health-check.html)

> **Operational readiness (doc 11).** Before closing something that reaches production, also apply doc
> **11**'s operational readiness gate: **tested alerts**, a recovery **runbook**, a
> **rollback/roll-forward** plan, an **E2E smoke test** from the real consumer, **idempotency and
> concurrency** tested, and **sign-off from the operational owner**.

Detail: docs **03-processes**, **07-integrations**, **08-alm-testing-naming**, **11-reliability-operations**.

---

## Quick gates by object type

Specific minimums, in addition to the seven cross-cutting gates:

- **Record type / data model:** keys, relationships and cardinality defined; tested with an existing
  record, a nonexistent one and an empty relationship; record-level security, sync, volume and refresh
  reviewed; sync failure options and who receives the alerts decided; delete behavior (relationship
  setting + FK) aligned; no duplication without a documented reason; record events decided for the main
  business entity.
- **Expression rule:** typed inputs; nominal/null/empty/invalid/boundary cases; no repeated or looped
  queries; stable output contract documented for its use; test cases saved.
- **Process model:** success/exception/cancellation/retry paths where applicable; every gateway with a
  default path and every node with an exit; reusable logic **outside** the process; start/tasks/escalation
  security, tasks assigned to groups or data-based users with deliberate reassignment privileges; messages
  targeted by process ID; a re-run **doesn't** duplicate effects; archiving policy set.
- **Process change with instances in flight:** decided whether running instances must change (Process
  Upgrade, Edit Process) or coexist (N/N-1); child subprocess inputs/outputs kept backward compatible,
  because running parents start the latest published child.
- **Integration:** credentials only in the connected system; timeout, remote error, empty and invalid
  response handled; no secrets/sensitive payloads in user-facing messages or logs; normalized
  input/output contract for its consumers.
- **Site / navigation:** visibility and access by role; consistent navigation with no unreachable pages;
  initial state and empty-data routes tested; no display name with a long-running query.
- **AI agent:** the path genuinely varies (otherwise rules or an AI skill); only the tools it needs, none
  overlapping; escalation triggers and a safe output for edge cases; watchdog or review path in the
  calling process; initiator/service account permissions checked on every tool; a saved test case library
  run after the last change; AI action estimate recorded.
- **AI skill / document extraction:** pattern chosen for the document type; execution mode chosen for
  the real duration (the Test button always runs Standard); model enabled in every target environment;
  confidence threshold and a human review path for low confidence; tested on representative documents
  before production volume; output structure validated before use.
- **Translation set / multilingual screen:** no hard-coded user-facing text; every translation locale
  enabled in every target environment; translator notes where a string needs context (e.g. two strings
  that look duplicated).
- **Offline form:** all data loaded at the top, in local variables or rule inputs; no incompatible
  functions, components or plug-ins; tested end to end in the Appian app where it will run.
- **DocCenter model:** extraction configuration no costlier than the accuracy target requires; source and
  target on the same platform version before deploying.

---

## Review stages across a delivery (Appian Max)

The gates above judge a change; these reviews judge a release. Fix High findings and re-review;
handle Medium and Low in parallel.

| Stage | When | Checks |
|---|---|---|
| Solution Architecture Review | End of Initiate | Data model, integrations, security model, volumes and NFRs against doc 00 |
| Development Review | A few times per iteration | Key interfaces under ~1 s, role security, database volume test, indexes |
| UX Review | Sprint 1, and before Build ends | Consistency, clicks and scrolling minimized, accessibility |
| Technical Readiness Check | Before go-live | UAT across every persona; deployment plan with owners; full package incl. DB scripts; whole-site peak load test on production-like volume (≥ 1 year of data) |
| Go-live checklist | Deployment day | Post-deployment validation scripts; testers with production access and a system administrator present; missing precedents, Security Summary and production values of environment-specific constants checked; owners of dependent systems notified; recurring Health Check scheduled in Production |

Source: [Appian Max — Manage and Mitigate Delivery Risk](https://community.appian.com/delivery-28/manage-and-mitigate-delivery-risk-1210) · [Appian Max — Application Go-Live Readiness Checklist](https://community.appian.com/delivery-28/application-go-live-readiness-checklist-1217) · [Appian Max — Design Review Checklist](https://community.appian.com/architecture-29/design-review-checklist-1223)

---

## Hierarchy when requirements conflict

When two requirements clash, this is the order (a higher layer is not overridden by a lower one):

1. **Security, privacy and platform validity** (an invalid reference or a security gap is never justified
   by a functional requirement).
2. **The project's approved requirements and acceptance criteria** (if its specification has several
   versions or annexes, the **most recent** prevails per its version control).
3. **Recorded architecture decisions** and the project's established conventions.
4. **Best practices** (these docs).
5. **Implementation preferences.**

If a requirement clashes with level 1, **don't silently reinterpret it**: document the conflict and ask
for a decision.

> **Project conventions vs. best practices (levels 3 and 4).** A reasonable local convention —prefixes,
> folder organization, constant patterns, interface structure— **overrides the generic preference of these
> docs**: consistency within an app matters more than canonical style. Before creating objects, look at how
> existing ones are named and organized and follow that pattern. If the local convention clashes with
> **level 1** (e.g. a pattern that leaves a sensitive field unprotected), flag it instead of perpetuating it.
