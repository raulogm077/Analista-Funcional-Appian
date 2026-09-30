# Best practices — Performance and scalability

> Official Appian doctrine for applications to load fast and scale: fetch only the data you need, don't recompute, keep processes lightweight, and measure before optimizing. Every rule is anchored to `docs.appian.com/suite/help/latest/`. The links use `latest` (an alias that redirects to the latest release; they never expire).

Cross-cutting rule that runs through the whole document: **the cheapest work is the work you don't do.** Every field you don't query, every row you don't fetch, every re-evaluation you avoid, and every process instance you archive is performance gained without writing code.

**Contents:** 1. Methodology: measure before optimizing · 2. Record type queries
· 3. Interfaces: evaluation cost · 4. Processes: memory footprint and scalability
· 5. Data and records: sync vs. direct access · 6. Integrations · 7. Diagnostic tools
· 8. Actionable summary (KPIs and limits) · Sources

---

## 1. Methodology: measure before optimizing

✅ **Measure with diagnostic tools before touching anything.** Every object has its own instrument: `Performance Details` in interfaces, `Query Performance` in the Monitor, the optimization process reports in processes, and Health Check at the environment level. Optimizing by intuition wastes effort on something that isn't the bottleneck.
Source: [Interface Performance Best Practices](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **Test with production data volumes, not development ones.** Performance in your development environment will differ from production; for a realistic assessment, replicate production volumes in the test environment. A screen that runs fine with 10 rows can collapse with 100,000.
Source: [Asynchronous Loading — Identifying slow-loading components](https://docs.appian.com/suite/help/latest/async_loading.html)

❌ **Anti-pattern:** declaring "it's fast" after testing with tables that are nearly empty. The real cost only shows up with data.

✅ **Test like production, on a schedule.** Load testing is expected above ~100 concurrent users. Cover ≥ 80 % of the real workload with think time; run a 1-user smoke first, then peak (1 h), endurance (8 h) and stress (≈ 4× users); never on an empty database — load production-like volume (≥ 1 year of data; 3–5 years in a hardening sprint), re-sync records after bulk loads, and repeat the volume test every 4–5 sprints. Keep findings as a prioritized backlog; Appian's Locust library is the reference tool.
Source: [Appian Max — Performance Testing Methodology](https://community.appian.com/architecture-29/performance-testing-methodology-1250) · [Appian Max — Database Volume Testing](https://community.appian.com/architecture-29/best-practices-database-volume-testing-1325) · [Appian Max — Performance and Load Testing](https://community.appian.com/platform-30/performance-and-load-testing-1251) · [Appian Max — Recommended Environments](https://community.appian.com/platform-30/recommended-environments-1221)

---

## 2. Record type queries

> **The single home for query mechanics in this skill.** `02-interfaces-sail.md` § 2 keeps only what
> is specific to querying from a screen and points here for the rest. The official Appian skill goes
> deeper still in `references/query-record-type-patterns.md` (filters, sorting, relationships,
> aggregations and paging, with a recipe per case) — **load it before writing a query whose shape is
> not already in this section.**
> **Without that skill installed**, the platform sources cited under each rule are what it is built
> from.

How you retrieve data directly impacts your application's speed and responsiveness. Guiding principle: **only fetch the data you need.**

✅ **Specify the exact fields in the `fields` parameter; don't use `a!selectionFields()` in production.** The more data you query, the longer it takes to load. `a!selectionFields()` fetches all fields, including those of related record types, driving up load time. Reserve it for when you genuinely need every field.
Source: [Record Type Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)

⚠️ **Trap:** if you leave `fields` empty in `a!queryRecordByIdentifier()`, only the base record type's primary key is returned. It's a silent failure: the query "works" but brings back nothing useful.
Source: [a!queryRecordByIdentifier() — Using the fields parameter](https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html)

✅ **Exclude expensive fields from high-volume queries:** *real-time custom record fields* and *Extra Long Text fields*. They're costly to return and penalize large grids and listings.
Source: [Query Performance Best Practices — Best practice checklist](https://docs.appian.com/suite/help/latest/query-best-practices.html)

✅ **Always paginate with `a!pagingInfo(startIndex, batchSize)` and filter to narrow the result set.** Returning 5,000 rows to display 5 wastes resources.
Source: [Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)

❌ **Don't query inside a loop (N+1 pattern).** `a!queryRecordByIdentifier()` **should not be used inside a loop**: if you need more than one base record or more than 100 related records, query the related record type separately in a single query.
Source: [a!queryRecordByIdentifier() — Usage considerations](https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html)

✅ **Know the ceiling of each query function.** `a!queryRecordByIdentifier()` returns **one** base record and up to **250** related records per relationship (automatic batching). `a!queryRecordType()` returns one or several and up to **100** related records per relationship (manual batching with `a!pagingInfo`). Choose based on what you need: `byIdentifier` for single-record detail views; `queryRecordType` for listings.
Source: [a!queryRecordByIdentifier() versus a!queryRecordType()](https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html)

✅ **On UNsynced record types, apply filters and sorts on the base record type, not on related ones.** For complex filtering or sorting on unsynced data, consider a database view instead of resolving it in the query.
Source: [Query Performance Best Practices — Best practice checklist](https://docs.appian.com/suite/help/latest/query-best-practices.html)

⚠️ **5,000-row ceiling on record-type-powered components.** Every records-powered component (grid, chart, dropdown, checkbox…) displays a maximum of **5,000 rows**, and you shouldn't get close to that number: paginate, filter, or aggregate. It's a platform limit, not a target.
Source: [Row limit for records-powered components](https://docs.appian.com/suite/help/latest/records-powered-components.html)

✅ **Filter by indexed fields.** Filtering and sorting by columns indexed in the source database is what keeps the query fast at volume. *(The index itself is a database design decision: doc 01 §8.1 and §12.3.)*
Source: [Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)

⚠️ **Database queries have their own limits.** `a!queryEntity` and query rules time out after **10 s** (`conf.data.query.timeout`; not configurable on Appian Cloud; not applied to Query Database) and stop at **5 MB** of result per query (`conf.data.query.memory.limit`); record type queries time out at 65 s. `fetchTotalCount: true` runs the query twice — ask for it only where a total is shown. `ignoreFiltersWithEmptyValues` plus a missing input returns the whole table: always cap the batch.
Source: [Post-Install Configurations — Query limits to external databases](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#query-limits-to-external-databases) · [KB-1681](https://community.appian.com/infrastructure-37/kb-1681-unable-to-retrieve-data-due-to-query-timeout-859) · [Appian Max — An Introduction to Query Optimization](https://community.appian.com/architecture-29/an-introduction-to-query-optimization-1311) · [Appian Max — Antipatterns](https://community.appian.com/architecture-29/antipatterns-solution-design-mistakes-to-avoid-in-appian-1225)

---

## 3. Interfaces: evaluation cost

Principle: **every user interaction re-evaluates the entire interface** (entering a value, pressing a button, changing a filter). Everything inside a component parameter is recomputed on every re-evaluation.

✅ **Put expensive computations in local variables, not in component parameters.** A local variable is only re-evaluated when the interface loads, when it's updated via `saveInto`, or when another local variable it references changes; a parameter is recomputed on every interaction.
Source: [Interface Performance — Local variable best practices](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **Design independent queries so they evaluate in parallel.** If a local variable holding a query references another local variable holding a query, they evaluate serially (one waits for the other). Rewrite them so they don't depend on each other and they'll evaluate at the same time, reducing total time.
Source: [Interface Performance — Set them up to evaluate in parallel](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **Defer loading slow data with asynchronous loading.** Use `a!asyncVariable()`, or the `loadDataAsync` parameter on read-only grids, charts, and KPIs powered by record data. The user sees and can interact with the rest of the screen while the slow data loads (with skeletons). Rule of thumb: apply it to any data that takes **more than 500 ms**.
Source: [Asynchronous Loading — When to enable async loading](https://docs.appian.com/suite/help/latest/async_loading.html)

❌ **Don't overuse async.** Every `a!asyncVariable()` consumes additional server resources; overusing it degrades the environment. **Recommended limit: 7 async variables per interface.** Don't apply it to data that's already fast (<500 ms): the skeleton flicker is more annoying than an instant load.
Source: [a!asyncVariable() — Performance considerations](https://docs.appian.com/suite/help/latest/fnc_evaluation_a_asyncvariable.html)

✅ **In interfaces that display a lot of data (reporting dashboards), reduce user interactions.** Every filter or editable field triggers a full re-evaluation with all its queries. Fewer interactions = less waiting.
Source: [Interface Performance — Don't add a lot of user interactions](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **In `and()`, `or()`, and `match()`, put expensive computations last.** These functions short-circuit: if a cheap earlier condition already decides the result, the expensive one never runs.
Source: [Interface Performance — Put expensive computations last](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **Don't wrap text in `a!richTextItem()` if you're not going to style it.** It's evaluation cost for nothing.
Source: [Interface Performance — Don't wrap text in a!richTextItem()](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **In grids with conditional columns, use the `fields` parameter of `a!recordData()`** to specify which fields to query and when, instead of fetching them all.
Source: [Query Performance Best Practices — Verify Grid Logic](https://docs.appian.com/suite/help/latest/query-best-practices.html)

✅ **Use `rv!identifier` in record views and related actions with dynamic start forms** to avoid over-fetching record data.
Source: [Query Performance Best Practices — Best practice checklist](https://docs.appian.com/suite/help/latest/query-best-practices.html)

✅ **`if()`, `choose()`, and `showWhen: false` don't evaluate the hidden branch or component.** This is the main lever for not paying for what isn't shown: the false branch of an `if()`/`choose()` and any component with `showWhen: false` are skipped entirely during evaluation. Break large forms (multi-step wizards) so each step is wrapped in a `choose()` or `showWhen`, so only the visible step is computed instead of the whole screen at once.
Source: [Interface Performance — Conditional logic](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **Control when a piece of data re-evaluates with `a!refreshVariable()` instead of reloading everything.** Its parameters (`refreshAlways`, `refreshInterval`, `refreshOnReferencedVarChange`, `refreshOnVarChange`, and `refreshAfter: "RECORD_ACTION"`) set exactly what triggers that variable's re-evaluation, avoiding recomputing expensive queries on every interaction. In grids and charts powered by record data, also use their refresh parameters to control when they re-query.
Source: [Interface Performance — Local variable best practices](https://docs.appian.com/suite/help/latest/interface-performance.html) · [Local Variables — a!refreshVariable()](https://docs.appian.com/suite/help/latest/Local_Variables.html)

✅ **Write memory-efficient expressions.** Three rules that bound memory consumption during evaluation: **never use `batchSize: -1`** (it fetches the result with no limit and can blow up memory — always paginate); **keep loops (`a!forEach`) under ~500 items**; and **don't nest more than 2 levels** of functions that iterate over arrays. Prefer array functions (`a!forEach`, `filter`, `reduce`) over iterating with indexes.
Source: [Expressions Best Practices — Designing memory-efficient expressions](https://docs.appian.com/suite/help/latest/expressions-best-practices.html)

⚠️ **Memory Circuit Breaker:** an expression that exceeds **100,000 AMUs** (≈ 1 KB each) fails on its own, whatever the heap size. It is the hard backstop behind the rules above.
Source: [Memory Circuit Breaker](https://docs.appian.com/suite/help/latest/Memory_Circuit_Breaker.html)

✅ **Browser time is the other half: it depends almost entirely on the number of visible components.** Fewer components per screen (split big forms into wizard steps, hide what isn't needed) is what shortens rendering; hidden components aren't evaluated or drawn. `refreshInterval` accepts only 0.5, 1, 2, 3, 4, 5, 10, 30 or 60 minutes, and a `refreshAlways` variable is recomputed on every evaluation — keep slow queries out of it.
Source: [SAIL Performance — Browser processing / Local variables](https://docs.appian.com/suite/help/latest/SAIL_Performance.html) · [a!refreshVariable()](https://docs.appian.com/suite/help/latest/fnc_evaluation_a_refreshvariable.html)

✅ **Records UX performance levers:** several record actions on one screen (one per grid row especially) → style `"MENU"`/`"MENU_ICON"`, whose `securityOnDemand` (default `true`) checks action security only when the menu opens; split a heavy Summary view into several views with only the fastest data on Summary; in feed-style record list views, **no integrations or looping functions** (the expression runs once per row); in complex record views use `rv!identifier` + `a!queryRecordByIdentifier()` instead of `rv!record`.
Source: [Interface Performance — Multiple record actions in a menu style](https://docs.appian.com/suite/help/latest/interface-performance.html) · [Health Check — Slow record interfaces and actions](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#slow-record-interfaces-and-actions) · [Query Performance Best Practices — rv!identifier](https://docs.appian.com/suite/help/latest/query-best-practices.html#use-rvidentifier-instead-of-rvrecord-for-record-views-with-complex-interfaces)

⚠️ **Interface context has a hard 200 MB limit** (uncompressed): beyond it the interface won't even open in the designer. Appian Max's review targets: pickers returning fewer than 50 suggestions, at most ~3 queries per page, search triggered by a button rather than every keystroke.
Source: [KB-1828](https://community.appian.com/application-design-33/kb-1828-interface-in-design-loads-with-cannot-interpret-context-for-ui-expression-reason-bindings-error-946) · [Appian Max — Interface Performance and Debugging](https://community.appian.com/architecture-29/interface-performance-and-debugging-1320)

---

## 4. Processes: memory footprint and scalability

Official Appian Efficiency Tip: **keep processes short-lived.** Reducing instance lifespan significantly improves memory usage and scalability.
Source: [Analyzing Process Model Performance](https://docs.appian.com/suite/help/latest/analyzing-process-model-performance.html)

✅ **Configure aggressive archiving/deletion policies for completed instances.** Completed processes that aren't archived or deleted keep occupying engine memory; the Health Check flags cleanup delays above **7 days**. Archiving frees memory, but much of it stays reserved as pre-allocated space that new processes reuse (only an engine restart releases reserved-but-unused memory), so prevention — short-lived processes plus automatic cleanup — is key.
Source: [KB-2011 How to address high memory usage in Appian Cloud](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047) · [Configuring Archived Processes](https://docs.appian.com/suite/help/latest/Configuring_Archived_Processes.html) · [Health Check — Long cleanup delay for completed processes](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#long-cleanup-delay-for-completed-processes)

✅ **Put a timer on processes users rarely complete.** Without one, those instances live in memory forever. An `Intermediate Event - Timer` that closes the process after a deadline prevents accumulation.
Source: [KB-2011 High memory usage](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047)

✅ **Keep process variables few and small.** Appian recommends **≤ 100 process variables** per model (more complicates maintenance and drives up memory consumption). Each version of a large PV is saved in the history and grows over time. Convert PVs into *activity class parameters* where applicable, or split into subprocesses.
Source: [Appian Design Guidance — Too many process variables](https://docs.appian.com/suite/help/latest/appian-recommendations.html)

✅ **Split large models into subprocesses.** Appian recommends **≤ 50 nodes** per model; beyond that it complicates maintenance, raises memory consumption, and lengthens completion time.
Source: [Appian Design Guidance — Too many nodes](https://docs.appian.com/suite/help/latest/appian-recommendations.html)

✅ **Remove unused process variables.** They add nothing and clutter memory and maintainability.
Source: [Appian Design Guidance — Unused process variable](https://docs.appian.com/suite/help/latest/appian-recommendations.html)

✅ **Factors that bloat a process's footprint** (review them when redesigning): the model definition and each node's, the number and **value** of process variables, the length of the process history, and any notes/attachments the instance carries. Watch them in the Monitor → *Process Model Metrics*.
Source: [Monitor View — Monitoring process model AMU](https://docs.appian.com/suite/help/latest/monitoring_view.html)

⚠️ **Application server heap** (3 GB by default on Appian Cloud): frequent garbage collection is the warning sign, and an OutOfMemoryError restarts the server — a full outage on a single-node site. The usual causes are design causes: large query results, document generation in plug-ins, very large PVs. Filter and batch, cap upload sizes and stagger bulk work instead of asking for more heap.
Source: [KB-2288](https://community.appian.com/performance-70/kb-2288-application-server-heap-memory-faq-15935)

### Autoscale (advanced/premium tier)

✅ **With Autoscale, keep process variables under 5 MB.** Test with the largest data volume you expect. Prefer more small models whose PVs hold less, over a few complex models with large PVs.
Source: [Autoscale Patterns and Best Practices — Keep process variables small](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

✅ **Dynamically scale data fabric queries** to support the query load of autoscaled processes (avoids manual scaling). Requested via a support case.
Source: [Autoscale Patterns and Best Practices — Query throughput](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

⚠️ **Platform limits under Autoscale:** nodes **time out at 90 seconds** (AI skills: the docs give 1.5 min and disagree on whether Long Running lifts it — doc 12 §10.0); processes start up to a maximum of **700 per minute** (above that they go to a queue of up to **1 million**; if the queue fills up, the Start Process node fails). A node runs up to **10,000 times per process instance**; ⓥ one Start Process node with MNI starts up to **10,000** instances (MNI in autoscale from 26.5); ⓥ activity chaining (from 26.4) has a **30 s** execution timeout plus a **10-minute** timeout from the user's click. Use batching in web API calls that start processes.
Source: [Autoscale Patterns and Best Practices](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html) · [Start Process Smart Service — Usage considerations](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html#usage-considerations)

⚠️ **Autoscaled process data is kept for a limited time:** completed without errors **7 days**, with errors **14 days**, active **90 days**. Anything needed for reporting or audit must be written to the database/records, not read from process history.
Source: [Monitoring Autoscaled Processes — Process data retention](https://docs.appian.com/suite/help/latest/monitoring-autoscaled-processes.html#process-data-retention)

### Process reports (task lists, process-backed grids)

Process reports run in real time and are **not cached**; the ones users open often must be tuned. Target: **≤ 500 ms** to display; the analytics engine cuts a report at `MAXIMUM_REPORT_MS` (default **2,000 ms**, cannot exceed 15,000 ms). ⓥ From 26.9, `a!queryTaskList()` queries tasks from standard and autoscaled processes directly in an interface, without a process report ([a!queryTaskList()](https://docs.appian.com/suite/help/latest/fnc_system_a_querytasklist.html)).

✅ **Design the process model with reporting in mind:** when a report spans several models, store the data in a process variable with the **same name in every model**; keep status columns **numeric** (integers), not text.
Source: [Report Performance Details — Designing process models with reporting in mind](https://docs.appian.com/suite/help/latest/Report_Performance_Details.html#designing-process-models-with-reporting-in-mind) · [Post-Install Configurations — Report timeout settings](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#report-timeout-settings)

✅ **Several filtered reports rather than one monolithic report users page through.** Rendering the last page costs more than the first, and filters on **dates and numbers** are faster than text (case-insensitive text is the slowest).

✅ **Keep sort columns simple:** sort by grouped columns, not aggregated ones; no functions or `if()` in the sort column; don't mix data types in a column. Columns not used to filter, group or sort are only evaluated for the visible page, so complex expressions belong there.

❌ **No expressions in drill-down paths:** they are evaluated for every item, not just the visible page.

✅ **Aggregate over simple report variables;** text aggregation is slower than numeric.

Source: [Process Report Performance Details — Optimizing process reports](https://docs.appian.com/suite/help/latest/Report_Performance_Details.html#optimizing-process-reports)

---

## 5. Data and records: sync vs. direct access

✅ **Prefer synced record types (Optimized Data Access)** when you want automatic performance optimization and full access to data fabric capabilities. Sync caches the data in Appian's data service, giving fast queries regardless of source complexity.
Source: [Record Type Data Access](https://docs.appian.com/suite/help/latest/about-data-sync.html)

✅ **Use Direct Data Access only** when you need real-time data modified outside Appian and syncing is impractical. It queries the source directly and depends on its native performance.
Source: [Record Type Data Access](https://docs.appian.com/suite/help/latest/about-data-sync.html)

⚠️ **Platform limits for sync (by capability tier):**

| Tier | Maximum synced rows per record type |
|---|---|
| Standard | **4 million** |
| Advanced | **20 million** |
| Premium | No fixed limit |

Additionally, **every record type supports up to 100 fields**, including custom record fields. If you expect to exceed your tier's limit, use **sync filters** or switch to direct access.
Source: [Record Type Data Access — row limits & field limit](https://docs.appian.com/suite/help/latest/about-data-sync.html)

✅ **Add sync filters to your largest synced record types** so only the data the application needs gets synced. It's the main lever for maintaining performance at high volume.
Source: [Configure Sync Options](https://docs.appian.com/suite/help/latest/records-data-sync.html)

✅ **Schedule full syncs outside peak hours**, and if you have several synced record types, stagger their full syncs at different times for optimal performance.
Source: [Configure Sync Options](https://docs.appian.com/suite/help/latest/records-data-sync.html)

✅ **Enable "Keep data available at high volumes" on your fastest-growing record types** (histories, audit logs; database sources in tiers with a row limit — doc 01 §3.2). It's the sync option designed for high-growth record types: it sustains query performance as volume grows over time. Check its status in the record type's monitoring details.
Source: [Configure Sync Options — Keep data available at high volumes](https://docs.appian.com/suite/help/latest/records-data-sync.html) · [Records Monitoring Details](https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html)

✅ **Calculated custom record fields: sync-time vs. runtime.** *Real-time custom record fields* are computed on every query and are expensive: exclude them from high-volume queries (see §2). Sync-time calculated fields are materialized once per sync and are cheap to read, but they bypass field-level security. Choose based on cost and security.
Source: [Query Performance Best Practices — Best practice checklist](https://docs.appian.com/suite/help/latest/query-best-practices.html)

⚠️ **Write throughput under Autoscale:** if your autoscaled processes write to synced record types above **15,000 transactions per minute** (summed across all apps), apply the incremental-write guidance to work around the limit. (Don't confuse this with the "30,000/min" figure from older release notes, which was the data fabric's **general** write capacity, not this specific autoscale threshold.)
Source: [Autoscale Patterns — Write throughput considerations](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)
The pattern the docs link to (**deferred sync**): autoscaled writers write through a separate data store that doesn't auto-sync and keep `modifiedOn` current; a non-autoscaled process every ~5 minutes syncs the changed IDs with Sync Records (≤ 1,000 per call). Source: [Appian Max — Writing to Synced Record Types at High Throughput](https://community.appian.com/architecture-29/writing-to-synced-record-types-at-high-throughput-1397).

✅ **Database indexes.** For unsynced record types, filtering/sorting by columns indexed at the source is what sustains the query at volume; for complex logic, materialize it in an indexed database view instead of in the query. On Appian Cloud, the database administration page adds the tooling (slow query log, table metadata, page compression) — see doc 01 §12.
Source: [Query Performance Best Practices — unsynced record types](https://docs.appian.com/suite/help/latest/query-best-practices.html) · [Appian Cloud Database Administration — Best practices](https://docs.appian.com/suite/help/latest/appian-cloud-database-administration.html#best-practices)

---

## 6. Integrations

✅ **Always configure an explicit timeout on the HTTP integration.** The *Timeout (sec)* field covers the full runtime (prepare + execute + transform). **If you leave it blank, the integration runs indefinitely** until it responds or the connection fails — a hung source can block resources forever.
Source: [Integration Object — HTTP integration definition](https://docs.appian.com/suite/help/latest/Integration_Object.html)

✅ **Asynchronous loading for slow integrations in interfaces.** Async loading (§3) is designed precisely for "slow external systems you don't control": the user isn't blocked waiting on a third party.
Source: [Interface Performance Best Practices](https://docs.appian.com/suite/help/latest/interface-performance.html)

✅ **In processes, protect external calls with retries and avoid long-running ones.** Autoscaled nodes time out at 90 s; in standard processes an unattended activity must finish within 60 minutes or the process pauses by exception. Build a retry pattern with a timer + counter for unreliable sources instead of leaving the node waiting; governing retries (backoff, attempts, idempotency) is doc 11 §3.
Source: [Autoscale Patterns — Avoid long-running calls to external systems](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html) · [Process Node Properties — Assignment tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#assignment-tab)

⚠️ **Size limits on the HTTP integration body:** the request body cannot exceed **5 MB** (the size of documents sent doesn't count toward this limit); base64 files, up to **75 MB** combined; binary files, recommended to keep them under **250 MB**.
Source: [Integration Object — Body size limitations](https://docs.appian.com/suite/help/latest/Integration_Object.html)

✅ **Synchronous by default, asynchronous for what's parallelizable.** A synchronous call guarantees the step finishes before continuing and gives consistent output; reserve async for tasks that can run in parallel (e.g., confirming by email while other processing continues). *(The doctrine is written for AI agent calls, but the sync-vs-async criterion is cross-cutting.)*
Source: [AI Agents FAQ — synchronous versus asynchronous](https://docs.appian.com/suite/help/latest/ai-agents-faq.html)

---

## 7. Diagnostic tools

✅ **Interfaces → Performance Details.** Run an evaluation and review *Parameters and Direct Children* to locate the slowest local variables or components. Watch out: async variables always show up as `<1 ms`, it doesn't measure their real time; and it measures **only expression evaluation** — not app-server overhead, network or browser rendering — so a screen can feel slow with good numbers here.
Source: [Asynchronous Loading — Identifying slow-loading components](https://docs.appian.com/suite/help/latest/async_loading.html) · [SAIL Performance](https://docs.appian.com/suite/help/latest/SAIL_Performance.html)

✅ **Queries → Monitor's Query Performance tab.** *Capture Query Performance* is **off by default**: enable it in production only while actively troubleshooting (it uses disk and can collect usernames), then turn it off.
Source: [Monitor View — Query Performance](https://docs.appian.com/suite/help/latest/monitoring_view.html#query-performance)

✅ **Records → Monitor's Record Response Times tab** (on by default): the 10 slowest responses per record list/view and the 30-day maximum. **Rules → Admin Console → Rule Performance** (30-day window, Designer runs excluded).
Source: [Monitor View — Record Response Times](https://docs.appian.com/suite/help/latest/monitoring_view.html#record-response-times) · [Rule Performance](https://docs.appian.com/suite/help/latest/admin-rule-performance.html)

✅ ⓥ **End-to-end user interactions → Trace Explorer** (Monitor view, 26.5, Appian Cloud) for front-end traces of sites, interfaces, record views and task forms; from 26.7 any user can capture a trace ID with **Interaction Diagnostics** to hand to the developer.
Source: [Monitor View — Trace Explorer](https://docs.appian.com/suite/help/latest/monitoring_view.html#trace-explorer)

✅ **Processes → optimization process reports + Monitor.** `Default Process Model Optimization Metrics` (average lag and completion) and `Default Process Optimization Metrics` (actual lag and completion) flag bottlenecks per node. The Monitor → *Process Model Metrics* shows memory (AMU), instance count, and % completion.
Source: [Analyzing Process Model Performance](https://docs.appian.com/suite/help/latest/analyzing-process-model-performance.html)

✅ **Environment → Health Check.** Run it regularly on every environment, **including Production**. It monitors server metrics (CPU, heap, disk), detects design and performance risks, and tracks capacity trends. Available to system administrators in the Admin Console; reports are managed from MyAppian.
Source: [Health Check](https://docs.appian.com/suite/help/latest/health-check.html) · [Monitoring Applications](https://docs.appian.com/suite/help/latest/monitoring-applications.html)

✅ **Log analysis.** During data collection, Health Check generates a zip with Appian's logs plus information on design patterns, configurations, and objects — a starting point for performance log analysis.
Source: [Monitoring Applications](https://docs.appian.com/suite/help/latest/monitoring-applications.html)

✅ **Prioritize by total cost:** fix the rules and interfaces with high executions × high average time first (the Health Check flags rules averaging over 2,000 ms). In the query performance log, read the phase: *Prepare* points at filters and nesting, *Execute* at the database (check the explain plan), *Transform* at result size.
Source: [Appian Max — Interface Performance and Debugging](https://community.appian.com/architecture-29/interface-performance-and-debugging-1320) · [Appian Max — Database Performance Best Practices](https://community.appian.com/architecture-29/database-performance-best-practices-1312)

---

## 8. Actionable summary (KPIs and limits)

**Performance KPIs to watch:** interface evaluation time (Performance Details), query time (Query Performance), per-node lag/completion (process reports), process AMU and % completion (Monitor), environment CPU/heap/disk (Health Check).

**Platform limits cited** (each with its source page).

> Note the distinction the table blurs: **hard limits** (technical ceilings the platform enforces)
> versus **recommended thresholds** — marked *(recommended)* — from Appian Design Guidance and Health
> Check. The latter are design indicators, not barriers: exceeding them **warns, it doesn't block**, and
> splitting an object purely to comply with them can hurt traceability. Tier limits and platform
> limits **change between releases**: if a decision depends on the exact number, confirm it for
> your environment before designing around it.

Other limits live in their own domain doc with their source: calculated fields per record type, text
lengths and unique fields (doc 01), record type query timeout and translation strings per set (doc 02),
MNI and Write Records per node (doc 03), default sync for a web service source (doc 07), agent tool
timeouts, parallel tool calls and multi-agent depth (doc 12). AI cost is measured in **AI actions**, not
in CPU or memory: its levers are in doc 12 §4.

| Scope | Limit | Source |
|---|---|---|
| Synced rows / record type | 4 M (Standard) · 20 M (Advanced) · no limit (Premium) | about-data-sync |
| Fields per record type | 100 (incl. custom fields) | about-data-sync |
| Related records per query | 100 (`queryRecordType`) · 250 (`byIdentifier`) | queryRecordByIdentifier |
| Rows in records-powered component (grid/chart/dropdown…) | 5,000 | records-powered-components |
| Async variables per interface | 7 (recommended) | async_loading |
| Threshold for async loading | > 500 ms | async_loading |
| Nodes per process model | 50 (recommended) | appian-recommendations |
| Process variables per model | 100 (recommended) | appian-recommendations |
| Process variable size (Autoscale) | 5 MB | autoscale-patterns-practices |
| Node timeout (Autoscale) | 90 s | autoscale-patterns-practices |
| Unattended activity (standard process) | 60 min, then paused by exception | Process_Node_and_Smart_Service_Properties |
| Node executions per process | 1,000 (`MAX_NODE_INSTANCES`) · 10,000 (Autoscale) | Post-Install_Configurations · autoscale-patterns-practices |
| Process starts (Autoscale) | 700/min · queue of 1 M | autoscale-patterns-practices |
| Autoscaled process data retention | 7 d (ok) · 14 d (errors) · 90 d (active) | monitoring-autoscaled-processes |
| Process report | ≤ 500 ms (recommended) · 2,000 ms timeout (default) | Report_Performance_Details · Post-Install_Configurations |
| Expression memory (circuit breaker) | 100,000 AMU | Memory_Circuit_Breaker |
| Database query (`a!queryEntity`, query rule) | 10 s timeout · 5 MB result | Post-Install_Configurations |
| Interface context | 200 MB (uncompressed) | KB-1828 |
| Synchronous request on Appian Cloud (export, dialog) | 5 min (load balancer) | KB-2293 |
| Writes to synced record (Autoscale) | 15,000 transactions/min | autoscale-patterns-practices |
| HTTP integration body | 5 MB (body) · 75 MB (base64) · 250 MB (binary, recommended) | Integration_Object |

---

## Sources

- [Record Type Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html)
- [Row limit for records-powered components (5,000 rows)](https://docs.appian.com/suite/help/latest/records-powered-components.html)
- [a!queryRecordByIdentifier() Function](https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html)
- [Interface Performance Best Practices](https://docs.appian.com/suite/help/latest/interface-performance.html)
- [Local Variables (a!refreshVariable())](https://docs.appian.com/suite/help/latest/Local_Variables.html)
- [Expressions Best Practices (memory-efficient expressions)](https://docs.appian.com/suite/help/latest/expressions-best-practices.html)
- [Asynchronous Loading](https://docs.appian.com/suite/help/latest/async_loading.html)
- [a!asyncVariable() Function](https://docs.appian.com/suite/help/latest/fnc_evaluation_a_asyncvariable.html)
- [Analyzing Process Model Performance](https://docs.appian.com/suite/help/latest/analyzing-process-model-performance.html)
- [Monitor View — Process Model Metrics](https://docs.appian.com/suite/help/latest/monitoring_view.html)
- [Process Report Performance Details](https://docs.appian.com/suite/help/latest/Report_Performance_Details.html)
- [Appian Design Guidance (Recommendations)](https://docs.appian.com/suite/help/latest/appian-recommendations.html)
- [Autoscale Patterns and Best Practices](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)
- [Record Type Data Access (about-data-sync)](https://docs.appian.com/suite/help/latest/about-data-sync.html)
- [Configure Sync Options (records-data-sync)](https://docs.appian.com/suite/help/latest/records-data-sync.html)
- [Records Monitoring Details](https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html)
- [Integration Object](https://docs.appian.com/suite/help/latest/Integration_Object.html)
- [AI Agents FAQ](https://docs.appian.com/suite/help/latest/ai-agents-faq.html)
- [Health Check](https://docs.appian.com/suite/help/latest/health-check.html)
- [Monitoring Applications](https://docs.appian.com/suite/help/latest/monitoring-applications.html)
- [KB-2011 How to address high memory usage in Appian Cloud environments](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047)
- [Configuring Archived Processes](https://docs.appian.com/suite/help/latest/Configuring_Archived_Processes.html) · [Understanding the Health Check Report](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html)
- [Monitoring Autoscaled Processes](https://docs.appian.com/suite/help/latest/monitoring-autoscaled-processes.html) · [Start Process Smart Service](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html) · [Post-Install Configurations](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html)
- [Memory Circuit Breaker](https://docs.appian.com/suite/help/latest/Memory_Circuit_Breaker.html) · [SAIL Performance](https://docs.appian.com/suite/help/latest/SAIL_Performance.html) · [a!refreshVariable()](https://docs.appian.com/suite/help/latest/fnc_evaluation_a_refreshvariable.html)
- [Rule Performance](https://docs.appian.com/suite/help/latest/admin-rule-performance.html) · [Appian Cloud Database Administration](https://docs.appian.com/suite/help/latest/appian-cloud-database-administration.html)
