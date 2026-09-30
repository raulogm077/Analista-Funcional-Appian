# Best Practices — Data Model and Record Types

> Official Appian doctrine for designing an application's data model: how to model entities as record types, when to sync, how to relate, type, secure and expose data to the end user, plus documents, record events and the database layer (views, stored procedures, Appian Cloud database). Every rule is anchored to the official documentation (`docs.appian.com/suite/help/latest/…`, an alias to the latest release). Verified against Appian 26.x.

**Contents:** 0. Guiding principle · 1. Plan the model before creating objects
· 2. Choose the data source and access method · 3. Synchronization (data sync): when, limits and what to sync
· 4. Relationships between record types · 5. Calculated fields (custom record fields)
· 6. Security in model design · 7. CDTs: when they still make sense · 8. Data types, precision, dates and keys
· 8.bis. Document management: folders vs record types
· 9. Design for the end user: list, views, actions, filters · 10. Data Fabric and reuse across applications
· 11. Record events: audit trail, activity log and process data
· 12. The database layer: views, direct SQL and Appian Cloud administration · Sources

---

## 0. Guiding principle

The **record type** is the central piece of Appian's data fabric and the primary way to work with data. For almost every use case, model your data as record types (not as CDT + data store) to access relationships, calculated fields, row-level security and AI capabilities.

- ✅ Use a record type to read, display, report and write data from a database, process, Salesforce or another web service; to relate data from different sources without writing SQL; and to secure at row level.
- ❌ Don't start a new model on CDT + Data Store Entity "out of habit": it's the legacy pattern and forgoes the data fabric.

