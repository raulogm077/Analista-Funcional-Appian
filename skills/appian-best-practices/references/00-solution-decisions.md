# Solution decisions — which Appian mechanism for which need

> The decision map to open **first** when the task is to orient or design a solution rather than to build
> one object. Each row is a decision Appian's doctrine already settles; the detail, the traps and the
> official source live in the domain doc the row points to. Its rows add no rule of their own: if a row
> and its domain doc ever disagree, the domain doc (and above it, the official documentation) wins.

---

## How to use it

1. Walk the layers **in order** — data → security → logic → process → interfaces → navigation →
   integrations → AI → ALM. Earlier layers constrain later ones: a data model decided late forces rework
   in every screen and process.
2. For each need, take the **Choose** column unless a real constraint rules it out; say which constraint.
3. Open the pointed section **only** for the decisions the solution actually faces.
4. Before recommending anything marked ⓣ (tier) or ⓥ (version), confirm it against the environment
   (see the last section).
5. Present each decision as: **decision · why (source) · alternative rejected · risk · tier/version
   dependency · what to verify**.

---

## Data

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| A business entity (person, place, thing, event) | One **synced record type** (Optimized Data Access) per entity | CDT + data store "out of habit"; cramming concepts into one record type | 01 §0–§2 |
| See external changes instantly / exceed the tier's row limit | **Direct Data Access, features enabled** (single PK; no smart search; Process HQ process data needs synced record types) — or sync filters | Legacy record type (loses relationships) | 01 §2.1, §3.2 |
| Keep data current when other systems write | Sync Records after direct writes; ⓣ incremental syncs + a periodic full sync | Relying on the nightly full sync alone | 01 §3.4 |
| Remove rows but keep them for audit | **Soft delete** (`isDeleted` + sync filter) | Hard delete when history is required | 01 §4.3 |
| Bulk, set-based writes | Stored procedure + Sync Records | Row-by-row writes in MNI or loops | 01 §12.2, 03 §5 |
| Delete for real (privacy, volume) | Hard delete by PK + JSON audit copy + batched purge | Deleting without a trail | 01 §4.3 |
| Field-level change history | Database triggers into history tables (not synced) | Diffs computed in processes | 01 §11 |
| Heavy aggregations for reporting | Reporting tables / "materialized view" refreshed by a scheduled procedure | Nested views | 01 §12 |
| Letters and documents with many inputs or dynamic sections | Out-of-the-box Word template up to ~10 static inputs; Advanced Document Templating plug-in beyond | Generating documents nobody needs to store | 01 §8.bis.4 |
| Catalog / status / type values | A **lookup record type** related N:1 | Repeated free text | 01 §1.1 |
| Many-to-many | A **join record type** with N:1 to each side | — | 01 §4.1 |
| Derived value | **Sync-time** custom field if static; **real-time** if relative (`today()`) or from related data | Sync-time over a field-level-secured field | 01 §5 |
| Design documents (logos, templates) | **Folders** (knowledge center + document folder) | Workflow documents in folders | 01 §8.bis.1 |
| Documents born in the workflow | **Document management record type** ⓣ | Loose documents with no row | 01 §8.bis.2 |
| Letters, minutes, reports | **Doc-from-template** smart services | Hand-built HTML/text | 01 §8.bis.3 |
| Audit trail, activity log, process mining | **Record events** (Event History + Event Type Lookup) | Ad-hoc log tables; events on lookup record types | 01 §11 |
| Values that differ per environment | **Environment-specific constant + ICF** | Editing objects after each deployment | 04 §9, 08 §3 |

## Security

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Access by role | **Groups** in role maps; Administrator + Viewer groups on every object | Named users; Default = Administrator | 06 §1–§2 |
| Rows per user | **Security Rules**; Security Expression only for complex logic | Filtering in the UI | 06 §5.1 |
| Sensitive fields | **Field-level security** + `a!doesUserHaveAccess()` in `showWhen` | User filters or sync-time fields over them | 06 §5.2 |
| Actions per user | **Record action security** + Initiator on the process model | Hiding the button | 06 §5.3 |
| External, unauthenticated users | **Portal** with a least-privilege service account | Exposing personal or case data without authentication | 06 §9 |
| External users seeing their own data | Login (or own front end) + **record-level security by user** + non-guessable ids | Sequential ids in URLs | 06 §9.1 |

## Logic

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Reusable calculation or query | **Expression rule**, typed inputs, keyword arguments | Copy-pasted expressions | 04 §1–§2 |
| Rule matrix maintained by the business | **Decision** object | 15-branch `a!match` | 04 §4 |
| Read data | Expression rule | A process model | 03 §8 |

