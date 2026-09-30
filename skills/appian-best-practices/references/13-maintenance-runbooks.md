# Maintenance runbooks — symptom → cause → action

> Field knowledge for keeping a live Appian application healthy, harvested from Appian's own Community
> Knowledge Base (the Solution Engineering KB and Appian Max) and filtered for **Appian Cloud 26.x**:
> self-managed-only articles and issues fixed before 26.x were left out. Open this doc when something is
> already failing, or when a design review asks "what goes wrong with this in production?".
>
> **How to read a row.** KB articles are dated, and many describe a known issue with a ticket number
> (AN-/AP-). Before applying a workaround, open the article, check its *Affected Versions* and whether
> the environment's hotfix already fixes it. When a KB article and `docs.appian.com` disagree for the
> environment's version, **the documentation wins** — the disagreements found are listed in §11. The
> durable design lessons behind these rows live in the domain docs (01–12); this doc is the runbook.

Convention: each table row is *Symptom · Cause · Action · Source*; ⓥ marks a version-dependent row.
Sources are listed at the end.

**Contents:** 0. Before diagnosing · 1. Processes and tasks · 2. Data, sync and the Appian Cloud database
· 3. Interfaces, rules and expressions · 4. Documents, email and generation
· 5. Deployment, packages and objects · 6. Integrations, certificates and network
· 7. Authentication, users and groups · 8. Browser, mobile and embedding · 9. AI · 10. Appian Cloud operations
· 11. KB advice that differs from the current documentation (the docs win) · Sources

---

## 0. Before diagnosing

- ✅ **Reproduce in a private window with extensions off.** If it works there, a browser extension (ad
  blockers are the usual suspect) or cached state is the cause ([KB-2108]). Monitoring agents that
  inject JavaScript (Dynatrace, AppDynamics, New Relic) cause random UI failures, sometimes first after
  an upgrade ([KB-1414]). A 401 with correct credentials and nothing in `login-audit.csv` is usually the
  browser cache ([KB-1567]).
- ✅ **Collect evidence the way Support needs it:** user, URL, timestamp with time zone, browser and
  network path (VPN, proxy), steps, and a HAR file. Record the HAR only on the affected site, avoid
  capturing the login unless login is the problem, and log out and back in afterwards so the tokens in
  the capture are dead ([KB-2048], [Analyzing Performance Issues]).
- ✅ **Logs on Appian Cloud** are read from the Admin Console (System Logs, `/suite/logs`). DEBUG loggers
  for sync, deployments, connected systems, SAML/OIDC or SAIL errors are switched on by Support, make logs
  large and can slow the site: use them on a lower environment first, then return them to ERROR ([KB-1575],
  [KB-1238]).
- ✅ **Health Check data collection:** prefer Automatic Upload (manual uploads are capped at 1 GB,
  automatic at 2 GB) ([KB-2203]). The organization has one Health Check account whose password expires
  every **365 days** — a 401 or "Invalid Community credentials" means reset it in MyAppian › Health and
  update Admin Console › Health Check ([KB-2277], [KB-1556]). Schedule runs outside the Community/Forum
  maintenance windows ([KB-1979]).

## 1. Processes and tasks

| Symptom | Cause | Action | Source |
|---|---|---|---|
| Subprocesses keep running after the parent reaches a Terminate end event | Activity chaining into the Terminate event runs the cancel as the (basic) user who completed the task, who can't cancel the children | Don't chain into Terminate: end the chained flow on a plain End and terminate from a parallel, unchained flow, or use Cancel Process run by an account with rights | [KB-1300] |
| Parent PVs become null after an asynchronous subprocess | A subprocess switched from synchronous to asynchronous keeps hidden output mappings | Switch back to synchronous, delete the outputs, switch to asynchronous again | [KB-2158] |
| An XOR with several incoming flows hangs the second time | A gateway with multiple incoming flows waits for all of them (doc 03 §5) | One gateway per incoming flow, or a merging script task; unblock running instances by starting the next node or with Edit Process | [KB-2144] |
| An XOR condition path doesn't save | The target is the first node ever created in the model | Copy that node, delete it, paste it back and re-point the gateway | [KB-2267] |
| Process pauses with `ERROR:EVAL:@reason=index` from an escalation, timer or exception | A rule called with **keyword** arguments inside an event, where keyword syntax isn't supported | Pass arguments by position in events, process reports and the Web Content Channel (doc 04 §2) | [KB-1794] |
| Timers or escalations fire at the wrong time for long durations | `intervalds()` overflows to a negative value above 2,147,483 seconds (~24.8 days) | Use day-based arithmetic or `a!addDateTime()` for long durations | [KB-1386] |
| A recurring start interval ignores a changed constant | The value is taken when the model is published | Re-save and republish the model | [KB-1835] |
| "Does not exist: Process" in Monitor, or a Web API returns "Error when parsing process details" after starting a process | The instance was already archived or deleted | Keep the Data Management delay longer than any caller that reads process info or PVs afterwards | [KB-2111] |
| Old tasks fail with "Could not find variable ac!…" | Running tasks render the **latest** interface version; a changed rule input breaks them | Create a new interface (or version-conditional logic) instead of changing inputs used by in-flight tasks (doc 03 §12) | [KB-1175] |
| After a CDT change, node custom outputs fail with "Cannot index property"; export fails with "Could not serialize Process Model into DOM tree" | "Update dependents" remaps node inputs only; a node still points to an old CDT version | Fix custom outputs by hand; find the stale reference in the process model documentation | [KB-1137], [KB-1139] |
| A user is blocked from **all** tasks for 15 minutes | More than 10 accesses to invalid tasks (completed, deleted or not permitted) within 15 minutes; not configurable; logged in `task_errors.csv` | Don't expose stale task links (old emails, bookmarks, custom lists that keep completed tasks) | [KB-2360] |
| "User Does Not Have Rights…", or APNX-1-4188-001 "work item cancelled" / "not in any role" when a process runs | The initiator lacks Initiator on a (sub)model, or a node runs as a **deactivated** designer or initiator; a swim lane assignment overrides the node's | Republish with an active service account as designer; override the lane assignment where the node needs its own | [KB-1027], [KB-1626], [KB-1130] |
| A parent process won't start (generic error) | A child process model is not published | Publish every child | [KB-1237] |
| Publishing fails: "Neither variable(s) nor rule(s) found" or "error in an expression in null at null" | An uncaught syntax error (missing comma, duplicate dictionary key), or a swim lane or expression referencing a deleted PV, constant or group | Fix the syntax; find and replace the stale reference | [KB-1627], [KB-1013] |
| A parent still warns about a child it no longer uses | Old parent versions reference it | Delete the old versions | [KB-2202] |
| Many nodes paused by exception after an outage | — | Fix the cause first, confirm the nodes are safe to re-run, then bulk-restart them (Process By Node Status, status 8 + Restart All Nodes; community plug-ins provided as-is) | [KB-1340] |
| "Send alerts to the process initiator" reaches other people | Known issue AN-93556 | Use the expression option with `pp!initiator` | [KB-1788] |
| Escalation emails show HTML tags | Rich text pasted into the message | Paste as plain text | [KB-2282] |
| A process model won't save: "Non-nullable input ACP(s)… isAsynchronous" | The application server is inconsistent after an engine issue | Appian Cloud: support case to restart it | [KB-2190] |
| A process report returns wrong data when casting a CDT | Appian BULK type values | Cast with `cast(-tointeger('type!…'), pv!x)` inside a helper rule | [KB-1617] |

## 2. Data, sync and the Appian Cloud database

