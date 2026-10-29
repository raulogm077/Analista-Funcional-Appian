# Official Appian skill — where it departs from the documentation

> Read this before the first write of a session through a design MCP, with the official Appian skill
> ([`appian/dev-mcp-skills`](https://github.com/appian/dev-mcp-skills/)) loaded. That skill owns the
> mechanics of the MCP and is required for writing (SKILL.md, *Tools*). This page lists the points where
> its guidance does not match `docs.appian.com`, so you know which one to follow. **The documentation
> wins over both skills** (SKILL.md, *Which Source Wins*).
>
> Checked against the skill shipped in the DevMCP bundle 26.9.5 (build 20261026-140102) and the 26.9
> documentation. Appian updates that skill often: if the installed skill no longer says what a row
> attributes to it, the row is obsolete — ignore it and tell the user, who decides whether to update this page.

---

## 1. Statements the documentation contradicts

Follow the "Do" column. The file named is where the official skill says it.

| Topic | The official skill says | The documentation says | Do |
|---|---|---|---|
| One query or several | Query once and derive the subsets in memory: hold one result and split it (open vs closed) with `where()` rather than querying again (`expressions.md`, `query-record-type-patterns.md`) | Query only the rows and fields you use and filter at the source; independent queries in separate local variables evaluate in parallel | Filter in the query and size the batch to what is displayed or processed; split in memory only a small set that is already loaded (doc 05 §2, doc 04 §7) |
| `choose()` | Listed as not to be used (`function-reference.md`) | Current function; evaluates only the chosen option. `a!match()` is offered as the more flexible alternative | Prefer `a!match()` in new code; `choose()` is valid where an index is the natural key (doc 04 §4) |
| Audit field names | `createdBy` / `createdAt` / `modifiedBy` / `modifiedAt` (`data-modeling.md`) | The default fields are `createdBy`, `createdOn`, `modifiedBy`, `modifiedOn` | Use Appian's names unless the project's convention says otherwise (doc 01 §3.4) |
| Record list | Not an interface type: embed a custom grid in a dashboard; a native Record List page is rare (`appian-workflow-patterns.md`) | A current feature: shown as a site or Tempo page, or through a records-powered grid | Record List page by default; a grid in an interface when the list falls short (doc 09 §1.3) |
| Where rules, interfaces and constants get security | Only from the application's default role map (`security.md`) | They inherit from their rule folder by default | Secure the folder; the result matches because generated folders carry the same groups (doc 06 §3) |
| Record action security | Expressions decide who runs a record action (`security.md`, *Where Role Checks Apply*); `record-types.md` names Views and Actions security only as one more gate | Security rules first; a security expression for complex conditions or legacy record types | Through the MCP the field is `visibilityExpr`; keep its logic as simple as a rule would be (doc 06 §5.3) |
| Destructive button | Solid + Negative (`button-instructions.md`, `ui-patterns.md`) | Ghost + Negative; at most one Solid button per interface | Ghost + Negative, with a confirmation (doc 02 §4.9) |
| Saving inside `a!forEach()` | Saves into `local!list[fv!index]` (`sail.md` example) | Components must save into `fv!item` | `fv!item` (doc 02 §4.3) |
| Rows per page | 10–25 typical (`grid-field-instructions.md`) | 5–10 when the grid shares the page, 50 when it is alone, 25 if unsure | The documentation's figures (doc 02 §5.6) |
| Formatting amounts | Decimal values display with `dollar()` (`interfaces.md`; also in the examples of `grid-field-instructions.md` and `patterns/kpis.md`) | `dollar()` is deprecated; `a!currency()` localizes the amount for the user's locale | `a!currency()` with the ISO code (doc 02 §10.3) |
| Wizard step style | Vertical from 4 steps; Minimal for mobile (`wizard-layout-instructions.md`) | Vertical with more than five steps or labels too long for a horizontal milestone; Minimal for one or two steps | The documentation's thresholds (doc 02 §4.6) |

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

## 3. Dev MCP behaviour the official skill does not cover

Only when you see the symptom; the normal path doesn't change (the prefix check is the exception, one call).
*Seen* is the DevMCP bundle build where it happened. If the symptom no longer appears, the row is obsolete:
drop it and tell the user.

| Symptom | Do | Seen |
|---|---|---|
| `createApplication` fails with a 500 ("Duplicate names for public and team groups") and the application exists, empty | The prefix was used by an application with another name. Choose another. To check one beforehand: `listObjects` with `query` = the prefix finds its `<prefix> Users` and `<prefix> Administrators` groups (`listGroups` needs an application) | 20261008-132401 |
| A field created by `createRecordType` as `GROUP` is an `INTEGER` | `updateRecordTypeField` to `GROUP`; read it back | 20261008-132401 |
| `insertRecordData` into a group-type field wants the group's numeric ID and no `get` returns it | `validateExpression` with `{1,2}[tointeger(cons!X)]`, or with no constant `{1,2}[tointeger(a!groupsByName("<group>")[1])]`: the error shows the value | 20261008-132401 |
| `createInterface` refuses an `a!recordLink`: the record type "has no summary view. Record links will not work until the record type has a summary view"; `validateExpression` had passed it | The record type needs its summary view first. If another issue creates it, that is an order dependency: stop and ask | 20261008-132401 |
| The spec asks for *Default (All Other Users)* on an object; `getObjectSecurity` returns it as `defaultRole` (e.g. `"no access"`), but `updateObjectSecurity` has no field to set it | Read it and compare it with the spec; if it differs, report it for a person in Designer | 20261019-134534 |
| `runAllInterfaceTestCases` fails on an interface with a records `a!gridField` ("Could not find variable 'flow!userFilterSetData'") although `testInterface` renders it | Seen with one records grid. Don't offer that saved test case as coverage: test the logic in rules with test cases and the screen in QA. Report an existing one as not evaluable (it shows red in Designer) and ask before removing it | 20261008-132401 |
| After `updateExpressionRuleTestCase` a case lost its inputs, or the UUIDs no longer resolve | The update drops inputs you don't repeat and every write renews all the UUIDs: repeat all inputs and re-list. The expected result is `test!output = …`, not `fv!output` | 20261008-132401 |
| After `createExpressionRule` with `testInputs` the rule has a test case you didn't create («Test Case 1», default, `NO_ERRORS`), and running its cases counts one more (also seen with build 20261008-132401) | It is where Appian keeps the default test values: leave it. It only proves the rule doesn't fail, so it doesn't count as coverage of a criterion just by existing: a criterion about what the rule returns needs a case with `EXPECTED_OUTPUT` or `RESULT_ASSERTIONS` | 20261026-140102 |
| `listProcessInstances` doesn't list an instance you expected, or its order doesn't match what happened (with build 20261019-134534 instances were also missing and `total` changed between calls) | Its absence doesn't prove the process didn't run: check the effect (the data it writes, `listProcessEvents` of an instance, the mailbox). Read `startTime`, not the position: the tool says newest-first, but the list came grouped by execution engine (ids 77…, 268…, 536…) | 20261026-140102 |
| A record list column from a related record is refused | Not available through the MCP. The design stays: a person adds the column in Designer (say which, in the delivery); don't swap the record list for an interface only because of this | 20261008-132401 |

---

## Sources

- [a!queryRecordType() — pagingInfo](https://docs.appian.com/suite/help/latest/fnc_system_queryrecordtype.html#using-the-paginginfo-parameter)
- [Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)
- [Using a!forEach() with interface components](https://docs.appian.com/suite/help/latest/fnc_looping_a_foreach.html#using-aforeach-with-interface-components)
- [choose() — Evaluation order](https://docs.appian.com/suite/help/latest/fnc_logical_choose.html#evaluation-order)
- [Create a record type — Review the default fields](https://docs.appian.com/suite/help/latest/create-record-data-source.html#review-the-default-fields)
- [Record list](https://docs.appian.com/suite/help/latest/record-list.html#what-is-a-record-list)
- [Object security — Security inheritance](https://docs.appian.com/suite/help/latest/object-security.html#security-inheritance)
- [Record Action Security — Security expression](https://docs.appian.com/suite/help/latest/record-action-security.html#security-expression)
- [Process model object — Process model security](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security)
- [Buttons — Position](https://docs.appian.com/suite/help/latest/sail/ux-buttons.html#position)
- [Grids — Batch size](https://docs.appian.com/suite/help/latest/sail/ux-grids.html#batch-size)
- [dollar() — deprecated](https://docs.appian.com/suite/help/latest/fnc_text_dollar.html) · [a!currency()](https://docs.appian.com/suite/help/latest/fnc_text_currency.html)
- [Wizard layout — Selecting a wizard style](https://docs.appian.com/suite/help/latest/sail/ux-wizard-layout.html#selecting-a-wizard-style)