## Process

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Orchestrate people, waits, writes | **Process model**, short, one responsibility, ≤ 50 nodes | Logic-only processes (use a rule) | 03 §1, §8 |
| Start from the UI | **Record list action** (create) · **related action** (update/delete) | Custom buttons starting processes ad hoc | 01 §9.2 |
| Many instances | **Start Process** smart service; from outside, **Web API + `a!startProcess()`** with batching | Async subprocess with large MNI | 03 §2, §9 |
| Deadlines on tasks | **Escalations** on the attended node | Hand-built timer loops | 03 §6 |
| Who gets each task | **Groups** or data-based users; reassignment privileges set on purpose | Named users; the default "reassign to anyone" | 03 §7 |
| Talk to a running process | Send Message with `DestinationProcessID`; persist state when delivery matters | Untargeted messages; message loops as request/response | 03 §13 |
| High-volume unattended processing | ⓣ **Autoscale**, within its limits | Autoscale for flows that need messages, timer starts or long nodes | 05 §4, 03 §6, §13 |
| Abandoned processes | Timer that closes them + archiving policy | Instances living forever | 03 §6, §9 |
| Work that lives for weeks with hand-offs | Linked models split at hand-offs, restartable from an ID; nightly scheduler instead of long timers | One process instance for the whole case lifetime | 03 §2–§3 |
| Change a process with instances in flight | Backward-compatible change; **Process Upgrade** (all instances) or **Edit Process** (one), off-peak, with backup | Editing and hoping; changing a child's inputs under running parents | 03 §12 |

## Interfaces

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Single-screen form / sequential steps / parallel views | `a!formLayout` / **`a!wizardLayout`** / `a!tabLayout` | A hand-made wizard with `showWhen` | 02 §4.6 |
| Show tabular data / edit a few rows inline | Read-only grid on `a!recordData` / editable grid | Editable grid at volume (no paging) | 02 §5.1 |
| Slow data | `a!asyncVariable` / `loadDataAsync` (≤ 7 per interface recommended, > 500 ms) | Async on fast data | 02 §2.3, 05 §3 |
| Charts | Aggregations on the record type + chart↔grid toggle | A chart as the only path to the data | 02 §5A, §9.5 |
| Several languages | **Translation set** (one per app) | Hard-coded labels | 02 §10 |
| Users upload files | File Upload with `fv!files` validation + Admin Console allow list and type verification | Accepting any extension | 02 §4.10 |
| Business self-service reporting | ⓣ **Process HQ** over record types exposed in the Data Catalog | A hand-built report screen per question | 01 §10–§11 |
| Work without connectivity | **Offline-enabled interfaces** ⓣ following the offline rules | Pickers, plug-ins, record lists offline | 02 §11 |

## Navigation

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| A record list on the site | **Record List** page | Rebuilding the list in an interface | 09 §1.3 |
| Many pages | Page groups (Interface pages only), ≤ 8 top-level items; sidebar if navigation is complex | Every subsection as a top-level page | 09 §2–§4 |

## Integrations

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Call an external API | **Connected system** (credentials, base URL) + integration with timeout | Secrets in the integration | 07 §1–§3 |
| Read external data on screen | "Query" integration, async if slow | Integrations inside `a!forEach` | 07 §4 |
| Change external data | "Modify" integration from a process, `saveInto` or Web API write | Modify integration marked "query" | 07 §3 |
| Expose Appian to other systems | **Web API** + service account with API key or OAuth 2.0 client credentials | Personal accounts, session auth | 07 §6, 06 §7 |
| External data as records | Service-backed record type with batching | Query functions in the record data source | 07 §7 |
| A system with no API | **RPA** robotic task orchestrated from a process | RPA when an API or integration is available | 07 §8 |
| External system reports progress | Webhook → Web API → process | Polling per instance | 07 §4 |
| Event streaming / message queues | ⓥ ⓣ Kafka: Apache Kafka connected system + Event Consumer / Publish Event (26.6+); other queues (JMS, MQ): an API gateway calling a Web API | Direct JMS (not available on Cloud) | 07 §4 |
| Private connectivity to on-premises systems | VPN / PrivateLink; ⓥ ⓣ Cloud Secure Link (26.7) | Opening inbound ports | 07 §2 |

