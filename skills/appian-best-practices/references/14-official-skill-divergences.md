# Official Appian skill — where it departs from the documentation

> Read this before the first write of a session through a design MCP, with the official Appian skill
> ([`appian/dev-mcp-skills`](https://github.com/appian/dev-mcp-skills/)) loaded. That skill owns the
> mechanics of the MCP and is required for writing (SKILL.md, *Tools*). This page lists the points where
> its guidance does not match `docs.appian.com`, so you know which one to follow. **The documentation
> wins over both skills** (SKILL.md, *Which Source Wins*).
>
> Checked against the skill shipped in the DevMCP bundle (build 2026-10-08), `dev-mcp-skills` commit
> `6e87fb6` (2026-09-23) and the 26.9 documentation. Appian updates that skill often: if the installed
> skill no longer says what a row attributes to it, the row is obsolete — ignore it and tell the user,
> who decides whether to update this page.

---

## 1. Statements the documentation contradicts

Follow the "Do" column. The file named is where the official skill says it.

| Topic | The official skill says | The documentation says | Do |
|---|---|---|---|
| `and()` / `or()` | They don't short-circuit; guard with nested `if()` (`short-circuit-patterns.md`) | Arguments are evaluated left to right and evaluation stops at the first `false` (`and`) or `true` (`or`) | Put the cheap or guarding condition first (doc 05 §3). A nested `if()` is harmless, not required |
| `fetchTotalCount` | Required on every `a!queryRecordType()` (`query-record-type-patterns.md`) | Defaults to `false`; `true` runs an additional query for the total | Set it only where a total is shown or `.totalCount` is read (doc 05 §2) |
| One query or several | "Query once, transform many": one unfiltered query split in memory is the efficient form, two filtered queries the inefficient one (`expressions.md`) | Query only the rows and fields you use and filter at the source; independent queries in separate local variables evaluate in parallel | Filter in the query and size the batch to what is displayed or processed; split in memory only a small set that is already loaded (doc 05 §2, doc 04 §7) |
| `a!forEach()` over null | Returns null (`expressions.md`) | Returns an empty list of the same type and doesn't evaluate the expression | Don't wrap the list only to avoid a null result; do test with populated data (doc 04 §5) |
| `length()` on a list | It is an error; use `count()` (`expressions.md`) | `length()` takes an array and returns its number of elements | Either works; they differ in how they treat nulls (doc 04 §5) |
| `choose()` | Listed as not to be used (`function-reference.md`) | Current function; evaluates only the chosen option. `a!match()` is offered as the more flexible alternative | Prefer `a!match()` in new code; `choose()` is valid where an index is the natural key (doc 04 §4) |
| Today's date | `todate(now())` (`date-time-patterns.md`) | `todate()` of a date-time works in GMT and can return a different day | `todate(local(now()))` for the user's local day (doc 04 §11) |
| Composite primary key | Not supported; the key must be a single integer `id` (`data-modeling.md`) | Synced record types over an existing table accept a composite key (ⓥ from 26.3); a generated table gets a single integer `id` | New table through the MCP: single `id`. Existing source: its key as it is (doc 01 §2.1, §8.1) |
| Audit field names | `createdAt` / `updatedAt` (`data-modeling.md`) | The default fields are `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn` | Use Appian's names unless the project's convention says otherwise (doc 01 §3.4) |
| Record list | Deprecated as an interface type (`record-summary-views.md`) | A current feature: shown as a site or Tempo page, or through a records-powered grid | Record List page by default; a grid in an interface when the list falls short (doc 09 §1.3) |
| Where rules, interfaces and constants get security | Only from the application's default role map (`security.md`) | They inherit from their rule folder by default | Secure the folder; the result matches because generated folders carry the same groups (doc 06 §3) |
| Record action security | Only a visibility expression (`record-types.md`) | Security rules first; a security expression for complex conditions or legacy record types | Through the MCP the field is `visibilityExpr`; keep its logic as simple as a rule would be (doc 06 §5.3) |
| Destructive button | Solid + Negative (`sail.md`) | Ghost + Negative; at most one Solid button per interface | Ghost + Negative, with a confirmation (doc 02 §4.9) |
| Saving inside `a!forEach()` | Saves into `local!list[fv!index]` (`sail.md` example) | Components must save into `fv!item` | `fv!item` (doc 02 §4.3) |
| Rows per page | 10–25 typical (`grid-field-instructions.md`) | 5–10 when the grid shares the page, 50 when it is alone, 25 if unsure | The documentation's figures (doc 02 §5.6) |
| Wizard step style | Vertical from 4 steps; Minimal for mobile (`wizard-layout-instructions.md`) | Vertical with more than five steps or labels too long for a horizontal milestone; Minimal for one or two steps | The documentation's thresholds (doc 02 §4.6) |
| Rich text colors | `STANDARD`, `ACCENT`, `POSITIVE`, `NEGATIVE`, `SECONDARY` or hex (`rich-text-instructions.md`) | The same plus `WARN` (ⓥ from 26.6) | `WARN` is valid from 26.6; check the environment's version (doc 02 §6.2) |
| Recursive rules | Circular references between rules are a runtime error (`expression-rules.md`) | Recursive rules are allowed; Health Check flags a total depth over 20 | Allowed with a bounded depth; prefer looping functions (doc 04 §7) |

## 2. Conventions of the official skill this guide narrows

The documentation doesn't settle these; this guide's criterion applies, and the official skill's
mechanics still do.

- **Write inline or in a process.** Its test is whether an update process already exists
  (`write-records-patterns.md`), and its plan review asks that every form have a backing process model
  (`change-planning.md`). Decide by what the write needs instead — doc 03 §8.
- **A button that starts a process to save a record.** Documented for unattended work; to create or
  edit a record with a form, use a record action — doc 00, *Process*.
- **Reference tables.** Its fixed four-field shape with `isActive` suits a static lookup; reference data
  whose validity period matters takes `startDate`/`endDate` — doc 01 §4.3.
- **Audit fields only on primary entities.** A table read by a scheduled incremental sync needs its Last
  Modified field whatever kind of table it is — doc 01 §3.4.
- **Relationship names.** It derives them from the foreign key field; the documentation asks for the
  related record type's name. They coincide in the simple case; with several relationships to the same
  record type, name each by its role — doc 01 §4.2.
- **Retrying a failed write.** It retries once after a timeout or a 500 (`change-review.md`). Before
  that retry, re-read or list whether the first attempt persisted: a `create` that timed out may have
  created the object — SKILL.md, *Red Flags*; doc 11 §2.
- **Completing mandatory steps without asking.** The reverse side of a relationship or the relationship
  of a user field belong to the object being built: completing them is not working outside the agreed
  scope. If one of them touches an object the issue freezes or leaves to another one (`construccion/<U>/ISS-nn.md`),
  stop and ask — SKILL.md, *Discovering Project Context*.
- **Loading its references before every write.** That is its own rule, whatever the size of the change;
  this skill's calibration only decides which of **this** skill's docs to open — SKILL.md, *Calibrate*.
- **Listing a type before creating an object.** A collision check, not the exploration this skill warns
  against — SKILL.md, *Discovering Project Context*.

---

## Sources

- [and() — Evaluation order and performance](https://docs.appian.com/suite/help/latest/fnc_logical_and.html#evaluation-order-and-performance)
- [a!queryRecordType() — fetchTotalCount](https://docs.appian.com/suite/help/latest/fnc_system_queryrecordtype.html#using-the-fetchtotalcount-parameter) · [pagingInfo](https://docs.appian.com/suite/help/latest/fnc_system_queryrecordtype.html#using-the-paginginfo-parameter)
- [Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)
- [a!forEach() — Null or empty items list](https://docs.appian.com/suite/help/latest/fnc_looping_a_foreach.html#null-or-empty-items-list) · [Using a!forEach() with interface components](https://docs.appian.com/suite/help/latest/fnc_looping_a_foreach.html#using-aforeach-with-interface-components)
- [length()](https://docs.appian.com/suite/help/latest/fnc_array_length.html) · [choose() — Evaluation order](https://docs.appian.com/suite/help/latest/fnc_logical_choose.html#evaluation-order)
- [local()](https://docs.appian.com/suite/help/latest/fnc_date_and_time_local.html#use-local-to-get-the-current-context-for-date-time-functions)
- [Data access — field requirements for optimized data access](https://docs.appian.com/suite/help/latest/about-data-sync.html#field-requirements-for-optimized-data-access)
- [Create a record type — Review the default fields](https://docs.appian.com/suite/help/latest/create-record-data-source.html#review-the-default-fields)
- [Record list](https://docs.appian.com/suite/help/latest/record-list.html#what-is-a-record-list)
- [Object security — Security inheritance](https://docs.appian.com/suite/help/latest/object-security.html#security-inheritance)
- [Record Action Security — Security expression](https://docs.appian.com/suite/help/latest/record-action-security.html#security-expression)
- [Process model object — Process model security](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security)
- [Buttons — Position](https://docs.appian.com/suite/help/latest/sail/ux-buttons.html#position)
- [Grids — Batch size](https://docs.appian.com/suite/help/latest/sail/ux-grids.html#batch-size)
- [Wizard layout — Selecting a wizard style](https://docs.appian.com/suite/help/latest/sail/ux-wizard-layout.html#selecting-a-wizard-style)
- [Rich Text Icon — Parameters](https://docs.appian.com/suite/help/latest/Styled_Icon_Component.html#parameters)
- [Health Check — Recursive rule depth limit](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#recursive-rule-depth-limit)