| Symptom | Cause | Action | Source |
|---|---|---|---|
| `isServiceAccount` shows false for service accounts in the User record type (24.3+) | A full sync on a site that has deactivated users (AP-63793) | Deactivate/reactivate the account, or remove it from and re-add it to the Service Accounts group, after each full sync; don't base security or filters on that field until fixed | [KB-2392] |
| `totalCount` doesn't match the rows, changes with the batch size, or a grid fails with "totalCount… must not be less than the number of items" | The column Appian treats as the primary key is duplicated or null in the table or view | Map the key to a unique, non-null column; give every table a primary key or unique index | [KB-2120], [KB-1121], [KB-1413] |
| Export Data Store Entity to CSV/Excel returns only 1,000 rows | The CDT and the table/view define different primary keys | Align the keys; export from tables (views have no keys or indexes) | [KB-2148] |
| Export to Excel fails with "insufficient memory" | The batch exceeds the query memory limit, which can't be raised on Cloud | Export fewer and narrower columns | [KB-1521] |
| Export to Excel rejects the "Document to Update" template | The file decompresses to ≥ 100× its size or has an entry > 4 GB | Clean repeated styles and data out of the template | [KB-1708] |
| A record list export fails with a network error below the row limits | The Appian Cloud load balancer cuts requests at **5 minutes** | Filter or batch so each export finishes in under 5 minutes | [KB-2293] |
| "Unexpected error executing query" with `Value '0000-00-00'` in the log | Zero dates in the table (typically loaded by scripts or procedures) | Fix or delete those rows | [KB-1038] |
| `a!queryEntity` fails on a CDT with an `@Transient` field | Transient fields aren't persisted | Use `selection` with persisted fields only | [KB-1404] |
| Mapping verification fails on a CHAR key ("expected nvarchar(255)") | CHAR primary or foreign keys | Use VARCHAR keys | [KB-1346] |
| A three-level nested CDT won't save ("types cannot be used…") | Known issue AN-128273 | Remove the bottom field from the middle CDT, save the top, add the field back | [KB-2131] |
| CDT import: "Qualified name not unique or temporary" | An interrupted import locks the type for 2 hours | Wait 2 hours, or rename the CDT and repoint its users | [KB-1007] |
| `a!queryEntity` or a query rule times out | Queries to external databases time out after **10 s** (`conf.data.query.timeout`; not configurable on Cloud; doesn't apply to Query Database) | Optimize the query; read `perf_monitor_rdbms_slow.csv` | [KB-1681] |
| "Long Running Database Transaction" alert (self-service alerts, ⓥ preview from 26.4), or phpMyAdmin returns 504 | A long-running query | `CALL AppianProcess.getFullProcessList()`, read the Time column, then `CALL AppianProcess.killProcess(<id>)` | [KB-2379], [KB-1530], [KB-1776] |
| `DeadlockLoserDataAccessException` | Database deadlock | `CALL AppianProcess.showEngineInnodbStatus()` (Full texts) → *LATEST DETECTED DEADLOCK*; also `databaseLocks()` and `metadataLocks()`. External SQL Server: the DBA enables `ALLOW_SNAPSHOT_ISOLATION` and `READ_COMMITTED_SNAPSHOT` | [KB-2331], [KB-1263] |
| Wrong results or errors from one table | Corrupted index | `CHECK TABLE` → `SHOW CREATE TABLE` → drop and re-add the index → `CHECK TABLE` | [KB-2381] |
| `CONVERT_TZ` returns NULL | The Cloud database has no time zone tables | Store UTC and convert in SAIL | [KB-2127] |
| A trigger fails: "INSERT command denied to user 'appian'@'127.0.0.1'" | Explicit `DEFINER` clause | Recreate it without DEFINER (doc 01 §12.3) | [KB-1056] |
| phpMyAdmin returns 502 | Two tables whose names differ only by case | Rename one | [KB-1348] |
| Writes fail with emojis or other Unicode; a view fails with "Illegal mix of collations" | Table not in `utf8mb4`; tables behind the view with different collations | `utf8mb4` everywhere (index keys then fit 191 characters); one collation for every table behind a view | [KB-2038], [KB-1822] |
| `GROUP_CONCAT` output is cut short | 1,024-byte limit, not changeable on Cloud | Split the query | [KB-1115] |
| Deleting rows doesn't free disk | Space is reclaimed only by Support | See §10 | [KB-1354] |

## 3. Interfaces, rules and expressions

| Symptom | Cause | Action | Source |
|---|---|---|---|
| Values saved in the wrong order inside `a!forEach` | Saving into `local!list[fv!index]` | Save into `fv!item` | [KB-1398] |
| Grid rows repeat across pages when sorting | Sorting only on a non-unique column | Add the primary key as a secondary sort (records-powered grids add a deterministic sort; `a!queryEntity` and dictionaries don't) | [KB-1519] |
| "Select all" in an editable grid produces a wrong selection | — | `selectionSaveInto: a!save(local!sel, a!flatten(save!value))` | [KB-2025] |
| The interface won't open in the designer: "Cannot interpret context… Bindings" | Uncompressed interface context above the **200 MB** hard limit | Temporarily blank the heavy rule (or fix it in another environment and import), then reduce what the context holds (doc 05 §3) | [KB-1828] |
| "Could not cast… CastInvalid" on interaction | The `saveInto` target type doesn't match the value | Save single fields with dot notation, or cast | [KB-1570] |
| A task with uploaded files can't be saved as a draft | By design (except offline tasks in Appian Mobile) | Don't depend on Save Draft in forms with File Upload | [KB-1480] |
| Uploaded documents can't be downloaded from Designer ("Not Visible") | `target` set to the same document variable as `value`/`saveInto` | Target a folder constant or a document management record type; recover with *Download as zip* | [KB-1826] |
| Dates one day off (`today()`, `datetext()`, a Date shown as date-time) | `today()` and Date → Date and Time conversions use **GMT** | `todate(local(now()))` for the user's day; wrap conversions in `gmt()`; check the primary time zone settings | [KB-1363], [KB-1344] |
| `round()` of a computed value that should end in 5 rounds down (`round(123/240*100, 1)`); `fixed(8192.80*100, 0)` returns 819279 | Decimals are IEEE-754 doubles | Round in two steps (to 6 decimals, then to the target), `roundup`/`rounddown`, `fixed()` for display | [KB-1426] |
| `a!isNullOrEmpty({null})` returns false | The function doesn't iterate lists | Check with `length()` or `a!forEach()` | [KB-2222] |
| "The given datatype id 97 is not a primitive type" | Values taken from lists of dictionaries come back wrapped | Cast with `tointeger()`/`tostring()` before passing them on | [KB-1658] |
| A rule input doesn't take its value | Input named like a SAIL keyword (`submit`, `style`); an input named `action` only fails in the designer's test inputs | Rename the input, or save with `a!save(ri!x, save!value)` | [KB-1098], [KB-2029] |
| Class Cast Exception in reports | A constant named like a function (e.g. `task_status`) | Rename it | [KB-1170] |
| System function calls revert to `_18r3`/`_17r1` versions on save | A wrong `type!` namespace in the expression | Fix the namespace and remove the suffixes | [KB-1917] |
| Errors after a hotfix in expressions that index `env!clientMode`, `uploadedDocumentName`… | Undocumented internal structures change between hotfixes | Never dot-index internal system types | [KB-1441], [KB-1405] |
| Opening a user constant fails: "All users and groups must be valid…" | The user was renamed | Prefer group constants | [KB-1854] |
| Designer expression search fails with `CdtQueryRequest` | An object larger than **1,000,000 characters** | Split the object | [KB-2213] |
| Slow `rule!`/`cons!` suggestions in the designer | Very many object versions | Prune old versions | [KB-2168] |
| Content engine memory keeps growing | A constant with 100+ versions created by Update Constant with *Create New Version* on | Keep *Create New Version* off on Update Constant; use Increment Constant for counters (it never versions); prune versions off-hours | [KB-1226] |
| Byte-limited truncation breaks with emojis | `left()` counts an emoji as 2 characters, `leftb()` as 2 bytes | `lenb()` plus a `regexfirstmatch()` loop | [KB-2372] |
| A variable with `refreshInterval` doesn't update | Browsers throttle background tabs (by design) | Monitoring screens in their own active window, plus a manual refresh button | [KB-1992] |

## 4. Documents, email and generation

| Symptom | Cause | Action | Source |
|---|---|---|---|
| Word Doc from Template leaves `###key###` unreplaced | Word splits the key across XML runs (proofing marks, bookmarks) | Retype the key in a clean document with proofing off; check it's contiguous in the XML | [KB-1819] |
| Text Doc from Template files end in `_` | The template isn't a `.txt` file | Use a `.txt` template | [KB-2076] |
| SFTP sends an empty file | The document is sent right after it's generated | A short timer (≤ 1 min) between generation and transfer | [KB-1113] |
| Blank rows in a knowledge center | Documents stored directly in the knowledge center | Knowledge centers hold folders; move documents with Move Document | [KB-1432] |
| Basic users get "User Does Not Have Rights" opening a record | `document()` on a folder they can't view | Viewer on the folder, or a document management record type | [KB-1155] |
| A folder is smaller in the target, or sizes differ between back end and designer | Deployment carries only the latest version; a moved document stays in its original knowledge center on disk | Expected; manage object versions to reclaim space | [KB-2235], [KB-2287] |
| Send E-Mail: "No valid recipients resolved" | The To field is Text | Wrap it in `toemailrecipient()` | [KB-1046] |
| The sender keeps an old address after deployment | Sender address hard-coded in the model | Take it from a constant | [KB-1197] |
| Email-started process fails: "Invalid bean property name 'Attachments'"; Receive Message errors on a null importance | No attachments folder configured; `msg!` properties can be null | Set the Email Attachments Folder; read properties with `property(…, default)` | [KB-1848], [KB-1538] |
| Users don't receive Appian email | "Allow Appian to send email" is off, or the domain/sender changed without an SPF include | Admin Console › Email; add the site's SPF include; Sender and Return-Path stay `admin@<site>.appiancloud.com` until Support changes the notification sender | [KB-1864], [KB-2181], [KB-2010], [KB-1887] |
| Office 365 rejects with `SendAsDenied` | O365 doesn't allow Appian to send as that address | Allow the sender in O365 or change it | [KB-2123] |
| Exchange Online: "432 4.3.2 sender thread limit exceeded" | 3 concurrent SMTP connections per mailbox | Use the Appian Cloud mail server | [KB-1981] |
| Inbound email never reaches the process | Aliases aren't supported on Cloud; the sending server expands CNAMEs | Forward from your own mailbox; turn CNAME expansion off on the sender | [KB-1896], [KB-1394] |

A custom SMTP server isn't available on Basic Support and needs a 2–4 hour restart window ([KB-2100]).

## 5. Deployment, packages and objects

| Symptom | Cause | Action | Source |
|---|---|---|---|
| The deployment dialog shows 502/504 | Imports run in the background since 21.4 (exports since 23.3); the dialog timed out, not the import | Confirm in the News feed and Admin Console › Import History (kept 30 days — archive the evidence); if inspection times out, split the package by layer | [KB-1747], [KB-1738], [KB-1282] |
| CI/CD deployment returns 403 or times out, with nothing in `login-audit.csv` | The runner's public IP isn't in Trusted IPs | Add the runner IP (the list holds up to 500 entries) | [KB-1568] |
| Adding a connected environment: "URL did not return valid public key" | The sites don't trust each other's certificates, or the target's trusted IPs miss the region's outbound IPs | Both sites need certificates the other trusts (public CA, full chain — see KB-1187); support case to add the region's outbound IPs to the target's Trusted IPs | [KB-1973], [KB-1187] |
| AI skill export returns 504, or import with inspection fails | Each AI skill took ~4 min to export when the KB was written (2024); synchronous requests stop at 5 min | The KB's workaround: a package with only the AI skill, exported manually and imported without inspection. Skipping inspection loses its checks — try the single-skill package with inspection first | [KB-2298] |
| ⓥ Deployment fails: "Missing Precedent… relationshipPath is null" (26.6+) | Semantic search `similarityScore` referenced directly in a script task custom output (AP-66295) | Move the search into an expression rule and call the rule | [KB-2395] |
| Importing an object with `a!recordActionField`: "recordAction… cannot be found" | The record type isn't in the package | Include the record type | [KB-2104] |
| Export fails: "invalid precedent… cannot be found" | A precedent was deleted | Restore it from another environment (same UUID) or remove the references | [KB-1217] |
| The latest process model changes are missing from the package | Only the **published** version is exported | Save & Publish before packaging | [KB-1254] |
| A group or object was deleted | It can only come back by importing the **same UUID** from another environment; recreating it by name gets a new UUID | Re-import from another environment; never delete production groups | [KB-1154], [KB-1200] |
| "Invalid function" and missing dependents after a rename | Dependents that reference the object by name weren't updated | Rename back, re-save the dependents, rename again | [KB-2024] |
| Web API import: "Duplicate entry '<endpoint>-<METHOD>-0'" | Endpoint + method must be unique system-wide | Rename the endpoint | [KB-2191] |
| Connected system: "query did not return a unique result" after import | Known issue AN-147907 | Delete it in the target and re-import | [KB-2066] |
| "???" instead of object names | The application came from an environment with a different primary locale | Add names in the target's primary locale | [KB-1193] |
| Creating a record type fails (`registerLoadEditWindow`) | A CDT named like a system type (`RecordType`) | Never name objects after system types | [KB-1301] |

## 6. Integrations, certificates and network

| Symptom | Cause | Action | Source |
|---|---|---|---|
| A Web API doesn't find a header | Appian Cloud uses HTTP/2, which lowercases header names | Read headers in lowercase | [KB-2342] |
| Custom auth reading `Authorization` or `appian-api-key` gets null | Sensitive headers are stripped from `http!request.headers` | Use Web API authentication, not custom header parsing | [KB-2128] |
| An integration or Web API that calls the same site gets 403 | Trusted IPs block the site calling itself | Avoid the self-call (e.g. Call Integration in a process); allow-listing the region's outbound IP also admits other customers' sites | [KB-2217] |
| Accented characters come back as `?`, or `MalformedInputException` | No charset in the response / non-UTF-8 request body | `Content-Type: application/json; charset=utf-8` in `a!httpResponse`; require UTF-8 from callers | [KB-1851], [KB-1857] |
| 415 Unsupported Media Type | Appian appends `charset=UTF-8` to the content type | Add an explicit `Content-Type` header | [KB-1771] |
| An OAuth 2.0 client credentials connected system logs "Could not authenticate…" but works | Appian sends credentials in the header first, then retries in the body | Make the token endpoint accept header credentials | [KB-2367] |
| `PKIX path building failed` | Trusted Server Certificates only apply to the services the docs list; the endpoint doesn't send the intermediate chain | Public CA certificate with the full chain on the endpoint | [KB-1187] |
| "Host name does not match the certificate subject" | Calling by IP without that IP in the certificate's SAN | Call by a name in the certificate, or reissue it with an IPAddress SAN entry | [KB-2020], [KB-1644] |
| Integration objects time out but `a!httpQuery` works | The HTTP proxy configured in the Admin Console | Review the proxy settings | [KB-2080] |
| SQL Server connection fails with PKIX after an upgrade | The JDBC driver now validates the server certificate | Per the docs: `encrypt=true;trustServerCertificate=false` and the database CA in Trusted Server Certificates (not KB-2311's `trustServerCertificate=true`) | [KB-2311] |
| Snowflake: `NoClassDefFoundError …arrow…` | Java 17 vs Arrow result format | `JDBC_QUERY_RESULT_FORMAT=JSON` in the URL | [KB-2338] |
| Database over VPN: "Communications link failure" | MTU mismatch or short tunnel drops | Support checks MTU; on Cisco ASA, `sysopt connection preserve-vpn-flows` | [KB-1206], [KB-1621] |
| Callers get "The underlying connection was closed" | Client below TLS 1.2 (required on Cloud) | Upgrade the client; test at `tlstest.appiancloud.com` | [KB-2058], [KB-1483] |
| SAP calls reuse old `connectionProperties` | Properties stick to the Third-Party Credentials key | Use a new key | [KB-1918] |
| Re-importing a WSDL fails: "Qualified name not unique or temporary" | Enumerations in the XSD | Strip enumerations before import | [KB-1198] |

## 7. Authentication, users and groups

| Symptom | Cause | Action | Source |
|---|---|---|---|
| SAML: "issued in the future" or "Assertion failed security policy check" | Clock skew between IdP and Appian | Fix time sync on the IdP | [KB-1901], [KB-1153] |
| SAML 401: invalid signature | IdP signing certificate rotated or metadata wrong | Rotate in non-production first: replace IdP metadata → *Test this configuration* → *Verify my access* → Save; for a new SP certificate, also send the new SP metadata to the IdP | [KB-1938], [KB-1461], [KB-1459] |
| SAML broken after a domain change | SP metadata (ACS URLs) contains the hostname | Keep a system administrator outside the SAML group beforehand; regenerate SP metadata, upload it to the IdP, refresh the IdP metadata, fix start pages | [KB-2343] |
| Entra ID AADSTS90023, or ADFS shows its login form instead of Windows auth | Appian sends `Comparison="minimum"` | Set the SAML *Authentication Method* to None | [KB-1686], [KB-1903] |
| OIDC with Azure AD B2C: "tokenValue cannot be empty" | Missing scope | Add the client ID to the scopes (`openid <clientId>`) | [KB-2337] |
| Deep links land on the start page after SSO | RelayState isn't supported; the IdP must return `InResponseTo` | Configure the IdP to return InResponseTo | [KB-2043] |
| Only some users can't log in | Usernames are case-sensitive | Untick "Retain Casing" if the IdP sends mixed case; diagnose in `login-audit.csv` | [KB-1450] |
| A service account can't reset its password ("link has expired") | Members of the Service Accounts group can't log in or reset | Expected | [KB-2198] |
| A new password policy isn't applied | Existing passwords aren't invalidated | Reset in batches of 100, or set max age to 1 day and restore it | [KB-1463] |
| `InvalidSupervisorException` deactivating a user | The user supervises others | Reassign the supervisor first | [KB-1364] |
| The Cloud Database (phpMyAdmin) link disappeared | The Database Administrators group was deleted | Re-import it (same UUID) from an environment on the same version | [KB-1882] |
| Log pipelines break parsing `login-audit.csv` after 25.4 | A header row and an MFA column were added | Parse by column name, not position | [KB-2386] |

## 8. Browser, mobile and embedding

| Symptom | Cause | Action | Source |
|---|---|---|---|
| Web Content component blank or pink | Source sends `X-Frame-Options`, isn't public, or isn't HTTPS (Safari isn't supported) | Only the source's owner can fix headers; use HTTPS | [KB-1583] |
| Images or resources missing in the iOS app | App Transport Security blocks HTTP, TLS < 1.2 or no forward secrecy | HTTPS with TLS 1.2+ | [KB-1272] |
| Embedded interfaces don't authenticate | Third-party cookies; with SAML the IdP cookies need `SameSite=None; Secure` | Same parent domain avoids it | [KB-2065] |
| Embedded page stays blank | Self-closing `<script …/>` tags | Close tags explicitly | [KB-1305] |
| Tasks won't open (popup error) | A proxy or firewall blocks PUT | Allow GET, POST, PUT, DELETE, OPTIONS | [KB-1209] |
| Blank page or 403 through Zscaler | TLS inspection | Add the site to Zscaler's SSL bypass list | [KB-1792] |
| PDFs don't render inline | Chrome "Download PDFs" setting | Turn it off | [KB-1688] |
| First login very slow on slow connections | Large JavaScript bundles for Tempo | Set user start pages to a site | [KB-1566] |
| Repeated "You are already editing" in the designers (Chrome, 25.4+) | Chrome's deprecation of the unload event | Chrome flag or another browser | [KB-1923] |
| Sites return 403 after an upgrade | Known issue AN-140947 | Open the site's security and save it unchanged | [KB-2002] |
| iOS users can't see or open sites | An error in a site page **Title** expression (silent on the web) | Fix the title; the log names the page's web address identifier | [KB-2146] |
| Offline form: "system is in a degraded (stateless) status" | `a!startProcessLink` in an offline-enabled interface | Remove offline or redesign the form | [KB-1867] |
| Mobile SSO popup blank; Android "Untrusted site" | The IdP login isn't form/cookie based; the IdP certificate chain is incomplete | Forms-based IdP login; CA certificate with the full chain | [KB-1553], [KB-1628] |
| The mobile app renders in browser mode | A custom auth front door doesn't redirect back correctly | Redirect 301/302 to a URL containing `/suite/tempo` or `/suite/sites` | [KB-1594] |
| Barcodes don't scan | `acceptedTypes` silently ignores other types | Set it only when there's a real requirement | [KB-1968] |

Mobile facts to design around: push delivery isn't guaranteed (never the only channel for urgent work);
IdP-initiated SAML isn't supported on mobile; Android must trust the root **and** intermediate
certificates ([KB-2016]).

## 9. AI

| Symptom | Cause | Action | Source |
|---|---|---|---|
| An agent fails intermittently: `EVENT_NOT_FOUND`, `INVALID_TOOL_RESPONSE`, "Input is too long" | Model non-determinism, or a request larger than the model accepts | Sharper prompt and descriptive tool names; a retry path around Execute AI Agent in the calling process; limit document inputs and `extraInstructions` | [KB-2396] |
| Which DocCenter version is installed? | — | DocCenter app → Constants → `AIA_VERSION` (`<environment version> - <DocCenter version>`); check before cross-environment deployments and plug-in upgrades | [KB-2378] |
| Legacy IDP / Google document classification stopped working | Google shut down AutoML Natural Language (January 2024) | Move to AI skills or AI DocCenter | [KB-2262] |

See also KB-2298 and KB-2395 in §5.

## 10. Appian Cloud operations

- **Disk.** Support opens a case above 80 %. Knowledge center 0 holds deployment packages (deleted after
  30 days, configurable); temporary documents are kept 30 days; binary logs 4 days; archived processes are
  compressed after 7 days; large PVs and looping processes grow the engine transaction logs. Only the
  customer can delete knowledge center documents; deleted database rows free disk only when Support
  reclaims it. Extra storage comes in 25 GB steps, applies in ~30 minutes and can't be removed or moved
  ([KB-1354], [KB-2364]).
- **What Appian monitors for you:** disk (80/90/95 %), memory (80/90 %), more than 60 % of requests over
  3 s, connection pool, replication, VPN, certificates, data and search servers. Business SLOs,
  integrations and process health remain yours (doc 11 §5) ([KB-1859]).
- **Application server heap:** 3 GB by default on Cloud. High heap alone is normal; frequent garbage
  collection is the problem, and an OutOfMemoryError restarts the server (a full outage on a single node).
  Usual causes: large query results, document generation in plug-ins, very large PVs — fix the design
  (filter, batch, cap uploads, stagger bulk work) rather than asking for heap ([KB-2288]).
- **"Could not obtain 3 thread(s)… in work poller":** application server threads held by failing
  integrations, slow queries or load ([KB-2094]).
- **Health Check sizing sheet empty:** the engines are too large to collect in 2 minutes — archive or
  delete processes ([KB-1989]).
- **Upgrades and maintenance:** set default maintenance windows in MyAppian (2 h by default); reschedule
  through Support with 3 working days' notice (Cloud installation upgrades can be self-rescheduled up to
  10 minutes before); put a distribution list on maintenance notifications and Appian-opened cases
  ([KB-2248], [KB-1403], [KB-1934], [KB-2228]).
- **Restore from backup** rolls back the **whole site** (data, business database, version,
  configuration), costs extra and needs a maintenance window: to recover a deleted object, re-import it
  first ([KB-2013], [KB-1200]).
- **Disaster recovery tests:** one per year for qualifying HA or Enhanced Business Continuity sites,
  requested at least 2 weeks ahead ([KB-2292]).
- **Site clones made by Support** hold a full snapshot, have outbound traffic and email disabled and are
  deleted at case closure — useful for data-protection approvals ([KB-1831]).
- **Portal error APNX-1-4561-032 after a republish:** users had a stale page open; unpublish, then
  republish ([KB-2369]).

## 11. KB advice that differs from the current documentation (the docs win)

| KB / article | It says | The 26.x docs say |
|---|---|---|
| [KB-2311] | `trustServerCertificate=true` for SQL Server | `encrypt=true;trustServerCertificate=false` and upload the database CA |
| [KB-1683] | LDAPS on Cloud needs a public-CA certificate | Self-signed LDAPS certificates uploaded as Trusted Server Certificates are used |
| [KB-1330] | Initiator-only users need Viewer for `onSuccess` to fire | Initiator starts the process; PV and model values in `fv!processInfo` need Viewer (doc 03 §7) |
| [KB-1240] | A plain Date shifts with the user's time zone | Date values aren't time-zone adjusted; Date and Time values are |
| [KB-1465] | Escape `& < >` with `toHtml()` in Word templates | Since 26.3 Doc from Template escapes them; don't double-escape |
| [KB-1243] | Use `""` instead of JSON null | JSON null maps to null |
| [KB-1186] | Unarchive on Cloud through Support or the Process Management Services plug-in | Monitor › Process Activity (sites created on 21.1+) |
| [KB-1411] | Query memory limit 1 MB | `conf.data.query.memory.limit` default 5 MB |
| [KB-1673] | Connection pool 200 | 100 per data source connected system (doc 01 §12.3) |
| [KB-1622] | Inbound email 25 MB | 70 MB in total |
| [KB-2016] | The app may be two versions behind the server | Offline needs an app on the same version or newer; each app release is supported for about 6 months |
| [Deployment Automation] | Deploy with the Automated Import Manager | Don't; use the deployment REST APIs |
| [Integrating Using JMS] | Queues only through an API gateway calling a Web API | Kafka is supported natively from 26.6 (Apache Kafka connected system, Event Consumer, Publish Event); the gateway pattern remains for JMS |
| [Manage Your Cloud Upgrade] | Quarterly upgrades, stay within 2 releases | Since 26.1, monthly releases are optional and supported only until the next one; quarterly releases (.3/.6/.9/.12) are supported six months; hotfixes at least every 90 days (SKILL.md *Version*) |
| [Writing to Synced Record Types at High Throughput] | ~30,000 writes/min | Design to the autoscale threshold, 15,000 transactions/min; 30,000 was the general data fabric write capacity (doc 05 §5) |
| [Design Review Checklist] | ≤ 30 nodes, ≤ 50 PVs per model | Design Guidance thresholds (50 nodes, 100 PVs) are the reference and don't block (doc 10, gate 6); the checklist's numbers are a stricter team target |

---

## Sources

All articles: Appian Community Knowledge Base, https://community.appian.com/knowledge-base (Solution
Engineering KB and Appian Max). Retrieved September 2026.

[Analyzing Performance Issues]: https://community.appian.com/architecture-29/analyzing-performance-issues-1344
[Integrating Using JMS]: https://community.appian.com/architecture-29/integrating-using-jms-1340
[Deployment Automation]: https://community.appian.com/platform-30/deployment-automation-1329
[Manage Your Cloud Upgrade]: https://community.appian.com/platform-30/manage-your-appian-cloud-upgrade-1240
[Writing to Synced Record Types at High Throughput]: https://community.appian.com/architecture-29/writing-to-synced-record-types-at-high-throughput-1397
[Design Review Checklist]: https://community.appian.com/architecture-29/design-review-checklist-1223
[KB-1007]: https://community.appian.com/application-design-33/kb-1007-qualified-name-not-unique-or-temporary-error-thrown-when-trying-to-import-cdts-into-appian-324
[KB-1013]: https://community.appian.com/application-design-33/kb-1013-there-was-an-error-in-an-expression-in-null-at-null-null-error-thrown-attempting-to-publish-a-process-model-330
[KB-1027]: https://community.appian.com/application-design-33/kb-1027-user-does-not-have-rights-to-perform-this-operation-error-thrown-when-running-a-process-342
[KB-1038]: https://community.appian.com/application-design-33/kb-1038-error-evaluating-function-queryruleexec-unexpected-error-executing-query-thrown-when-evaluating-query-rule-351
[KB-1046]: https://community.appian.com/application-design-33/kb-1046-no-valid-recipients-resolved-error-thrown-when-using-send-email-359
[KB-1056]: https://community.appian.com/cloud-35/kb-1056-insert-command-denied-to-user-appian-at-127-0-0-1-for-table-xxxx-error-returned-when-executing-a-sql-trigger-368
[KB-1098]: https://community.appian.com/application-design-33/kb-1098-input-variables-named-after-sail-keywords-don-t-take-the-value-that-is-assigned-to-them-403
[KB-1113]: https://community.appian.com/application-design-33/kb-1113-sftp-smart-service-transfers-a-blank-file-to-its-destination-416
[KB-1115]: https://community.appian.com/infrastructure-37/kb-1115-group-concat-function-in-mysql-truncates-value-417
[KB-1121]: https://community.appian.com/infrastructure-37/kb-1121-changing-the-batch-size-of-a-queryentity-also-changes-the-total-count-423
[KB-1130]: https://community.appian.com/administration-32/kb-1130-the-user-xxxxx-does-not-have-sufficient-privileges-to-perform-the-requested-action-because-they-are-not-in-any-role-error-thrown-in-different-scenarios-432
[KB-1137]: https://community.appian.com/application-design-33/kb-1137-cdt-updates-do-not-modify-custom-outputs-438
[KB-1139]: https://community.appian.com/application-design-33/kb-1139-could-not-serialize-process-model-into-dom-tree-error-thrown-when-trying-to-export-a-process-model-440
[KB-1153]: https://community.appian.com/administration-32/kb-1153-saml-authentication-faq-449
[KB-1154]: https://community.appian.com/application-design-33/kb-1154-group-was-deleted-in-an-environment-450
[KB-1155]: https://community.appian.com/application-design-33/kb-1155-user-does-not-have-rights-to-perform-this-operation-error-thrown-for-basic-users-when-trying-to-open-records-451
[KB-1170]: https://community.appian.com/application-design-33/kb-1170-class-cast-exception-465
[KB-1175]: https://community.appian.com/application-design-33/kb-1175-processes-fail-with-could-not-find-variable-ac-variable-error-470
[KB-1186]: https://community.appian.com/how-to-36/kb-1186-how-to-unarchive-processes-478
[KB-1187]: https://community.appian.com/administration-32/kb-1187-pkix-path-building-failed-error-when-attempting-to-make-a-call-to-an-external-server-error-thrown-when-making-web-service-calls-over-https-or-ldaps-479
[KB-1193]: https://community.appian.com/application-design-33/kb-1193-question-marks-appear-in-place-of-a-process-model-name-483
[KB-1197]: https://community.appian.com/application-design-33/kb-1197-custom-email-senders-send-from-old-email-addresses-and-do-not-use-new-values-487
[KB-1198]: https://community.appian.com/integration-39/kb-1198-qualified-name-not-unique-or-temporary-error-returned-when-calling-a-wsdl-that-uses-data-types-that-contain-enumerations-488
[KB-1200]: https://community.appian.com/administration-32/kb-1200-how-to-recover-a-deleted-process-model-490
[KB-1206]: https://community.appian.com/administration-32/kb-1206-communications-link-failure-during-rollback-transaction-resolution-unknown-error-thrown-in-application-server-log-495
[KB-1209]: https://community.appian.com/infrastructure-37/kb-1209-browser-popup-error-displays-when-trying-to-open-a-task-498
[KB-1217]: https://community.appian.com/application-design-33/kb-1217-the-content-content-was-not-exported-because-it-contains-an-invalid-precedent-content-content-cannot-be-found-error-thrown-when-exporting-an-application-505
[KB-1934]: https://community.appian.com/how-to-36/kb-1934-how-to-add-new-recipients-for-appian-cloud-maintenance-notifications-1002
[KB-1226]: https://community.appian.com/administration-32/kb-1226-content-collaboration-engine-consumes-high-memory-514
[KB-1237]: https://community.appian.com/application-design-33/kb-1237-generic-error-thrown-when-attempting-to-start-a-process-with-sub-processes-525
[KB-1238]: https://community.appian.com/cloud-35/kb-1238-how-to-access-system-logs-on-an-appian-cloud-site-526
[KB-1240]: https://community.appian.com/application-design-33/kb-1240-date-time-displays-an-incorrect-value-for-one-or-more-users-528
[KB-1243]: https://community.appian.com/application-design-33/kb-1243-the-jsontext-parameter-of-a-fromjson-was-not-valid-json-error-thrown-when-executing-a-fromjson-querying-a-json-object-with-a-null-value-531
[KB-1254]: https://community.appian.com/application-design-33/kb-1254-latest-changes-in-a-process-model-are-not-included-in-an-export-540
[KB-1263]: https://community.appian.com/infrastructure-37/kb-1263-deadlock-errors-with-sql-server-548
[KB-1272]: https://community.appian.com/mobile-40/kb-1272-apple-enforcing-app-transport-security-ats-starting-1-january-2017-557
[KB-1282]: https://community.appian.com/administration-32/kb-1282-incomplete-import-history-in-admin-console-565
[KB-1300]: https://community.appian.com/application-design-33/kb-1300-terminate-event-not-cancelling-sub-process-597
[KB-1301]: https://community.appian.com/application-design-33/kb-1301-expression-evaluation-error-at-function-a-appdesigner-registerloadeditwindow-line-48-no-message-error-thrown-when-creating-a-record-type-object-578
[KB-1305]: https://community.appian.com/integration-39/kb-1305-embedded-interface-with-self-closing-tags-does-not-render-584
[KB-1330]: https://community.appian.com/application-design-33/kb-1330-a-startprocess-fails-to-trigger-onsuccess-607
[KB-1340]: https://community.appian.com/how-to-36/kb-1340-how-to-automate-the-restart-of-stuck-nodes-within-a-process-model-581
[KB-1344]: https://community.appian.com/application-design-33/kb-1344-datetext-returns-one-day-before-expected-date-613
[KB-1346]: https://community.appian.com/application-design-33/kb-1346-char-datatype-does-not-map-as-a-foreign-key-616
[KB-1348]: https://community.appian.com/cloud-35/kb-1348-502-error-on-phpmyadmin-after-creating-two-tables-with-the-same-name-but-different-case-619
[KB-1354]: https://community.appian.com/how-to-36/kb-1354-how-to-manage-high-disk-usage-in-appian-cloud-environments-603
[KB-1363]: https://community.appian.com/application-design-33/kb-1363-today-returns-one-day-prior-when-locale-is-set-to-particular-time-zones-630
[KB-1364]: https://community.appian.com/administration-32/kb-1364-invalidsupervisorexception-thrown-when-editing-a-user-632
[KB-1386]: https://community.appian.com/application-design-33/kb-1386-negative-value-returned-for-intervalds-function-when-passing-inputs-amounting-to-greater-than-591-hours-31-minutes-and-23-seconds-651
[KB-1394]: https://community.appian.com/cloud-35/kb-1394-emails-are-not-sent-to-appian-cloud-because-of-cname-expansion-660
[KB-1398]: https://community.appian.com/application-design-33/kb-1398-a-foreach-does-not-save-inputs-in-the-order-they-are-entered-662
[KB-1403]: https://community.appian.com/cloud-35/kb-1403-rescheduling-cloud-installation-upgrades-667
[KB-1404]: https://community.appian.com/application-design-33/kb-1404-queryentity-fails-when-an-xsd-has-a-field-marked-as-attransient-663
[KB-1405]: https://community.appian.com/application-design-33/kb-1405-cannot-index-property-uploadeddocumentname-of-type-text-into-type-fieldlayout-666
[KB-1411]: https://community.appian.com/infrastructure-37/kb-1411-memory-threshold-reached-during-output-conversion-670
[KB-1413]: https://community.appian.com/infrastructure-37/kb-1413-mysql-best-practices-primary-key-or-unique-index-on-every-table-675
[KB-1414]: https://community.appian.com/web-browser-43/kb-1414-dynatrace-interfering-with-appian-components-674
[KB-1426]: https://community.appian.com/application-design-33/kb-1426-unexpected-results-on-decimal-calculations-and-rounding-678
[KB-1432]: https://community.appian.com/application-design-33/kb-1432-blank-items-in-knowledge-center-682
[KB-1441]: https://community.appian.com/application-design-33/kb-1441-could-not-find-variable-env-clientmode-using-a-recordlink-656
[KB-1450]: https://community.appian.com/how-to-36/kb-1450-how-to-troubleshoot-saml-login-issues-impacting-only-some-users-691
[KB-1459]: https://community.appian.com/how-to-36/kb-1459-how-to-update-the-service-provider-signing-certificate-in-the-administration-console-702
[KB-1461]: https://community.appian.com/how-to-36/kb-1461-how-to-update-saml-configurations-for-use-with-a-new-idp-signing-certificate-703
[KB-1463]: https://community.appian.com/how-to-36/kb-1463-how-to-reset-all-passwords-after-updating-appian-s-password-policy-705
[KB-1465]: https://community.appian.com/application-design-33/kb-1465-parsing-error-thrown-when-attempting-to-open-a-word-document-from-word-doc-from-template-smart-service-701
[KB-1480]: https://community.appian.com/application-design-33/kb-1480-unable-to-save-changes-on-a-sail-form-if-an-file-upload-component-is-present-with-uploaded-files-719
[KB-1483]: https://community.appian.com/security-42/kb-1483-connection-closed-errors-when-connecting-to-appian-cloud-from-external-resources-722
[KB-1519]: https://community.appian.com/application-design-33/kb-1519-grid-data-duplicated-across-multiple-pages-in-a-grid-when-sorting-on-a-non-unique-column-748
[KB-1521]: https://community.appian.com/application-design-33/kb-1521-export-to-excel-smart-service-fails-with-insufficient-memory-error-739
[KB-1530]: https://community.appian.com/infrastructure-37/kb-1530-how-to-kill-queries-initiated-from-phpmyadmin-729
[KB-1538]: https://community.appian.com/application-design-33/kb-1538-receive-message-node-throws-error-when-importance-flag-is-null-758
[KB-1553]: https://community.appian.com/authentication-34/kb-1553-appian-mobile-app-sso-sign-in-popup-is-blank-775
[KB-1556]: https://community.appian.com/administration-32/kb-1556-appian-health-check-fails-with-a-401-unauthorized-error-774
[KB-1566]: https://community.appian.com/web-browser-43/kb-1566-long-page-loading-time-for-slow-connections-during-first-log-in-or-after-browser-cache-has-been-cleared-780
[KB-1567]: https://community.appian.com/web-browser-43/kb-1567-401-unauthorized-error-when-attempting-to-log-in-via-appian-authentication-with-correct-credentials-784
[KB-1568]: https://community.appian.com/cloud-35/kb-1568-errors-when-deploying-application-to-appian-cloud-site-from-the-command-line-using-deployment-automation-manager-785
[KB-1570]: https://community.appian.com/application-design-33/kb-1570-could-not-cast-from-variable-type-1-to-variable-type-2-error-thrown-when-interacting-with-a-sail-interface-783
[KB-1575]: https://community.appian.com/how-to-36/kb-1575-how-to-enable-loggers-for-commonly-seen-appian-issues-782
[KB-1583]: https://community.appian.com/web-browser-43/kb-1583-web-content-component-not-rendering-content-795
[KB-1594]: https://community.appian.com/mobile-40/kb-1594-appian-mobile-app-renders-in-browser-mode-instead-of-native-app-mode-582
[KB-1617]: https://community.appian.com/application-design-33/kb-1617-casting-of-cdt-in-process-reports-returns-inconsistent-unexpected-data-due-to-appian-bulk-type-values-808
[KB-1621]: https://community.appian.com/how-to-36/kb-1621-how-to-enable-preservation-of-vpn-flows-on-a-cisco-asa-822
[KB-1622]: https://community.appian.com/infrastructure-37/kb-1622-sending-an-email-with-an-attachment-to-a-process-in-appian-cloud-fails-812
[KB-1626]: https://community.appian.com/administration-32/kb-1626-error-work-item-cancelled-data-inputs-thrown-from-process-model-nodes-816
[KB-1627]: https://community.appian.com/application-design-33/kb-1627-publishing-a-process-model-fails-with-neither-variable-s-nor-rule-s-found-error-821
[KB-1628]: https://community.appian.com/security-42/kb-1628-untrusted-site-unable-to-login-error-when-loading-a-saml-login-page-on-android-823
[KB-1644]: https://community.appian.com/integration-39/kb-1644-ldap-sync-service-from-the-ldap-tools-plugin-fails-with-a-javax-net-ssl-sslhandshakeexception-after-updating-to-java-1-8-181-831
[KB-1658]: https://community.appian.com/application-design-33/kb-1658-the-given-datatype-id-97-is-not-a-primitive-type-error-received-when-using-the-index-function-on-a-list-of-dictionaries-841
[KB-1673]: https://community.appian.com/infrastructure-37/kb-1673-general-faqs-related-to-appian-and-rdbms-849
[KB-1681]: https://community.appian.com/infrastructure-37/kb-1681-unable-to-retrieve-data-due-to-query-timeout-859
[KB-1683]: https://community.appian.com/authentication-34/kb-1683-ldap-authentication-faq-852
[KB-1686]: https://community.appian.com/integration-39/kb-1686-saml-authentication-request-s-requestedauthenticationcontext-s-comparison-value-must-be-exact-error-thrown-when-using-microsoft-azure-ad-as-a-saml-identity-provider-864
[KB-1688]: https://community.appian.com/web-browser-43/kb-1688-pdfs-do-not-render-inline-in-the-appian-document-viewer-component-in-google-chrome-862
[KB-1708]: https://community.appian.com/application-design-33/kb-1708-errors-related-to-file-size-thrown-when-using-the-export-to-excel-csv-smart-service-763
[KB-1738]: https://community.appian.com/how-to-36/kb-1738-how-to-check-whether-an-application-import-was-successful-884
[KB-1747]: https://community.appian.com/infrastructure-37/kb-1747-import-dialog-timed-out-error-thrown-when-importing-an-application-or-patch-890
[KB-1771]: https://community.appian.com/integration-39/kb-1771-http-1-1-415-unsupported-media-type-error-returned-when-testing-an-http-request-using-an-integration-object-916
[KB-1776]: https://community.appian.com/cloud-35/kb-1776-http-504-error-received-when-accessing-the-business-database-in-appian-cloud-712
[KB-1788]: https://community.appian.com/administration-32/kb-1788-process-model-alert-setting-send-alerts-to-the-process-initiator-sends-alerts-to-other-recipients-926
[KB-1792]: https://community.appian.com/infrastructure-37/kb-1792-blank-page-and-403-errors-observed-when-accessing-appian-via-zscaler-928
[KB-1794]: https://community.appian.com/application-design-33/kb-1794-details-error-eval-atreason-index-error-thrown-when-using-escalations-timers-and-exception-flows-930
[KB-1819]: https://community.appian.com/integration-39/kb-1819-word-doc-from-template-smart-service-fails-to-replace-placeholders-937
[KB-1822]: https://community.appian.com/infrastructure-37/kb-1822-illegal-mix-of-collations-utf8mb4-unicode-ci-coercible-and-utf8mb4-general-ci-coercible-causes-failure-to-load-a-view-938
[KB-1826]: https://community.appian.com/application-design-33/kb-1826-documents-cannot-be-downloaded-from-appian-designer-943
[KB-1828]: https://community.appian.com/application-design-33/kb-1828-interface-in-design-loads-with-cannot-interpret-context-for-ui-expression-reason-bindings-error-946
[KB-1831]: https://community.appian.com/security-42/kb-1831-cloning-appian-cloud-sites-faq-948
[KB-1835]: https://community.appian.com/application-design-33/kb-1835-constant-based-process-model-start-intervals-do-not-update-with-a-new-constant-value-956
[KB-1848]: https://community.appian.com/application-design-33/kb-1848-invalid-bean-property-name-attachments-error-when-triggering-a-process-via-email-953
[KB-1851]: https://community.appian.com/integration-39/kb-1851-web-apis-return-special-characters-as-question-marks-959
[KB-1854]: https://community.appian.com/application-design-33/kb-1854-opening-a-user-constant-throws-an-all-users-and-groups-must-be-valid-and-visible-to-the-viewer-error-960
[KB-1857]: https://community.appian.com/integration-39/kb-1857-error-processing-request-to-web-api-endpoint-importproperty-when-passing-accented-characters-in-the-request-body-of-a-web-api-879
[KB-1859]: https://community.appian.com/cloud-35/kb-1859-appian-cloud-metrics-and-monitoring-962
[KB-1864]: https://community.appian.com/integration-39/kb-1864-users-not-receiving-emails-from-appian-961
[KB-1867]: https://community.appian.com/application-design-33/kb-1867-start-process-link-not-displayed-because-the-system-is-in-a-degraded-stateless-status-error-when-starting-processes-in-the-appian-for-mobile-devices-app-966
[KB-1882]: https://community.appian.com/administration-32/kb-1882-unable-to-access-the-cloud-database-835
[KB-1887]: https://community.appian.com/infrastructure-37/kb-1887-appian-18-4-custom-email-sender-functionality-return-path-and-sender-fields-differ-from-the-old-custom-email-sender-functionality-974
[KB-1896]: https://community.appian.com/cloud-35/kb-1896-faqs-related-to-email-configuration-on-appian-cloud-981
[KB-1901]: https://community.appian.com/integration-39/kb-1901-saml-authentication-results-in-401-caused-by-message-was-rejected-because-it-was-issued-in-the-future-errors-975
[KB-1903]: https://community.appian.com/security-42/kb-1903-saml-redirecting-to-adfs-login-page-instead-of-using-integrated-windows-authentication-986
[KB-1917]: https://community.appian.com/application-design-33/kb-1917-system-rule-references-revert-to-deprecated-versions-of-system-rules-990
[KB-1918]: https://community.appian.com/integration-39/kb-1918-sap-function-call-reuses-unspecified-connectionproperties-parameters-996
[KB-1923]: https://community.appian.com/web-browser-43/kb-1923-repeated-you-are-already-editing-warnings-in-interface-and-rule-designers-999
[KB-1938]: https://community.appian.com/integration-39/kb-1938-saml-authentication-fails-with-http-401-code-due-to-invalid-signature-1004
[KB-1968]: https://community.appian.com/integration-39/kb-1968-barcode-component-does-not-scan-some-barcodes-on-mobile-1014
[KB-1973]: https://community.appian.com/integration-39/kb-1973-adding-a-connected-environment-fails-with-url-did-not-return-valid-public-key-error-1016
[KB-1979]: https://community.appian.com/application-design-33/kb-1979-health-check-fails-to-run-with-http-404-error-or-unable-to-connect-to-forum-error-1024
[KB-1981]: https://community.appian.com/infrastructure-37/kb-1981-send-email-smart-service-fails-to-send-emails-for-some-processes-with-a-sender-thread-limit-exceeded-error-978
[KB-1989]: https://community.appian.com/infrastructure-37/kb-1989-process-sizing-sheet-is-not-populated-in-the-appian-health-check-report-1033
[KB-1992]: https://community.appian.com/web-browser-43/kb-1992-variables-configured-to-refresh-on-an-interval-do-not-update-when-the-browser-tab-is-in-the-background-1036
[KB-2002]: https://community.appian.com/installation-38/kb-2002-users-unable-to-access-sites-due-to-403-errors-following-an-upgrade-1034
[KB-2010]: https://community.appian.com/how-to-36/kb-2010-how-to-view-spf-records-for-appian-cloud-1045
[KB-2013]: https://community.appian.com/cloud-35/kb-2013-faq-for-restoring-from-a-backup-in-appian-cloud-1044
[KB-2016]: https://community.appian.com/mobile-40/kb-2016-mobile-faq-1048
[KB-2020]: https://community.appian.com/how-to-36/kb-2020-host-name-does-not-match-the-certificate-subject-provided-by-the-peer-cn-customer-endpoint-com-1053
[KB-2024]: https://community.appian.com/infrastructure-37/kb-2024-invalid-function-error-and-missing-dependents-after-object-rename-1052
[KB-2025]: https://community.appian.com/application-design-33/kb-2025-selecting-and-de-selecting-all-items-in-an-editable-grid-results-in-an-incorrect-selection-list-1050
[KB-2029]: https://community.appian.com/application-design-33/kb-2029-unable-to-save-value-in-interface-designer-when-rule-input-is-named-action-1054
[KB-2038]: https://community.appian.com/infrastructure-37/kb-2038-issues-writing-to-mysql-database-when-emojis-or-unicode-characters-are-used-1042
[KB-2043]: https://community.appian.com/administration-32/kb-2043-saml-users-are-redirected-to-a-start-page-instead-of-their-destination-upon-first-login-1065
[KB-2048]: https://community.appian.com/how-to-36/kb-2048-how-to-generate-a-browser-network-capture-har-file-728
[KB-2058]: https://community.appian.com/security-42/kb-2058-appian-cloud-end-of-support-for-tls-1-1-1076
[KB-2065]: https://community.appian.com/web-browser-43/kb-2065-embedded-interfaces-experience-authentication-issues-in-google-chrome-version-80-and-above-1079
[KB-2066]: https://community.appian.com/integration-39/kb-2066-connected-systems-object-authorization-fails-with-query-did-not-return-a-unique-result-following-import-1077
[KB-2076]: https://community.appian.com/application-design-33/kb-2076-trailing-underscores-in-filenames-created-by-text-doc-from-template-smart-service-1086
[KB-2080]: https://community.appian.com/administration-32/kb-2080-integration-object-calls-consistently-return-connection-timed-out-request-timed-out-or-http-400-errors-1087
[KB-2094]: https://community.appian.com/infrastructure-37/kb-2094-java-work-queue-faq-1091
[KB-2100]: https://community.appian.com/how-to-36/kb-2100-overview-of-custom-smtp-server-setup-process-in-appian-cloud-1098
[KB-2104]: https://community.appian.com/application-design-33/kb-2104-record-action-component-fails-to-import-properly-due-to-a-missing-precedent-1100
[KB-2108]: https://community.appian.com/web-browser-43/kb-2108-selecting-context-for-a-process-report-still-prompts-user-to-select-context-1056
[KB-2111]: https://community.appian.com/application-design-33/kb-2111-does-not-exist-process-error-thrown-when-accessing-a-process-instance-1104
[KB-2120]: https://community.appian.com/application-design-33/kb-2120-totalcount-returns-incorrect-results-1108
[KB-2123]: https://community.appian.com/cloud-35/kb-2123-emails-fail-to-send-through-office-365-with-failed-to-process-message-due-to-a-permanent-exception-with-message-error-1095
[KB-2127]: https://community.appian.com/cloud-35/kb-2127-convert-tz-function-returns-null-in-phpmyadmin-1110
[KB-2128]: https://community.appian.com/security-42/kb-2128-web-api-and-connected-system-object-errors-after-applying-a-hotfix-package-1109
[KB-2131]: https://community.appian.com/application-design-33/kb-2131-cdt-fails-to-save-with-the-following-types-cannot-be-used-because-they-do-not-have-a-definition-in-the-appian-data-source-error-1112
[KB-2144]: https://community.appian.com/application-design-33/kb-2144-xor-node-with-multiple-incoming-flows-hangs-on-second-execution-1121
[KB-2146]: https://community.appian.com/application-design-33/kb-2146-cannot-view-or-navigate-to-sites-on-ios-mobile-app-1117
[KB-2148]: https://community.appian.com/application-design-33/kb-2148-export-data-store-entity-to-csv-or-excel-smart-service-only-returns-1000-rows-1125
[KB-2158]: https://community.appian.com/application-design-33/kb-2158-process-variables-unexpectedly-set-to-null-after-asynchronous-sub-process-runs-1124
[KB-2168]: https://community.appian.com/application-design-33/kb-2168-slow-rule-or-content-suggestions-in-appian-designer-1132
[KB-2181]: https://community.appian.com/cloud-35/kb-2181-emails-from-appian-not-received-by-end-users-after-changing-site-domain-and-or-custom-email-sender-1141
[KB-2190]: https://community.appian.com/application-design-33/kb-2190-process-models-fail-to-save-with-non-nullable-input-acp-s-for-unattended-node-s-must-not-be-null-isasynchronous-error-1147
[KB-2191]: https://community.appian.com/integration-39/kb-2191-creating-or-importing-web-api-fails-with-error-could-not-insert-com-appiancorp-webapi-webapi-1146
[KB-2198]: https://community.appian.com/administration-32/kb-2198-your-link-has-expired-message-received-when-resetting-a-user-s-password-1150
[KB-2202]: https://community.appian.com/application-design-33/kb-2202-parent-process-warning-appears-even-after-dependence-on-child-process-model-is-removed-1156
[KB-2203]: https://community.appian.com/integration-39/kb-2203-health-check-data-collection-zip-file-exceeds-the-maximum-size-limit-of-1gb-1154
[KB-2213]: https://community.appian.com/application-design-33/kb-2213-expression-search-fails-with-cdtqueryrequest-error-1161
[KB-2217]: https://community.appian.com/integration-39/kb-2217-web-apis-or-integrations-that-call-the-site-itself-return-403-forbidden-on-cloud-sites-with-trusted-ips-configured-1164
[KB-2222]: https://community.appian.com/application-design-33/kb-2222-a-isnullorempty-returns-false-for-lists-containing-only-null-or-elements-1172
[KB-2228]: https://community.appian.com/how-to-36/kb-2228-how-to-update-default-support-case-contacts-and-email-distribution-lists-for-case-notifications-1174
[KB-2235]: https://community.appian.com/application-design-33/kb-2235-folder-is-smaller-in-target-environment-than-in-source-environment-1212
[KB-2248]: https://community.appian.com/security-42/kb-2248-how-to-configure-default-maintenance-windows-1236
[KB-2262]: https://community.appian.com/application-design-33/kb-2262-google-deprecating-automl-natural-language-1257
[KB-2267]: https://community.appian.com/application-design-33/kb-2267-xor-gateway-condition-path-not-saving-1245
[KB-2277]: https://community.appian.com/how-to-36/kb-2277-how-to-generate-or-reset-health-check-credentials-1351
[KB-2282]: https://community.appian.com/application-design-33/kb-2282-task-escalation-emails-show-html-code-as-plain-text-1176
[KB-2287]: https://community.appian.com/integration-39/kb-2287-the-folder-size-varies-between-the-back-end-and-front-end-1354
[KB-2288]: https://community.appian.com/performance-70/kb-2288-application-server-heap-memory-faq-15935
[KB-2292]: https://community.appian.com/administration-32/kb-2292-disaster-recovery-faqs-1338
[KB-2293]: https://community.appian.com/cloud-35/kb-2293-exporting-a-record-to-excel-fails-due-to-a-network-error-1352
[KB-2298]: https://community.appian.com/infrastructure-37/kb-2298-ai-skill-fails-to-import-and-or-export-1355
[KB-2311]: https://community.appian.com/integration-39/kb-2311-unable-to-connect-to-sql-server-after-upgrading-to-24-1-1382
[KB-2331]: https://community.appian.com/how-to-36/kb-2331-how-to-troubleshoot-database-deadlocks-1391
[KB-2337]: https://community.appian.com/integration-39/kb-2337-openid-connect-and-azure-ad-b2c-authentication-configuration-not-returning-access-token-1392
[KB-2338]: https://community.appian.com/integration-39/kb-2338-snowflake-connected-system-breaks-after-upgrade-to-24-2-1388
[KB-2342]: https://community.appian.com/integration-39/kb-2342-http-headers-appear-with-different-casing-than-expected-1399
[KB-2343]: https://community.appian.com/integration-39/kb-2343-transferring-saml-after-domain-change-1384
[KB-2360]: https://community.appian.com/application-design-33/kb-2360-a-user-is-locked-out-due-to-accessing-an-invalid-task-too-many-times-1406
[KB-2364]: https://community.appian.com/administration-32/kb-2364-additional-storage-faq-1409
[KB-2367]: https://community.appian.com/integration-39/kb-2367-oauth-2-0-client-credentials-grant-connected-system-shows-errors-despite-successful-connection-1413
[KB-2369]: https://community.appian.com/integration-39/kb-2369-apnx-1-4561-032-please-refresh-the-page-and-try-again-error-due-to-stale-portal-pages-1414
[KB-2372]: https://community.appian.com/integration-39/kb-2372-known-unexpected-behaviour-of-left-and-leftb-functions-1400
[KB-2378]: https://community.appian.com/how-to-36/kb-2378-how-to-view-doccenter-version-in-appian-designer-1415
[KB-2379]: https://community.appian.com/how-to-36/kb-2379-appian-cloud-self-service-alerts-1420
[KB-2381]: https://community.appian.com/how-to-36/kb-2381-how-to-fix-a-corrupted-database-table-index-using-phpmyadmin-1421
[KB-2386]: https://community.appian.com/integration-39/kb-2386-log-ingestion-pipelines-fail-for-login-audit-csv-after-upgrading-to-appian-25-4-1423
[KB-2392]: https://community.appian.com/application-design-33/kb-2392-isserviceaccount-field-displays-false-for-service-account-users-15841
[KB-2395]: https://community.appian.com/application-design-33/kb-2395-error-when-deploying-a-process-model-with-semantic-search-similarity-score-field-in-expression-node-output-15871
[KB-2396]: https://community.appian.com/application-design-33/kb-2396-ai-agent-intermittently-fails-with-event-not-found-invalid-tool-response-and-input-too-long-errors-15892