## AI

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Deterministic decision | Rules / Decision / process | An agent | 12 §0 |
| One cognitive step (classify, extract, summarize) | **AI skill** inside a process | An agent | 12 §0 |
| Multi-step work with an unpredictable path | **AI agent** (process or chat), ≤ 2 levels, human oversight | Agents whose path is always the same | 12 §0–§6 |
| Data from documents | **DocCenter**, cheapest configuration that reaches the target (Text → Visual → Advanced Layout), confidence + review ⓣ | Advanced Layout by default; blind straight-through processing | 12 §10 |
| An AI skill that may run long or at volume | **Long Running** mode, Auto model ⓥ, retry on throughput errors | Assuming the Test button's timing holds in production | 12 §10.0 |
| AI safety across the environment | **AI Guardrails** ⓥ + record/field security | Relying on the prompt for access control | 12 §7 |

## ALM

| Need | Choose | Avoid | Detail |
|---|---|---|---|
| Promote changes | **Packages**, Dev → Test → Prod, Compare & Deploy | Editing Production | 08 §3 |
| CI/CD | **Deployment REST API** ⓥ (inspect before import) | Home-grown export scripts | 08 §3 |
| Recovery | Roll-forward, N/N-1 compatibility, compensating scripts, backup | Treating versioning as rollback | 08 §3, 11 §7 |
| Environments on different releases | Deploy only from earlier to same or later versions | Upgrading Dev before its targets | 08 §3 |
| Shared platform or separate installation | One shared platform; separate only for 24x7 mission-critical volume, strict regulatory isolation or fully separate users and data | A new environment per application | 08 §3 |
| Business continuity (RPO/RTO) | High Availability or Enhanced Business Continuity, checked against their exceptions | Assuming a stricter RTO/RPO than the plan gives | 11 §7 |

---

## Stories that need an architect before building

Appian Max flags these patterns as the ones that most often go wrong; route them to an architect (and a
design note with test scenarios) before estimating: file import/export; querying far more data than is
shown; long same-user activity chains; ETL or headless processing inside processes; processes that live
for weeks or months; process-to-process messaging; nested CDTs; document generation; high volumes;
event-driven or unusually authenticated integrations (JMS isn't available on Appian Cloud); inbound email.

Source: [Appian Max — Heuristics of Complex User Stories](https://community.appian.com/architecture-29/heuristics-of-complex-user-stories-1214) · [Appian Max — Best Practices: Appian User Stories](https://community.appian.com/delivery-28/best-practices-appian-user-stories-1317)

---

## Before recommending: tier and version

- ⓣ **Tier-dependent** (Advanced/Premium, usage limits may apply): offline experiences, Process HQ,
  document extraction AI skills, document management by record type, Autoscale, incremental syncs, smart
  search, Case Management Studio, Composer, CSS profiles (per-site typefaces), Apache Kafka connected
  system, Cloud Secure Link. Appian for Windows is licensed separately. Confirm the environment's tier
  before a solution depends on them.
- ⓥ **Version-dependent**: read-only grid without total count by default (26.3); "Keep data available at
  high volumes" trimming on incremental and smart service syncs, rule exceptions and activity chaining in
  autoscale (26.4); timer exceptions, Start Process MNI in autoscale and Trace Explorer (26.5); AI
  Guardrails, Usage Groups (26.6); MCP tools, parallel tool calls and the Evaluate tab for agents (26.6);
  agent process-tool timeout (3 min in 26.3, 30 min in 26.6); external model providers for agents and
  Auto model for AI skills (26.7); cross-record SQL system tools, the Resources tab and status outputs on
  Execute AI Agent (26.8); model governance controls (26.4–26.6); Deployment REST API v3 (26.5+); offline
  forms in Appian for Windows and the Kafka connected system (26.6); per-site typefaces through CSS profiles
  (26.5); Cloud Secure Link (26.7, high availability 26.9); Interaction Diagnostics (26.7); autoscale start
  forms (26.1), activity chaining (26.4) and user input tasks with `a!queryTaskList()` (26.9); filtering a
  process model tool's output (26.9). Confirm the
  environment's version: on Appian Cloud the quarterly releases (.3, .6, .9, .12) are scheduled by Appian
  and can be rescheduled, while the monthly releases in between are optional and requested through
  support — so environments can sit on different versions and lag behind `latest`.
- When a need has no row here, don't invent one: check the domain doc, then the documentation MCP, and
  say which alternative you considered and why.

Source: each row's detail section carries its official source. Tiers: [Appian Tiers](https://docs.appian.com/suite/help/latest/Appian_Tiers.html) · Releases: [Appian Cloud Environment Maintenance — Platform upgrades](https://docs.appian.com/suite/help/latest/Appian_Cloud_Site_Maintenance.html#platform-upgrades).