Source: [About Record Types — When to use record types](https://docs.appian.com/suite/help/latest/Record_Type_Object.html) · [Objects that Access Data — When to use each object](https://docs.appian.com/suite/help/latest/working-with-data-in-appian.html#when-to-use-each-object)

---

## 1. Plan the model before creating objects

> **Where the order of creation lives.** The official Appian skill carries the full dependency-ordered
> change plan in `references/change-planning.md` — twelve steps and the complete graph, with the object
> types that **cannot be automated** marked `(manual)`, Connected Systems, Decision Objects, Record
> Actions and Portals among them. **Load it before sequencing any change that spans more than one
> object type, and do not restate its graph here.**
> **Without that skill installed**, the platform sources cited in this section give the same order for
> the types it covers.

Appian marks model planning as **the most critical step**: identifying which business entities deserve their own record type before touching Designer.

- ✅ List the people, places, things or events the app manages (e.g. Customers, Orders, Products). One record type = **one distinct business concept or one main process**.
- ✅ For each entity, list its attributes as fields; if an attribute requires a **list of values**, turn it into a separate entity (e.g. an Order with multiple lines → "Order Line" entity).
- ✅ Determine the relationships between entities before creating them.
- ❌ Don't cram independent concepts into the same record type "to save tables": it breaks relationships, security and queries later on.

Source: [Plan Your Data Model — Define business concepts](https://docs.appian.com/suite/help/latest/data-modeling-with-appian-records.html#define-business-concepts)

### 1.1 Catalog (lookup) data in its own record type

- ✅ Extract static, shared values (states, provinces, types, categories) into a **lookup record type** and relate it, instead of repeating the text in every entity.
- ❌ Don't duplicate a free-text field (`state`) in Customer and in Employee: it ends up with inconsistent data (a mix of abbreviations and full names). A related "State" record type avoids this.
- ✅ You can quickly generate the lookup record type by adding a **choice list field**.

Source: [Store lookup data in a separate record type](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#store-lookup-data-in-a-separate-record-type)

---

## 2. Choose the data source and access method

When you create a record type you choose a **source** and an **access method**. The method determines what type the record type is and which features you have available.

| Access method | Resulting type | Consequence |
|---|---|---|
| **Optimized Data Access** (with sync) | Synced record type | Recommended. Syncs and optimizes the data in Appian; **full access** to the data fabric (relationships, calculated fields, row-level security, smart search, Process HQ). |
| **Direct Data Access** (features enabled) | Unsynced record type | Direct query against MariaDB, MySQL, PostgreSQL or Snowflake; keeps **most** data fabric features; performance depends on the source DB; no row limit. |
| **Direct Data Access** (features disabled) | Legacy record type | Web service, process or a DB other than the four above. **No relationships or related features**; requires additional objects. Use only when syncing isn't an option. |

- ✅ By default, create **synced record types** whenever you can.
- ✅ Available data sources: **Database** (database-backed), **Web Service** (service-backed), **Process** (process-backed) and **data source shortcut** (e.g. Salesforce). If there's no source, generate a new table from the record type itself.
- ❌ Don't choose a legacy record type unless you need a source that isn't a supported DB/service and you can't sync; you lose relationships and everything that depends on them.

Source: [Types of record types](https://docs.appian.com/suite/help/latest/Record_Type_Object.html#types-of-record-types) · [Choose a Data Source](https://docs.appian.com/suite/help/latest/configure-record-data-source.html) · [Use synced record types (best practice)](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#use-synced-record-types)

### 2.1 What Direct Data Access (features enabled) loses compared to Optimized

Choosing Direct Data Access instead of syncing isn't free. Compared to a synced record type, **features enabled** gives up several capabilities:

| Capability | Optimized (synced) | Direct Data Access (features enabled) |
|---|---|---|
| **Primary key** | Supports **composite keys** | **Single PK required** — no composite key support |
| **Smart search** | Yes | No |
| **Process HQ process analysis** | Yes | No |
| **Sync-time calculated fields** | Yes | No (real-time only) |
| **Row filtering** | Sync filters (which rows exist) + record-level security (who sees them) | No sync filters and no default filters (legacy only); record-level security |
| **Relationships** | Yes | Yes (unlike legacy) |
| **Performance** | Stable (copy in the data service) | Depends on the source DB |

- ✅ Reserve features enabled for when you need to see changes made outside Appian **instantly** and syncing isn't an option; accept that you lose smart search, process analysis in Process HQ, sync-time calculated fields and sync filters.
- ❌ Don't choose features enabled expecting a composite key: it requires a **single PK**.

Source: [Direct data access — features enabled](https://docs.appian.com/suite/help/latest/about-data-sync.html#features-enabled)

---

## 3. Synchronization (data sync): when, limits and what to sync

Syncing is like caching: Appian runs queries against the synced copy in its data service, not against the source, so reads are faster and more consistent even when the query is complex.

### 3.1 When to sync

- ✅ Sync for stable performance, dynamic query scaling and access to **all** data fabric features.
- ✅ Use **Direct Data Access** (without sync) only when you need to see changes made outside Appian instantly and syncing isn't an option.
- ✅ It's valid to combine synced and unsynced in the same app: e.g. an unsynced record type with **all** of the history and synced ones with active subsets ("Active Orders", "Open Cases").

Source: [Optimized data access](https://docs.appian.com/suite/help/latest/about-data-sync.html#optimized-data-access) · [Synced and unsynced record types](https://docs.appian.com/suite/help/latest/Record_Type_Object.html#synced-record-types)

### 3.2 Row limit per synced record type

The limit depends on your **capability tier** — it's not a single number:

| Tier | Row limit per synced record type |
|---|---|
| **Premium** | No fixed limit |
| **Advanced** | Up to 20 million |
| **Standard** | Up to 4 million |

- ⚠️ The historical "50 million" and "2 million" limits that appear in older docs correspond to previous versions; **today the limit is the one for your tier**. Confirm the limit for your environment.
- ✅ Even if your tier has no limit, **configure sync filters** anyway: syncing unnecessary data consumes resources and degrades queries.
- ✅ Exceeding your tier's limit has two ways out: **sync filters** (sync only what you need) or switching to **Direct Data Access** (no row limit).
- ✅ For large or growing sources (typically Event History), enable **Keep data available at high volumes** to dynamically sync the most recent rows. It applies to database-backed record types in tiers with a row limit (not Premium); the sort field (the PK or a Date/Date and Time field, never a composite key) needs a **database index** (Appian can generate it). ⓥ In 26.3 it trimmed to the limit only at full syncs (required; a weekly one is auto-scheduled), smart service syncs could run up to **10% over the limit** until then, and incremental syncs had to be off. From 26.4 incremental and smart service syncs also trim the oldest rows, and fail only beyond 10% over the limit.

Source: [Row considerations for optimized data access](https://docs.appian.com/suite/help/latest/about-data-sync.html#optimized-data-access) · [Keep data available at high volumes](https://docs.appian.com/suite/help/latest/records-data-sync.html#keep-data-available-at-high-volumes)

### 3.3 Field and size limits (synced record type)

- **Maximum 100 fields** per record type, including calculated fields.
- **Maximum 40 calculated fields** (custom record fields) out of those 100. E.g.: if the record type already has 98 regular fields, only 2 calculated fields fit.
- **At least one primary key field** is required. **Composite keys** are only valid with **Optimized Data Access (synced)**; **Direct Data Access (features enabled) requires a single PK** — *"A single primary key field is required. The table cannot have a composite primary key."* The restriction depends on the **access method**, it isn't a general property of the record type (see §2.1). Source: [Direct data access — features enabled](https://docs.appian.com/suite/help/latest/about-data-sync.html#features-enabled).
- **Unique fields**: maximum **765 characters**.
- **Text tier** (aligned with §8): **Text** up to **255** characters; **Long Text** up to **4,000** (max. **2** per record type), where values that exceed that cap **get truncated**; **Extra Long Text** up to **64,000** (max. **3**; exceeding it fails the sync or write, and these fields can't be used in filters, sorts, aggregations or records-powered components). Move up a tier rather than risk truncation; the 4,000 cutoff belongs to **Long Text**, not Text.
- **Unsupported columns** for sync: BLOB, spatial, XML and user-defined types; plus engine-specific restrictions (MySQL excludes UUID and YEAR; PostgreSQL excludes JSON, UUID and XML). Check the list before syncing.
- **BIGINT/LONG** columns sync safely only within **±2,147,483,647** (the Integer range); larger values may not sync correctly.

- ✅ Sync **only the fields the app uses**; every extra field adds weight to every sync and every query.
- ❌ Don't sync huge text columns if you don't display them; if they exceed 64,000 characters, read/write them through a separate unsynced record type or CDT.

Source: [About Data Sync — Usage considerations](https://docs.appian.com/suite/help/latest/about-data-sync.html) · [About custom record fields (100/40 limit)](https://docs.appian.com/suite/help/latest/custom-record-fields.html#about-custom-record-fields)

### 3.4 Keeping synced data current

- ✅ Write using **smart services that sync automatically** (Write Records, Write to Data Store Entity on synced, Delete Records): changes are reflected in real time.
- ⚠️ **Not auto-synced:** Query Database, Execute Stored Procedure, plug-ins, Call Integration (except to Salesforce) and manual edits in the database. Follow them with **Sync Records** / `a!syncRecords()` — max **1,000 identifiers per call**; exceeding it fails the sync and makes the data unavailable, so loop.
- ✅ For changes made by **other systems**, use the **Sync Records smart service**, **scheduled incremental syncs** or a **scheduled full sync**. A full sync that runs over **4 hours** may time out: sync filters and fewer fields keep it short.
- ✅ ⓣ **Incremental syncs** (Advanced/Premium): database **tables** (not views) and service-backed record types; they need a **Last Modified** Date and Time field, fail above **50,000 rows** or **10 minutes**, don't coexist with a relationship-based sync filter, and **don't capture hard deletes** — pair them with a less frequent full sync. ⓥ In 26.3 they also required *Keep data available at high volumes* to be off.
- ✅ **Keep the audit fields** Appian generates (`createdBy`, `createdOn`, `modifiedBy`, `modifiedOn`) and fill `modifiedOn` on **every** write: if an incremental sync and a smart service sync hit the same row and either sees a null Last Modified value, both fail.
- ⚠️ **One table, several record types = several syncs:** every smart service sync on the table triggers a sync on each record type pointing at it. Don't duplicate record types over the same table without a reason.
- ✅ For Salesforce: 1,000 rows = 1 API call; size your API limit and use sync filters.

Source: [Keep synced data current](https://docs.appian.com/suite/help/latest/records-data-sync.html) · [Considerations for updating data](https://docs.appian.com/suite/help/latest/records-data-sync.html#considerations-for-updating-data) · [Schedule incremental syncs](https://docs.appian.com/suite/help/latest/records-data-sync.html#schedule-incremental-syncs) · [Records Monitoring — Incremental sync errors](https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html#incremental-sync-errors) · [Build Your Best Data Fabric — Sync changes efficiently](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#sync-changes-efficiently) · [Configure your data structure (default fields)](https://docs.appian.com/suite/help/latest/create-record-data-source.html#configure-your-data-structure) · [Salesforce API considerations](https://docs.appian.com/suite/help/latest/about-data-sync.html)

### 3.4.1 When a sync fails — availability options

| Option | Default | Effect |
|---|---|---|
| **Skip failed full and incremental syncs** | On for new record types | A failed scheduled sync is skipped; the previous data stays available (not for manual syncs or row-limit failures) |
| **Skip failed smart service syncs** | Off | Database-backed only: data stays available after a failed smart service sync (not for manual syncs or row-limit failures); only the first skip is logged — pair it with scheduled or recovery syncs |
| **Recover failed syncs** | Off | After a connection failure, a full re-sync starts at once; data is unavailable until it finishes |

- ⚠️ Sync failure **alerts** go only to system administrators and users with **Administrator** permission on the record type, only for scheduled full syncs and certain smart service syncs, and need outbound email. Decide who holds that role, or monitor sync status explicitly (doc 11 §5).

Source: [Configure sync options — Availability options](https://docs.appian.com/suite/help/latest/records-data-sync.html#availability-options) · [Records Monitoring — Sync failure alerts](https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html#sync-failure-alerts)

### 3.5 Sync filters and default filters — traps

- ✅ Use **sync filters** to bring in only the subset of rows the app needs: it reduces volume, speeds up queries and helps you stay clear of the tier limit.
- ⚠️ **`today()` in a sync filter freezes** at the value it had at the moment of the sync: it doesn't advance on its own with the calendar. A filter like "created in the last 30 days" stays stale until the next sync — schedule it or refresh it.
- ⚠️ A **sync filter on a related field** is only re-applied on a **full sync** of the base record type, not on incremental ones: changes in the related record type don't re-filter the rows until the next full sync.
- ✅ **Default filters** exist only on **legacy** record types. On synced ones, sync filters decide which rows exist and record-level security decides who sees them (a default filter carried over from an older version shows up as a **Security Expression**); on Direct Data Access ones, use record-level security. Neither default nor sync filters apply to **web service** sources — filter in the record data source expression instead.

Source: [Filter source data (sync filters)](https://docs.appian.com/suite/help/latest/records-filter-source-data.html) · [Default filters](https://docs.appian.com/suite/help/latest/default-filters.html) · [Record-Level Security — options](https://docs.appian.com/suite/help/latest/record-level-security.html#record-level-security-options)

---

## 4. Relationships between record types

Relationships connect data from different sources without SQL and are the foundation for queries, related security and AI features.

### 4.1 Types and modeling

- ✅ Supported types: **One-to-Many**, **Many-to-One**, **One-to-One**. Examples: an order has many lines (1:N); many customers in the same sector (N:1); an employee has one address (1:1).
- ✅ **Many-to-Many**: it isn't configured directly; model it with a **join record type** that has N:1 to each side (the "Order Line" pattern between Order and Product).
- ✅ Relationships require **Optimized** or **Direct Data Access (features enabled)**. **Legacy** doesn't support relationships.

Source: [Usage considerations for relationships](https://docs.appian.com/suite/help/latest/record-type-relationships.html#usage-considerations-for-relationships) · [Manage many-to-many with a join record type](https://docs.appian.com/suite/help/latest/data-modeling-with-appian-records.html#manage-many-to-many-relationships-with-a-join-record-type)

### 4.2 Bidirectionality and names

- ✅ Create **bidirectional** relationships: by default a relationship only exists on the record type where it was created. If you add an N:1 from Case → Case Type, also add a 1:N from Case Type → Case. It helps both people and AI models find the data.
- ✅ Use **suggested relationships** to create the bidirectional ones quickly.
- ✅ Give relationships **readable names** (relationship names): data stewards and AI use them to recognize the link. Convention: **camelCase**, matching the related record type's name, **without the application prefix** (`supportCases`, not `RE_supportCases`).

Source: [Create bi-directional record type relationships](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#create-bi-directional-record-type-relationships) · [Relationship names](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#relationship-names)

### 4.3 Composite keys and referential integrity

- ✅ With a **composite** primary key: it can't be the "one" side of a relationship. Relating **towards** a composite-key record type, only 1:N (with **Allow writes and deletes** forced on); relating **from** it, only N:1 using one of the key fields.
- ⚠️ Record type relationships **don't enforce referential integrity** by themselves: Appian trusts the source's rules. When you generate/update the source from the record type, Appian creates the foreign key using the common fields.
- ✅ If the source enforces referential integrity, keep the base record type and its related ones on **similar sync schedules** so the FKs stay consistent in Appian.
- ✅ If you're relating different sources (Salesforce + DB), **manage consistency in the app's logic**: no single system can guarantee it.
- ⚠️ **Deleting a parent: the relationship setting decides, the FK must agree.** When the relationship allows **writing and deleting related records** (the default when both record types share the source), **Delete Records** on the parent also deletes the related rows, in **one transaction**. When it doesn't, Appian sets the related foreign key to **null** (same database), leaves it untouched (different database), or the node **fails** (web service, process or Salesforce source). Declare the database FK as **`ON DELETE CASCADE`** or **`SET NULL`** so the source enforces the same behavior as the relationship. Views are not supported for writing or deleting related records.
- ✅ **Soft delete** when deleted rows must stay for audit, retention or referential integrity: an `isDeleted` (or `deletedOn`) field written with Write Records, plus a **sync filter** that keeps only non-deleted rows (built in expression mode, because it needs OR for null/false). On unsynced record types, hide them with record-level security instead.
- ✅ **Hard delete with a trail, dated reference data.** When rows must really go (privacy requests, volume), delete by indexed primary key, first copy the row as JSON into an audit table, and purge in batches of ≤ 1,000 rows off-hours. For reference data prefer `startDate`/`endDate` over an `isActive` flag, so historical rows keep their meaning; move rows older than the working window to mirror archive tables. Source: [Appian Max — Deleting Data in Appian Applications](https://community.appian.com/architecture-29/deleting-data-in-appian-applications-1277)

Source: [Relationship considerations — composite keys & referential integrity](https://docs.appian.com/suite/help/latest/record-type-relationships.html#relationship-considerations) · [Maintaining referential integrity (cascade delete)](https://docs.appian.com/suite/help/latest/record-type-relationships.html#maintaining-referential-integrity) · [Delete Records Smart Service](https://docs.appian.com/suite/help/latest/Delete_Records_Smart_Service.html) · [Manage record data — Delete data (soft delete)](https://docs.appian.com/suite/help/latest/manage-record-data.html#delete-data)

### 4.4 Avoiding deep joins (query performance)

The query mechanics — only the fields you need, no `a!selectionFields()` in production, expensive fields (real-time custom fields, Extra Long Text) out of high-volume queries, filters and sorts on the base record type when unsynced — live in `05-performance.md` §2. What belongs to the model:

- ✅ On related data, limit with `a!relatedRecordData()` (e.g. `limit: 3`) and paginate with `batchSize` instead of bringing in more rows than needed.
- ✅ In complex grids, query fields **conditionally** (the `fields` parameter of `a!recordData()`) so you don't over-fetch hidden columns; in complex record views use `rv!identifier` instead of `rv!record` to control when the query runs.

> Note: **real-time** calculated fields can reference related fields **up to 5 levels deep**; that it's possible doesn't mean it's advisable — each level makes evaluation more expensive.

Source: [Query Performance Best Practices](https://docs.appian.com/suite/help/latest/query-best-practices.html) · [Recipes for Querying Records — only specify the data you need](https://docs.appian.com/suite/help/latest/Query_Recipes.html)

---

## 5. Calculated fields (custom record fields)

They let you calculate, transform or aggregate existing data into new fields without touching the source. Only on record types with **sync**.

### 5.1 Sync-time vs real-time — choose based on the case

| | **Sync-time** | **Real-time** |
|---|---|---|
| When it's calculated | Only at sync time | Every time the field is referenced |
| Best use | Static calculations, formatting, logic on the base record type itself | Relative dates (`today()`) and data from **related** record types |
| Available fields | Fields on the record type and other sync-time fields | Fields, **related up to 5 levels**, and any calculated field |
| Objects | None | Constants |
| Unique values | Yes (can serve as the common field of a relationship) | No |
| Reference | `rv!record[recordType!X.fields.y]` | `recordType!X.fields.y` |

- ✅ Use **sync-time** for static logic (concatenating `firstName`+`lastName`, classifying by rules) and for values you need as the unique **common field** of a relationship.
- ✅ Use **real-time** for anything that depends on the moment (age as of today) or on related data.
- ✅ Typical case: `profit = salesPrice − cost`; or a **fullName** field so AI can correctly identify people when only a username is available.

Source: [Comparison: Sync-time vs real-time evaluations](https://docs.appian.com/suite/help/latest/custom-record-fields.html#comparison-sync-time-versus-real-time-evaluations) · [Optimize field usage](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html#optimize-field-usage)

### 5.2 Calculated fields and field-level security (a trap!)

- ⚠️ **Sync-time**: the user **sees** the calculated value even if they **don't** have access to the source field (it bypasses field-level security). Don't calculate at sync-time over a sensitive field the user shouldn't be able to derive.
- ✅ **Real-time**: if the user doesn't have access to a source field, the calculated field returns **null** and is hidden in Process HQ reports and dashboards. This is the safe behavior for protected data.

Source: [Custom record fields — Field-level security](https://docs.appian.com/suite/help/latest/custom-record-fields.html#comparison-sync-time-versus-real-time-evaluations)

---

## 6. Security in model design

Appian secures the record type **in layers**, from the broadest to the most granular; each layer builds on the previous one and is applied **everywhere** (lists, queries, grids, charts, related data).

| Layer | What it controls |
|---|---|
| **Object security** | Who can see/modify the record type (mandatory on all). |
| **Record-level security** | Which **rows** each user sees (row-level). |
| **Field-level security** | Which **fields** each user sees. |
| **Record view security** | Which **views** each user sees. |
| **Record action security** | Which **actions** each user sees. |

- ✅ Every record type needs **object security** configured — it's the base layer.
- ✅ Add **record-level security** when different users need to see different subsets of rows (plain language or expression). Available on synced and on unsynced (features enabled); **not** on legacy.
- ✅ Add **field-level security** for sensitive fields (salary, SSN). Remember the traps, which **aren't** the same depending on where you read from: in **interface components** the protected field arrives as **null** (it doesn't disappear), but in **queries** (`a!queryRecordType` / `a!queryRecordByIdentifier`) the field **isn't returned** in the output. In both cases filtering or sorting by it causes an error, and **sync-time** calculated fields **bypass it**. The detail is in `06-security.md` §5.2.
- ⚠️ Row-level and field-level security **don't apply in Appian Designer**: test them by logging in with a real user for each role. They're also out of scope in Process Insights (there, process security governs).

Source: [Secure Your Data Fabric — How security layers work together](https://docs.appian.com/suite/help/latest/secure-your-data-fabric.html) · [Record-Level Security](https://docs.appian.com/suite/help/latest/record-level-security.html) · [Overview of Record Type Security](https://docs.appian.com/suite/help/latest/appian-records-security.html)

---

## 7. CDTs: when they still make sense

For almost everything, use record types. The CDT is reserved for specific cases.

- ✅ Use a **CDT** when: you're working with a **legacy record type** connected via data store; you're defining a CDT as a **Java object** via a data type plug-in; it goes in/out of a **Call Web Service** or **plug-in**; it feeds an **Export to Excel/CSV** of a Data Store Entity (requires a CDT); or it's the output of **Extract from Document** (how to design the extraction itself — pattern, confidence, review — is in `12-ai-agents-and-skills.md` §10).
- ✅ If you have an old app built on CDT/DSE, **don't refactor the whole thing**: add **new record types** pointing at the same tables to unlock Process HQ, AI and new development, leaving the old part intact.
- ✅ CDT design (if you use one): **nested 1:1 and N:1** relationships; **flat 1:N and N:M** relationships to avoid performance problems when querying lists of lists.
- ⚠️ When you **write** a CDT to a DB, **all** fields get updated: if you don't fill in the rest, you overwrite them to null. Build the CDT with only the fields you're going to write.
- ⚠️ CDT/data store writes store a null Text as an **empty string**, while synced record types treat both as null: pick one convention per column and don't rely on `is null` filters in `a!queryEntity` ([KB-1253](https://community.appian.com/application-design-33/kb-1253-null-values-are-stored-as-empty-strings-when-writing-cdt-fields-to-a-database-539)).
- ❌ No **arrays of primitive types** in a CDT mapped to a data store (Design Guidance *"Primitive type array"*): their values can only be inserted, not updated (duplicates), and changes to them can't be synced. Use a child CDT (flat 1:N) instead.

Source: [CDT Design Guidance](https://docs.appian.com/suite/help/latest/cdt_design_guidance.html) · [Nested vs flat CDTs](https://docs.appian.com/suite/help/latest/cdt_design_guidance.html#nested-cdts) · [Use Data Fabric in Existing Apps](https://docs.appian.com/suite/help/latest/use-synced-record-types-in-existing-apps.html)

---

## 8. Data types, precision, dates and keys

When generating/updating the table from the record type, choose the type based on its semantics, not on convenience.

| Type | Recommended use |
|---|---|
| **Text** | Strings up to **255** characters. Most text fields. |
| **Long Text** | Up to **4,000** characters. Max. **2** per record type (MariaDB/MySQL row limits). Shows up as Text in the model. |
| **Extra Long Text** | Up to **64,000** characters. Max. **3** per record type. |
| **Number (Integer)** | Whole numbers: age, years, counters. |
| **Number (Decimal)** | **Double-precision** floating point: amounts, measurements. |
| **Date** | Date only. |
| **Date and Time** | Date and time, stored in **GMT**. Use it when the time matters. |
| **Boolean** | `true` / `false`. |
| **User** | Appian users (username fields). |
| **Group** | Appian groups. |
| **Document** | Document identifiers. **Only one** Document field per record type; if there's more info, generate a separate document management record type. |

- ✅ Choose **Integer** when you only need whole numbers and **Decimal** when you need precision (currency, measurements).
- ⚠️ **Decimal is double-precision floating point**: for monetary calculations requiring maximum accuracy, control the rounding in your logic; don't assume perfect decimal precision.
- ✅ **Date and Time is stored in GMT**: mind the time zone conversion when displaying and comparing. `today()` also returns the GMT day — the date traps are in doc 04 §11.

Source: [Configure field properties (types and limits)](https://docs.appian.com/suite/help/latest/create-record-data-source.html#configure-field-properties) · [Appian Data Types](https://docs.appian.com/suite/help/latest/Appian_Data_Types.html)

### 8.1 Primary keys and indexes

- ✅ **Every** source needs an explicit primary key to serve a record type; syncing requires it.
- ❌ Don't let Appian **auto-generate** the PK: that column can't be queried or referenced, so you won't be able to update existing rows.
- ✅ The PK can be **explicit** or **auto-generated by the DB**. If it's auto-generated, writing with a null PK creates a new row; if it isn't, writing with a null PK **fails**.
- ⚠️ **Composite keys** are only supported by an **Optimized (synced)** record type; with **Direct Data Access (features enabled)** the source must have a **single PK** (see §2.1). It isn't a general property of the record type: **it depends on the access method**.
- ✅ When you generate/update the source from the record type, Appian automatically creates the **foreign key** using the relationship's common fields, providing referential integrity at the source. Add the **indexes** your usual filters/sorting need in the DB (especially on unsynced record types, whose performance depends on the source).
- ✅ **Every table has a primary key or unique index, on a VARCHAR or integer column.** A duplicated or null key makes `totalCount` and paging wrong (it even changes with the batch size), and CHAR keys fail mapping verification ([KB-2120](https://community.appian.com/application-design-33/kb-2120-totalcount-returns-incorrect-results-1108), [KB-1413](https://community.appian.com/infrastructure-37/kb-1413-mysql-best-practices-primary-key-or-unique-index-on-every-table-675), [KB-1346](https://community.appian.com/application-design-33/kb-1346-char-datatype-does-not-map-as-a-foreign-key-616)).

Source: [Generating Database Tables — Primary keys](https://docs.appian.com/suite/help/latest/Generating_Database_Tables_from_CDTs.html) · [Maintaining referential integrity](https://docs.appian.com/suite/help/latest/record-type-relationships.html#relationship-considerations)

---

## 8.bis. Document management: folders vs record types

Appian has **two** official ways to store and secure documents; which one you use depends on what the document is for. A typical app handles both: attachments that users upload during the workflow (**workflow** documents) and logos or letter/report templates (**design** documents). Each one follows a different pattern.

### 8.bis.1 Design documents → folders (knowledge center + document folder)

- ✅ Use **folders** for documents that are uploaded in Appian Designer and are part of the app's **design**: a site's logo, a PDF/Word template for generating letters. They need to be **deployed** between environments because they're part of the design.
- ✅ It requires two objects: a **knowledge center** (root folder) and, inside it, a **document folder** (subfolder) where you organize the documents. Appian can generate them automatically when you create the application.
- ✅ Documents **inherit the folder's security**: secure the folder and the documents are secured.
- ❌ Don't put documents created by the workflow (resumes, case attachments) into folders: they don't stay linked to the data row and can't be secured at row level.

Source: [Manage Documents with Folders](https://docs.appian.com/suite/help/latest/folder-and-document-management.html) · [About Document Management — two ways to manage documents](https://docs.appian.com/suite/help/latest/about-doc-management.html) · [Design Objects — Content-management objects](https://docs.appian.com/suite/help/latest/design-objects.html#content-management-objects)

### 8.bis.2 Workflow documents → document management record type

- ✅ Use a **record type** when documents are created and maintained in the workflow and are **linked to data** (a supporting document tied to a request, an attachment on a case action). They aren't deployed between environments: they're born in the flow.
- ✅ A **document management record type** is simply a record type with **sync** (Optimized or Direct Data Access) and a field of type **Document**. Add whatever extra fields you need (e.g. `isActive`, document type) and the relationships to the record types with relevant data.
- ✅ When you create it, Appian automatically adds an **N:1 relationship to the Document record type** (name, description, extension…) and generates a document folder called **`<Record Type Name> Folder`** in the **Record Document System Knowledge Center** (provided out of the box, **not** accessible when browsing objects in Designer).
- ✅ To reference that generated folder in a **File Upload**, smart service or plug-in, use **`a!documentFolderForRecordType(recordType!YourRecordType)`**: it's the only way to point at the folder, since it can't be browsed to in Designer.
- ✅ The record type's **Documents** page monitors and cleans up: it shows **Total / Referenced / Orphaned** space (orphaned = documents in the folder with no row referencing them), lets you search, preview and download, and is where you adjust the **document cleanup schedule**.
- ⚠️ `a!documentFolderForRecordType()` is **incompatible with custom record fields** (sync-time and real-time): don't use it inside a calculated field.
- ⚠️ **Document management by record type** (Documents page, smart search over documents, Document chat) is an **Advanced/Premium** tier capability and may have **limits**: **it isn't available in every environment**. Confirm your environment's tier before basing the app's attachments on this pattern (this affects all of §8.bis.2).
- ✅ **Orphan cleanup cycle:** Appian purges documents in the folder that have no row referencing them via a **document cleanup schedule** (default **30 days**). It comes **enabled out of the box only** in environments that had no prior document management record types; if there were already some, you need to enable **"Record Document Cleanup"** in **Admin Console > Data Retention**. It's customizable or can be disabled **per record type** from its Documents page.

Source: [Manage Documents with Record Types](https://docs.appian.com/suite/help/latest/manage-docs-with-records.html) · [Clean up Appian-stored documents](https://docs.appian.com/suite/help/latest/manage-docs-with-records.html#clean-up-appian-stored-documents) · [Admin Console — Data Retention](https://docs.appian.com/suite/help/latest/admin-data-retention.html) · [a!documentFolderForRecordType()](https://docs.appian.com/suite/help/latest/fnc_system_documentFolderForRecordType.html)

### 8.bis.3 Generating documents from a template (letters, minutes, reports)

- ✅ To produce letters, minutes or reports, use a **template generation smart service** (*Document Generation* category): **MS Word 2007 Doc from Template** (`.docx`), **PDF Doc From Template**, **Text/HTML Doc From Template**.
- ✅ In Word/Text, the template marks each placeholder with a **substitution key** between triple hashes (`###Name###`); in the node's configuration you map each key to an expression or a `pv!`. The template is uploaded to a Document Management folder, and the user running the smart service needs **Author** access on that folder.
- ✅ The generated document can be written into the document management record type's folder (with `a!documentFolderForRecordType()`) so it stays linked and secured alongside the data.

Source: [MS Word 2007 Doc from Template](https://docs.appian.com/suite/help/latest/Word_Doc_from_Template_Smart_Service.html) · [PDF Doc From Template](https://docs.appian.com/suite/help/latest/PDF_Doc_From_Template_Smart_Service.html)

### 8.bis.4 Generation approach and document hygiene

- ✅ Before generating a document, ask whether a link or the browser's print is enough. Decide between **snapshot** (generate once and store — never regenerate a stored document from data that changed) and **on demand**; cap how many documents one action can fan out.
- ✅ The out-of-the-box Word template suits **≤ 10 static inputs**; beyond that — dynamic sections or tables, frequently changing formats — Appian Max points to the **Advanced Document Templating** AppMarket plug-in (a plug-in to govern, doc 11 §8).
- ❌ Never put `/ \ : ; < > " * ' ?` in generated file names.

Source: [Appian Max — How to Generate Appian Documents](https://community.appian.com/architecture-29/how-to-generate-appian-documents-1321) · [Appian Max — Comparison of Document Generation Approaches](https://community.appian.com/architecture-29/comparison-of-document-generation-approaches-15725)

---

## 9. Design for the end user: list, views, actions, filters

The record type automatically generates interfaces (list, views, actions) from the model.

### 9.1 Record list and grids

- ✅ Configure the **record list** (search, filter, export, act) once on the record type; then feed grids with `a!recordData()`, which reuse it.
- ✅ **Grid** style (default): tabular, configured in design mode, `fv!row`, **no row limit**, with Export to Excel. **Feed** style: vertical, news-like, `a!listViewItem()` expression, `rv!record`, **100-row limit**, no export.
- ✅ Apply a **logical order** that puts the most important thing at the top; keep values concise and consistently formatted per column.
- ❌ Don't use grids for large blocks of text; don't put **several related actions in the same cell** (put them above the grid or in separate columns).

Source: [Configure the Record List](https://docs.appian.com/suite/help/latest/record-list.html) · [SAIL — Grids (sort, filtering, actions)](https://docs.appian.com/suite/help/latest/sail/ux-grids.html)

### 9.2 Record actions

- ✅ **Record list actions**: start a process from the list, typically to **create** a new record (they don't need prior data).
- ✅ **Related actions**: start a process from **one** record, typically to **update or delete** that record.
- ✅ Reference these actions in records-powered grids or in the `Record Action Component`; secure them with **record action security**.

Source: [Configure Record Actions](https://docs.appian.com/suite/help/latest/record-actions.html)

### 9.3 User filters

- ✅ Add **user filters** (list and date-range) so the user can refine and **save** results; they're combinable (applied as AND between different filters, OR within the same one).
- ✅ Take advantage of the fact that Appian **automatically generates** a list user filter when you create an **N:1** relationship (it uses the common field; options = the first Text field after the PK of the related record type).
- ❌ **Never** put a user filter on a **field with field-level security** (e.g. financial data): filtering or sorting by it causes an error.
- ✅ Avoid user filters with more than **100 options**; users can save up to 10 filters per list — recommend saving filters with 10 or fewer selections.
- ✅ **Search:** limit the record list search to the fields users actually search (*Limit search to selected fields*, up to **10** Text/Integer/User/Group fields; avoid one-to-many related fields). ⓣ **Smart search** (synced record types, Advanced/Premium, not with Direct Data Access) is for free text: don't enable it on fields that hold lookup values — use user filters for those.

Source: [Add User Filters](https://docs.appian.com/suite/help/latest/filter-the-record-list.html) · [Search the record list — Limit search to selected fields](https://docs.appian.com/suite/help/latest/search-the-record-list.html#limit-search-to-selected-fields) · [Smart search — Requirements](https://docs.appian.com/suite/help/latest/records-smart-search.html#requirements-for-smart-search)

---

## 10. Data Fabric and reuse across applications

- ✅ The data fabric is a **unified, shareable** model: it relates record types from different sources into a single view. The same record type (e.g. a "State" lookup) is **reused** across multiple apps through relationships, avoiding data duplication.
- ✅ Give record types and relationships **standard names**, and give fields **display names + descriptions**: this is what lets Process HQ, the Data Fabric Chatbot and AI Copilot reason about your data. The data fabric is "the foundation for AI in Appian".
- ✅ To expose a record type as a dataset in Process HQ, enable **Show in Data Catalog**.
- ✅ Speed up the start: **Generate** multiple record types from several tables/views at once (including composite keys); Appian relates them by the existing foreign keys and secures them with the app's groups.

Source: [Build Your Best Data Fabric](https://docs.appian.com/suite/help/latest/build-best-data-fabric.html) · [Use Data Fabric in Existing Apps](https://docs.appian.com/suite/help/latest/use-synced-record-types-in-existing-apps.html) · [Data Fabric](https://docs.appian.com/suite/help/latest/data-fabric.html)

---

## 11. Record events: audit trail, activity log and process data

Record events capture **who did what, and when** on a record, feed the event history list component
(activity log, threaded comments) and provide the case + event data that Process HQ needs for process
mining. Decide them with the data model, not after the app is live: the history only exists from the
moment you start writing it.

- ✅ Configure record events only on record types that represent **major business concepts or
  processes** (the case: a request, an agreement, an order). ❌ Not on **lookup** record types.
- ✅ **Event types = the main steps of the process**, ideally each occurring once and in a known order,
  so an analysis can spot skipped, repeated or out-of-order steps.
- ✅ **Standardize names in the past tense** and keep them static ("Completed Financial Review"); put the
  dynamic details (who, amount) in **fields of the Event History record type**, never in the event name.
- ✅ Required record types: **Event History** (who, when, which event) and **Event Type Lookup** (the
  static list of event types); Reply Thread and Subscriber only if you use threaded conversations.
  Generate them from the record type's **Events** page (download the DB script) or reuse existing ones.
- ✅ Write case and event data **in the same Write Records node**.
- ⚠️ Supported on synced or unsynced record types backed by a **database table with a single primary
  key**. Not supported with composite keys, database views, web service sources or legacy record types.
- ⚠️ For Process HQ both the case and the Event History record type must be **synced**, with a 1:N
  relationship; each event needs a primary key, a link to the case, the activity and a timestamp.
- ✅ **Field-level change history** (who changed which field, from what to what) is a different need: capture it with database `AFTER INSERT/UPDATE` triggers into history tables that skip unchanged rows — process logic can't guarantee ordering — don't sync those trail tables, size them for the retention period, and show them on demand. Source: [Appian Max — Field Level Auditing](https://community.appian.com/architecture-29/field-level-auditing-1292)

Source: [About Record Events — Guidelines](https://docs.appian.com/suite/help/latest/record-events.html#guidelines-for-record-events) · [Configure Record Events](https://docs.appian.com/suite/help/latest/record-events-configuration.html) · [Process HQ Key Concepts — case and event history record types](https://docs.appian.com/suite/help/latest/key-pi-terms.html#case-record-type-and-event-history-record-type)

---

## 12. The database layer: views, direct SQL and Appian Cloud administration

### 12.1 Views as a record type source

- ✅ Pick the primary key **by hand** and make sure it is **truly unique**: duplicate key values in a batch fail the sync. Views don't support composite primary keys.
- ⚠️ Views are **read-only** for Appian: Write Records, Delete Records and related writes/deletes need tables; incremental syncs and record events don't support views either. Use a view for complex reads; write to the tables underneath.
- ✅ Check each view's **explain plan at production volume** (≈ 1 year of data). A view that can't be merged into the outer query (GROUP BY, DISTINCT, UNION) is computed in full before outer filters apply, so **don't nest views** and don't expect filters to be pushed down.
- ✅ For heavy aggregations, a **"materialized view"** on MariaDB: a real table, refreshed by a stored procedure that upserts the changed IDs, plus a nightly full refresh scheduled from a process.

Source: [Appian Max — Use Database and Materialized Views](https://community.appian.com/architecture-29/use-database-and-materialized-views-in-appian-1324) · [Appian Max — Database Performance Best Practices](https://community.appian.com/architecture-29/database-performance-best-practices-1312) · [Records Monitoring — Other sync errors](https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html#other-sync-errors) · [Write Records Smart Service](https://docs.appian.com/suite/help/latest/Write_Records_Smart_Service.html)

### 12.2 Query Database and stored procedures

- ✅ Use **Query Database** only when no other data capability fits (Health Check *"Use Query Database node in process model"* recommends placing it in a subprocess). It is **not** retried automatically (doc 03 §6) and its changes are **not** synced (§3.4).
- ✅ **Execute Stored Procedure** is the tool for bulk, set-based work; defaults: `timeout` **30 s**, **1,000 rows** per result set (extra rows are truncated) and 10,000 rows in total. Follow it with Sync Records when it touches synced tables.
- ✅ Give procedures **error handlers** (`SQLEXCEPTION`/`SQLWARNING` → `GET DIAGNOSTICS` → an error table); otherwise truncation warnings pass silently. The out-of-the-box smart service fails on duplicate or empty result column names and needs every IN/INOUT parameter; use `a!executeStoredProcedureForQuery()` only for reads.

Source: [Appian Max — Add Error Handling to Stored Procedures](https://community.appian.com/architecture-29/add-error-handling-to-stored-procedures-1371) · [Appian Max — Upgrade from the Execute Stored Procedure plug-in](https://community.appian.com/architecture-29/upgrade-from-execute-stored-procedure-plug-in-to-ootb-features-1276) · [Health Check — Use Query Database node in process model](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#use-query-database-node-in-process-model) · [Execute Stored Procedure — Limitations](https://docs.appian.com/suite/help/latest/Execute_Stored_Procedure_Smart_Service.html#limitations)

### 12.3 Appian Cloud database administration

- ✅ Normalized schema, the **indexes** your filters and sorts need, optimized queries and views, and performance tests in lower environments. Store only Appian application data in this database, and change it through Appian features.
- ❌ Don't use the **`DEFINER`** clause when creating views, procedures or triggers.
- ✅ The Cloud database runs in **GMT**, and Appian stores date-times in GMT: keep it that way if you use `NOW()`/`CURTIME()`.
- ✅ Diagnostics: `AppianProcess.slow_log` (statements over **7 s**), `AppianProcess.showTableMetadata('schema')` (rows, size, compression, fragmentation). **Page compression** (level 9) suits tables with over 2 M rows and 25 columns that are rarely updated; enabling it locks the table — test in a lower environment first.
- ✅ Connection pool: a data source connected system defaults to **100** connections per application server or engine (a custom JDBC one, 20); size the database for the total.
- ✅ **Schema shape:** normalized (3NF) tables for write-heavy data, and separate **reporting tables** refreshed by a scheduled stored procedure for heavy reads; indexes derived from the list of frequent queries; composite indexes with the most selective column first; `ANALYZE TABLE` after bulk loads. Sources: [Appian Max — A Case Study in Data Modeling](https://community.appian.com/architecture-29/a-case-study-in-data-modeling-for-an-appian-application-1285) · [Appian Max — An Introduction to Query Optimization](https://community.appian.com/architecture-29/an-introduction-to-query-optimization-1311).
- ⚠️ **Cloud MariaDB specifics:** `utf8mb4` everywhere (index keys then fit 191 characters) and one collation for all tables behind a view; no time zone tables (`CONVERT_TZ` returns NULL — store UTC); `GROUP_CONCAT` stops at 1,024 bytes; table names differing only by case break phpMyAdmin. Symptoms and fixes in doc 13 §2.
- ✅ **External database instead of the Cloud one:** keep the round trip under ~10 ms (25 ms at most); the Cloud database is written only through Appian and read from outside only through the Enhanced Data Pipeline. Source: [Appian Max — Customer Managed vs Cloud Managed Database](https://community.appian.com/architecture-29/customer-managed-vs-cloud-managed-database-1291).

Source: [Appian Cloud Database Administration — Best practices](https://docs.appian.com/suite/help/latest/appian-cloud-database-administration.html#best-practices) · [Enabling compression on tables](https://docs.appian.com/suite/help/latest/appian-cloud-database-administration.html#enabling-compression-on-tables) · [Configuring Relational Databases — Internationalization](https://docs.appian.com/suite/help/latest/Configuring_Relational_Databases.html#internationalization) · [Data Source Connected Systems — Properties](https://docs.appian.com/suite/help/latest/data-source-connected-systems.html#properties)

---

## Sources

- Plan Your Data Model — https://docs.appian.com/suite/help/latest/data-modeling-with-appian-records.html
- About Record Types — https://docs.appian.com/suite/help/latest/Record_Type_Object.html
- Types of record types — https://docs.appian.com/suite/help/latest/Record_Type_Object.html#types-of-record-types
- Choose a Data Source for Your Record Type — https://docs.appian.com/suite/help/latest/configure-record-data-source.html
- Generate a Database Table (field properties) — https://docs.appian.com/suite/help/latest/create-record-data-source.html
- Appian Data Types — https://docs.appian.com/suite/help/latest/Appian_Data_Types.html
- About Data Sync — https://docs.appian.com/suite/help/latest/about-data-sync.html
- Direct data access — features enabled (composite keys / features you lose) — https://docs.appian.com/suite/help/latest/about-data-sync.html#features-enabled
- Keep synced data current (smart services / scheduled syncs) — https://docs.appian.com/suite/help/latest/records-data-sync.html
- Filter source data (sync filters) — https://docs.appian.com/suite/help/latest/records-filter-source-data.html
- Default filters — https://docs.appian.com/suite/help/latest/default-filters.html
- Add Record Type Relationships — https://docs.appian.com/suite/help/latest/record-type-relationships.html
- Maintaining referential integrity (cascade delete) — https://docs.appian.com/suite/help/latest/record-type-relationships.html#maintaining-referential-integrity
- Build Your Best Data Fabric — https://docs.appian.com/suite/help/latest/build-best-data-fabric.html
- Create Custom Record Fields — https://docs.appian.com/suite/help/latest/custom-record-fields.html
- Secure Your Data Fabric — https://docs.appian.com/suite/help/latest/secure-your-data-fabric.html
- Record-Level Security — https://docs.appian.com/suite/help/latest/record-level-security.html
- Field-Level Security — https://docs.appian.com/suite/help/latest/field-level-security.html
- Overview of Record Type Security — https://docs.appian.com/suite/help/latest/appian-records-security.html
- CDT Design Guidance — https://docs.appian.com/suite/help/latest/cdt_design_guidance.html
- Custom Data Types (CDTs) — https://docs.appian.com/suite/help/latest/Custom_Data_Types.html
- Objects that Access Data (when to use each object) — https://docs.appian.com/suite/help/latest/working-with-data-in-appian.html
- Use Data Fabric in Existing Apps — https://docs.appian.com/suite/help/latest/use-synced-record-types-in-existing-apps.html
- Generating Database Tables from CDTs (primary keys) — https://docs.appian.com/suite/help/latest/Generating_Database_Tables_from_CDTs.html
- Configure the Record List — https://docs.appian.com/suite/help/latest/record-list.html
- Configure Record Actions — https://docs.appian.com/suite/help/latest/record-actions.html
- About Document Management — https://docs.appian.com/suite/help/latest/about-doc-management.html
- Manage Documents with Folders — https://docs.appian.com/suite/help/latest/folder-and-document-management.html
- Manage Documents with Record Types — https://docs.appian.com/suite/help/latest/manage-docs-with-records.html
- Clean up Appian-stored documents (orphans, cleanup schedule) — https://docs.appian.com/suite/help/latest/manage-docs-with-records.html#clean-up-appian-stored-documents
- Admin Console — Data Retention (Record Document Cleanup) — https://docs.appian.com/suite/help/latest/admin-data-retention.html
- a!documentFolderForRecordType() — https://docs.appian.com/suite/help/latest/fnc_system_documentFolderForRecordType.html
- Design Objects (content-management objects) — https://docs.appian.com/suite/help/latest/design-objects.html
- MS Word 2007 Doc from Template — https://docs.appian.com/suite/help/latest/Word_Doc_from_Template_Smart_Service.html
- PDF Doc From Template — https://docs.appian.com/suite/help/latest/PDF_Doc_From_Template_Smart_Service.html
- Add User Filters — https://docs.appian.com/suite/help/latest/filter-the-record-list.html
- Query Performance Best Practices — https://docs.appian.com/suite/help/latest/query-best-practices.html
- Recipes for Querying Records — https://docs.appian.com/suite/help/latest/Query_Recipes.html
- SAIL Grids (UX) — https://docs.appian.com/suite/help/latest/sail/ux-grids.html
- Data Fabric — https://docs.appian.com/suite/help/latest/data-fabric.html
- Appian Tiers (limits by tier) — https://docs.appian.com/suite/help/latest/Appian_Tiers.html
- About Record Events (guidelines) — https://docs.appian.com/suite/help/latest/record-events.html
- Configure Record Events — https://docs.appian.com/suite/help/latest/record-events-configuration.html
- Process HQ Key Concepts (case and event history record types) — https://docs.appian.com/suite/help/latest/key-pi-terms.html
- Delete Records Smart Service (related deletes, single transaction, FK delete behavior) — https://docs.appian.com/suite/help/latest/Delete_Records_Smart_Service.html
- Writing and Deleting Records Recipes (soft delete) — https://docs.appian.com/suite/help/latest/manage-record-data.html
- Sync Records Smart Service (1,000 identifiers) — https://docs.appian.com/suite/help/latest/Sync_Records_Smart_Service.html
- Records Monitoring Details (sync errors, alerts) — https://docs.appian.com/suite/help/latest/Records_Monitoring_Details.html
- Smart search — https://docs.appian.com/suite/help/latest/records-smart-search.html
- Search the record list — https://docs.appian.com/suite/help/latest/search-the-record-list.html
- Appian Design Guidance (primitive type array) — https://docs.appian.com/suite/help/latest/appian-recommendations.html#data-type-design-guidance
- Appian Cloud Database Administration — https://docs.appian.com/suite/help/latest/appian-cloud-database-administration.html
- Execute Stored Procedure Smart Service — https://docs.appian.com/suite/help/latest/Execute_Stored_Procedure_Smart_Service.html
- Data Source Connected Systems — https://docs.appian.com/suite/help/latest/data-source-connected-systems.html
