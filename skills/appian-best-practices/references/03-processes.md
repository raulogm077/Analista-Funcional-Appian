# Best practices — Processes (BPMN)

> Official Appian doctrine for designing process models that are robust, maintainable and
> scalable. Every rule is anchored to official documentation (`docs.appian.com/.../latest/...`)
> or the Appian Community. Links use the `latest` alias, which always redirects to the
> latest release. (The linked
> **Appian RPA** pages carry their own product version — `…/latest/rpa-9.25/…` —: that is their
> canonical path within `/latest/`, not a platform version pin.)

**Contents:** 1. Process design and size · 2. Subprocesses and reuse
· 3. Process variables and memory footprint · 4. Writing data (smart services)
· 5. MNI, parallelism and gateways · 6. Exceptions, timers and robustness · 7. User tasks
· 8. When NOT to use a process · 9. Performance, archiving and monitoring · 10. Email and notifications
· 11. Activity chaining · 12. Changing a process model with instances in flight
· 13. Messaging, timers and scheduled starts · Sources

---

## 1. Process design and size

**✅ Keep processes short: ~50 nodes is the reference threshold.**
Appian Design Guidance raises the *"Too many nodes"* recommendation once you go past **50
nodes**: more nodes complicate maintenance, raise memory consumption and lengthen completion
time. Combine nodes or split into subprocesses. It warns, it doesn't block (doc 10, gate 6).
- ❌ Anti-pattern: a single monolithic process model with 80 nodes that handles an entire
  onboarding flow.
- Source: [Appian Design Guidance — Process model design guidance](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance)

**✅ A single Start Event per process model.**
A process model admits only **one Start Event**; every model has one Start and one End Event.
Multiple entry points connect to the same start node.
- Source: [Start Event](https://docs.appian.com/suite/help/latest/Start_Event.html)

**✅ Formally terminate the process at End nodes.**
It is best practice to mark **Terminate Process** on End Events. A process remains *active*
until **all** active flows reach an end node; without Terminate, a forgotten parallel flow
keeps the instance alive in memory forever. Mark Terminate on most end nodes unless the
process genuinely expects multiple simultaneous active flows.
- ❌ Anti-pattern: unterminated end nodes in a process with AND branches that never close.
- Source: [Process Modeling Tutorial — Configure the end nodes](https://docs.appian.com/suite/help/latest/Process_Modeling_Tutorial.html#configure-the-end-nodes) · [Troubleshooting — process does not complete at end node](https://docs.appian.com/suite/help/latest/Testing_and_Debugging_Problems_with_Process_Models.html#the-process-does-not-complete-when-it-reaches-an-end-node)
- ⚠️ Don't **activity-chain into a Terminate** end event: the terminate then runs as the user who completed the task, who usually can't cancel the subprocesses, so they keep running. End the chained flow on a plain End and terminate from a parallel, unchained flow ([KB-1300](https://community.appian.com/application-design-33/kb-1300-terminate-event-not-cancelling-sub-process-597)).

**✅ One process = one responsibility.**
Appian recommends processes that are "clear and focused, doing a single job." Split when the
flow involves several users, contains timers/wait rules, or reuses standard operations.
When the process is an **AI agent tool**, Appian adds: keep deterministic logic (validations,
calculations, conditional flows) inside the process and leave the agent only the reasoning (doc 12 §3).
- Source: [Prepare process models for AI agent tools](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#before-you-begin-prepare-your-tools-and-actions) (applies the "focused process, single task" doctrine)

---

## 2. Subprocesses and reuse

**✅ Reuse shared functionality as a subprocess.**
Appian recommends using subprocesses for any functionality shared across models. The
Subprocess node links parent and child and transfers data between them.
- Source: [Subprocess](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html)

**✅ Choose synchronous vs. asynchronous with judgment.**
- **Synchronous**: the parent waits for the child to finish; allows passing data in both
  directions and **activity chaining** into the child.
- **Asynchronous**: the parent does not wait; data only travels parent→child (it does not come
  back) and it does **not** support activity chaining. Use it when the activities don't need to
  communicate back.
- Source: [Subprocess — synchronous / asynchronous](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html)

**✅ To launch MANY processes, use Start Process, not the Subprocess node.**
Subprocesses run on the **same execution engine** as the parent: there is no load balancing.
Starting a large number via the Subprocess node concentrates the load on a single engine and
degrades performance. The **Start Process smart service** spreads the load across engines.
Design Guidance flags this explicitly (*"Asynchronous subprocess"*) when an asynchronous
subprocess sits inside a loop or is configured with MNI.
- ❌ Anti-pattern: an asynchronous Subprocess node with MNI of 10,000 instances.
- Source: [Design Guidance — Asynchronous subprocess](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance) · [Start Process Smart Service](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html)

**⚠️ The Subprocess node isn't autoscale-compatible** (neither synchronous nor asynchronous): autoscaled
models start child processes with **Start Process**. The process modeler's design guidance offers to
convert eligible Subprocess nodes (no pass-by-reference, no inherited security, no incoming activity
chaining unless asynchronous); the conversion can't be undone automatically and the child's data leaves
the parent's process reports. ⓥ From 26.9 Start Process can follow activity chaining into an autoscaled
child.
- Source: [Subprocess — Converting subprocess nodes to Start Process nodes](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html#converting-subprocess-nodes-to-start-process-nodes) · [Ways to Start a Process](https://docs.appian.com/suite/help/latest/Ways_to_Start_a_Process_From_a_Process.html#starting-a-process-from-a-process)

**✅ Don't pass a CDT by reference into a subprocess; use input/output variables.**
Active processes keep using the version of the CDT they started with, but a subprocess always
starts with the **latest** version of the CDT. If the parent passes a CDT **by reference** and
the type is updated in the meantime, the parent **breaks** when it reaches the Subprocess node.
Pass the data through input and output variables instead.
- Source: [Design Guidance — Data types passed by reference](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance)

**✅ Don't overuse "wrapper models".**
A model that only wraps a simple smart service (e.g. a single write) plus a gateway degrades
throughput in exchange for a minimal reuse benefit. Configure simple smart services directly in
the relevant process. It is worth wrapping smart services with complex configuration (Send
Email, Document Generation, Stored Procedure) or integrations you expect to replace.
- Source: [Health Check — Simple wrapper process model](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#simple-wrapper-process-model)

**✅ Split long-lived work at hand-offs, and make models restartable.**
A process that lives for weeks is fragile to change and heavy in memory. Split it where work changes
hands into linked models started asynchronously; a "send back" starts a new instance of the earlier
step instead of looping back; each model can start from just an ID and queries what it needs; a small
router model started with Start Process lets a republish reach work that is already in flight.
- Source: [Appian Max — How to Create Flexible Processes](https://community.appian.com/architecture-29/how-to-create-flexible-processes-1224)

---

## 3. Process variables and memory footprint

**✅ Minimize the number of process variables: threshold 100, high risk 300+.**
Design Guidance warns (*"Too many process variables"*) past **100 PVs**; the Health Check marks
100 as medium risk and **300 or more as high risk**. Every PV reserves memory for the
**entire life of the process**, even once completed and unarchived. Convert PVs into
**activity class parameters** (node parameters) where you can, or split into subprocesses.
- Source: [Design Guidance — Too many process variables](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance) · [Health Check — Max process variables per model](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#maximum-number-of-process-variables-per-process-model)

**✅ Remove unused process variables.**
They complicate understanding and maintenance. (Watch out: the check does not see whether the
PV is used by a *process report*; confirm that before deleting.)
- Source: [Design Guidance — Unused process variable](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance)

**✅ Keep PVs small; CDTs and lists multiply the cost.**
The memory risk is higher when PVs are CDTs or lists: there is a multiplier effect per CDT
field or list element, made worse if they change frequently. Prefer **more, smaller models**
with PVs that hold less data, rather than a few complex models with large PVs.
- Source: [Health Check — Max process variables per model](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#maximum-number-of-process-variables-per-process-model) · [Autoscale Patterns and Best Practices — Keep process variables small](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

**✅ Never store large payloads in PVs.**
Avoid large strings (Base64, bulky JSON/XML) in PVs or node inputs: the execution engine's
memory is retained even for completed, unarchived processes. Store large content in a
**document, database table or external storage** and reference the pointer.
- ❌ Anti-pattern: storing an entire PDF as Base64 in a PV.
- Source: [KB-1248 — High memory usage: Memory impact of process variables](https://community.appian.com/how-to-36/kb-1248-how-to-address-high-memory-usage-in-self-managed-appian-environments-536)

**✅ Hard limit of 5 MB per PV in autoscale processes.**
With autoscale, each PV has a size limit of **5 MB**; test in development with the largest
volume you expect. The way out: more models, each holding less data.
- Source: [Autoscale Patterns and Best Practices — Keep process variables small](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

---

**✅ Memory-efficient patterns for long waits and slow integrations.**
Replace timers that wait days or weeks with a nightly scheduler process that queries what is due; let
asynchronous integrations end the process and resume it through a Web API callback or **one** shared
poller (never one poller per instance); mark large, frequently changing PVs as hidden; size models with
the Health Check's process model sizing sheet. Appian Max's design review goes further than the
defaults: models with user input archive after 3 days, the rest delete after 0 days — only where
nothing reads the instance afterwards (see the cleanup-delay trap in §9).
- Source: [Appian Max — How to Create Memory Efficient Models](https://community.appian.com/architecture-29/how-to-create-memory-efficient-models-1215) · [Appian Max — Design Review Checklist](https://community.appian.com/architecture-29/design-review-checklist-1223)

---

## 4. Writing data (smart services)

**✅ Use Write Records for database-backed record types.**
Write Records inserts/updates at the source and syncs the change into Appian automatically. The
record type needs a **database table** as its source (views are not supported) with data sync
(Optimized Data Access) or Direct Data Access with record type features enabled. Limit: **50,000**
records + related records + events combined per node. The user running the node needs
**Viewer** permission on every record type being written (otherwise the node fails and pauses
the process with an exception). Base and related rows are written in **one transaction**: all
tables or none.
- Failure modes differ: if the **write** fails, the node errors but record data stays available;
  if the write succeeds and the **sync** fails (e.g. the tier's synced row limit is exceeded),
  record data becomes **unavailable** — unless "Keep data available at high volumes" absorbs it
  (see doc 01).
- Source: [Write Records Smart Service — Possible errors](https://docs.appian.com/suite/help/latest/Write_Records_Smart_Service.html#possible-errors)

**✅ These smart services sync on their own: Write Records, Write to Data Store Entity, Write to Multiple Data Store Entities, Delete Records, Delete from Data Store Entities.**
When used in processes, interfaces or rules, Appian syncs the change and it is available
instantly on the record type. Write to Data Store Entity auto-syncs up to **50,000 rows** with
a flat CDT and **1,000** with a nested CDT. Changes made through **Query Database, Execute Stored
Procedure, plug-ins** or directly in the database are **not** synced: follow them with **Sync
Records** / `a!syncRecords()` (max **1,000 identifiers per call**; loop for more).
- Source: [Configure Data Sync Options — Smart service syncs](https://docs.appian.com/suite/help/latest/records-data-sync.html#smart-service-syncs) · [Sync Records Smart Service](https://docs.appian.com/suite/help/latest/Sync_Records_Smart_Service.html)

**✅ Write to Data Store Entity: fill in EVERY field of the CDT.**
If you leave a field blank, **null** is written to that column. Capture every needed value
before the node and cast to the correct type with `cast()` if required.
- Source: [Write Records Smart Service](https://docs.appian.com/suite/help/latest/Write_Records_Smart_Service.html) · [Troubleshooting — Unable to write data](https://docs.appian.com/suite/help/latest/Testing_and_Debugging_Problems_with_Process_Models.html#unable-to-write-data)

**✅ Guard the write from the form, not from the database.**
Add validations on the start form (not-null, max length) so you don't reach the node with data
the column rejects (null in a not-null field, length overflow, a PK without auto-increment). The
database constraint stays as the last line of defense; the form is what spares the process an
error node and the user a lost submission.
- Source: [Troubleshooting — Unable to write data](https://docs.appian.com/suite/help/latest/Testing_and_Debugging_Problems_with_Process_Models.html#unable-to-write-data)

**✅ One "action tool" process, one write.**
For processes that create/update data, avoid multiple Write Records nodes for different record
types in the same model. One node, one record type, one purpose.
- Source: [Prepare process models for AI agent tools](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html#before-you-begin-prepare-your-tools-and-actions)

---

## 5. MNI, parallelism and gateways

**✅ Use MNI for nodes that do NOT accept lists; for the ones that do, pass the list.**
Multiple Node Instances (MNI) repeats an activity N times. It is recommended for nodes that
**don't** accept lists of values. Using MNI on nodes that already accept lists (e.g. **Write to
Data Store Entity**) produces unwanted results; pass the list to it directly instead.
- ❌ Anti-pattern: MNI over Write to Data Store Entity to insert N rows.
- Source: [Looping Recipes — Multi-node instances](https://docs.appian.com/suite/help/latest/looping.html#multi-node-instances)

**✅ Know the limits of MNI.**
By default a node can be launched **1,000 times per process** (`MAX_NODE_INSTANCES`, max
150,000); Subprocess MNI ("Allow more than 1000 instances") and robotic task MNI go up to
**150,000**, and in autoscale a node runs up to **10,000 times per process instance**. Loops have
no static limit, but iterating over large volumes consumes a lot of memory. Apply a *circuit
breaker* to cap iterations. If the evaluated number of instances is empty, null or zero, the
process **pauses with an exception**: plan for that case.
- Source: [Looping Recipes — Multi-node instances](https://docs.appian.com/suite/help/latest/looping.html#multi-node-instances) · [Post-Install Configurations — Maximum activity instances](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#maximum-activity-instances) · [Autoscale Patterns and Best Practices](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

**✅ Work in bulk, not in loops; parallel branches are not parallel execution.**
Appian performs best when an action runs once over a list: pass the list to the smart service,
use MNI, or use looping functions inside one script task; offload heavy row-by-row work to the
database (stored procedure / ETL). Branches drawn in parallel **run in sequence** on the engine;
real parallelism comes from starting separate processes with **Start Process**. An **AND
gateway** is still useful to push independent activities out of an activity chain, so the user
doesn't wait for them.
- Source: [Health Check — Process flows with loops](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#process-flows-with-loops) · [Health Check — User experience](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#user-experience) · [Start Process Smart Service — Usage considerations](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html#usage-considerations)

**✅ Route multiple outgoing flows with a gateway, never at random.**
With several outgoing flows and activity chaining, Appian picks one **at random** — which is
not what you want. Standard practice is a gateway:
- **AND** (Parallel Fork/Join): activates every branch; on join, waits for all of them to arrive.
- **XOR** (Exclusive): a single path based on a condition.
- **OR** (Inclusive): one or several paths based on conditions.
- **Complex**: accepts/restricts incoming paths and evaluates outgoing rules.
- Source: [Common Recipes — Configuring multiple outgoing flows](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html#configuring-multiple-outgoing-flows) · [Gateways](https://docs.appian.com/suite/help/latest/Gateways.html)

**✅ A looping gateway with multiple incoming flows → precede it with a Script Task that merges the flows.**
A gateway with several incoming flows lets the first flow through but waits for **all** the
incoming flows to arrive before executing what follows; inside a loop that can hang the process
indefinitely. Place a script task in front to merge the incoming flows.
- ❌ Anti-pattern: a loop that re-enters directly into an AND gateway with two incoming flows.
- Source: [Design Guidance — Gateway nodes with multiple incoming flows](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance) · [Gateways — Usage considerations](https://docs.appian.com/suite/help/latest/Gateways.html)

**✅ In parallel/MNI flows, enable "Keep process variables synchronized".**
When a node runs multiple instances or the flow loops, each copy reads/writes the same PVs and
one instance can **overwrite** another's value. Check *Keep process variables synchronized
across this flow* on the connector's Flow Properties to protect values from being overwritten.
- Source: [Common Recipes — Using process variables in parallel flows](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html#using-process-variables-in-parallel-flows)

---

## 6. Exceptions, timers and robustness

**✅ Capture the result in a variable and route the exception; don't let the process die.**
The official resilience pattern: save the result (success/failure, error message) in an output
variable and use a gateway to route retry, human escalation or logging. It applies to Execute
Robotic Task (the `Success` variable), Execute AI Agent (ⓥ status outputs from 26.8) and, by extension, any smart service
with a status output.
- Source: [Design Patterns (RPA) — Handling unplanned exceptions](https://docs.appian.com/suite/help/latest/rpa-9.25/design-patterns.html#handling-unplanned-exceptions)

**✅ Watchdog timer: a parallel branch with a timer for processes that hang.**
For activities that can take longer than acceptable, run the activity in one branch and a
**timer event** in a parallel branch with the maximum tolerable duration. If the activity
doesn't finish in time, the timer triggers an orderly escalation (human queue, log, fallback).
- Source: [Design Patterns for Production AI Agents — Watchdog timer](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html#error-handling-and-resilience)

**✅ Set a timer to close processes users never complete.**
Incomplete processes stay in memory forever. Add an Intermediate Event Timer that terminates
the process if it isn't completed within a certain window.
- Source: [KB-2011 — High memory usage in Appian Cloud](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047) · [Intermediate Event - Timer](https://docs.appian.com/suite/help/latest/Intermediate_Event_-_Timer.html)

**✅ Send error alerts to a specific application GROUP, never to the default or to individual users.**
The system default only notifies process/model/system administrators, who differ between
environments. And a specific user may not exist in every environment. Use a constant or
expression that points to a **group** in the application, on the Alerts tab.
- ❌ Anti-pattern: error alerts left on "system default" or pointed at a named user.
- Source: [Design Guidance — Misconfigured error alerts](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance)

**✅ Task escalations: configure them on the attended node's Escalations tab.**
There is a dedicated official recipe (*"Escalating a task"*), so you don't need to model the
escalation by hand. An escalation is configured on any **attended node**; when its timer fires
it runs one of **four actions**: **reassign** the task to another user or group, **raise/change
the priority**, **alert** a user or group, or **notify another process** (Send Message Event).
You can **chain several levels**: level 2's timer (and beyond) doesn't start until the
previous level fires. To have the deadline respect the working calendar (excluding weekends),
set the timer with `a!addDateTime(startDateTime: now(), days: N, useProcessCalendar: true)`.
- ❌ Anti-pattern: an approval task that expires without reassigning or alerting anyone because
  no escalation was configured for it.
- Source: [Common Recipes — Escalating a task](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html#escalating-a-task) · [Process Node Properties — Escalation tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#escalation-tab) · [a!addDateTime()](https://docs.appian.com/suite/help/latest/fnc_date_and_time_adddatetime.html)

**✅ The node's Exceptions tab: interrupts the activity and reroutes it by condition.**
The **Exceptions** tab (present on every node except events and gateways) creates alternate
flows: a **Receive Message**, a **Timer** or a **Rule Event** which, once satisfied,
**interrupts/cancels** the activity in progress and diverts the flow down the exception branch
(skipping the rest of the node). Only **one** exception flow is allowed per activity even if it
has several events, and the exception branch does **not** support activity chaining.
- ⓥ **Autoscale:** up to 26.3 exceptions cannot be configured on autoscaled models; rule-based
  exceptions are supported from **26.4** and timer-based ones from **26.5**. In an autoscaled
  process a rule exception that fires on an unattended node sets it to *Skipped*, and rule events
  are evaluated only when the node activates (low-throughput use only). **Receive Message** is not
  autoscale-compatible, so message-based exceptions stay off autoscaled models.
- Source: [Process Node Properties — Exceptions tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#exceptions-tab) · [Rule Event — Usage considerations](https://docs.appian.com/suite/help/latest/Rule_Event.html#usage-considerations)

**✅ Know what each error type does: an unattended node does NOT pause the process; an attended task does.**
Error on an **unattended node** (system logic): the process **does not pause**, parallel
branches keep running and an alert is sent with a link to the Monitor view — which is why a
failed write can go unnoticed if nobody is watching the alerts (send them to a group, not the
default; see above). Error affecting an **attended task**: the **entire process pauses** with
status **"Paused by Exception"** and only a Process Administrator can resume it after fixing the
node. **Transient** errors (`safeToRetry`, no data changed): they don't alert immediately, they
**retry** on their own and only alert once retries are exhausted.
- Unattended activities run FIFO at **lower priority** than user interactions and must finish
  within **60 minutes**, or the process pauses by exception (autoscale nodes: 90 s, doc 05 §4).
- **No dead ends:** without autoscale, if no flow is active after a node completes (a gateway
  returns *-None-*, or a node has no outgoing flow) the process waits **one hour** and then pauses
  by exception. Give every gateway a default path and every node an exit.
- Source: [Process Errors](https://docs.appian.com/suite/help/latest/Process_Errors.html) · [Process Node Properties — Assignment tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#assignment-tab) · [Autoscale Patterns — Considerations for existing process models](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html#considerations-for-using-autoscale-with-existing-process-models)

**✅ Automatic retry: exponential backoff up to 18 h, but Query Database is not retried.**
For a `safeToRetry` error (only when data has **not** been modified) Appian retries at
intervals that roughly double: **32 s → 64 s → 127 s → 4.5 min … → 18 h** (12 attempts); if the
last one fails there are no more and the activity ends up *canceled by exception*. Internal
smart services, Call Web Service (503/408) and Send E-Mail (connection error) are retried;
**Query Database is NOT retried**, so you are responsible for its robustness (capture the
result and route it, the pattern above). An Activity Execution Exception is not `safeToRetry`:
it cancels without retrying.
- Source: [Automatic Error Handling — Retry intervals](https://docs.appian.com/suite/help/latest/Automatic_Error_Handling.html)

---

## 7. User tasks

**✅ Dynamic task name.**
The display name of a User Input Task should include a variable or expression (an ID, an
entered value) so the user can tell instances of the same task apart in Tempo and in task
reports. A static name makes them indistinguishable.
- ❌ Anti-pattern: a literal display name `"Review request"` across 300 open tasks.
- The same applies to the **process** display name (Design Guidance *"Process display name not
  dynamic"*): include an ID or timestamp so instances can be told apart in Process Activity.
- Source: [Design Guidance — Task display name not dynamic / Process display name not dynamic](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance)

**✅ Assign to groups or data-based users, and set the reassignment privileges on purpose.**
Assign attended tasks to **groups** or a data-based user value (`pp!initiator`, a user stored in
the case) — not to named users. The default reassignment privilege lets assignees **reject or
reassign to anyone**; choose deliberately between none, reject only, back to the original
assignees, or anyone. Users with Manager or higher on the process can always reassign. Known
issue: a task passed through a user with Manager/Editor/Administrator rights keeps that user's
reassignment privileges when handed back, so avoid routing tasks through elevated users.
- Rejecting returns the task to the other original assignees. For one task per group member, use
  MNI with *Run one instance for each assignee* + *Run all instances at the same time* + one-to-one
  assignment; otherwise every member gets several copies.
- **Quick tasks** can't be reassigned, and their permissions are evaluated only when first enabled.
- Notifications aren't sent when the recipients exceed `conf.notifications.MAX_RECIPIENTS`
  (default **100**): don't rely on the task email for big groups. Mobile push delivery isn't guaranteed
  either (it depends on Apple and Google): never the only channel for urgent work ([KB-2016](https://community.appian.com/mobile-40/kb-2016-mobile-faq-1048)).
- Source: [Process Node Properties — Assignment tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#assignment-tab) · [Tasks — Rejecting / Reassigning](https://docs.appian.com/suite/help/latest/Tasks.html#rejecting) · [Common Recipes — Creating a quick task](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html#creating-a-quick-task) · [Post-Install Configurations — Maximum notification recipients](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#maximum-notification-recipients) · [KB-2182](https://community.appian.com/application-design-33/kb-2182-reassigned-task-inherits-reassignment-permissions-of-previous-assignee-1133)

**✅ Expose the process to the user as a Record Action or Application Action.**
For users to start processes (create a request, close a ticket, add a document), expose the
model as a **record action** (an action on a record or list) or an **application action**
(a Site page or the Tempo Actions tab). ⓥ Autoscaled models accept start forms from 26.1 (record and
related actions, start process links; application and site actions in the 26.6 docs), activity chaining
from 26.4, and user input tasks after the start form only from 26.9.
- Source: [Ways to Start a Process — from Tempo or sites](https://docs.appian.com/suite/help/latest/Ways_to_Start_a_Process_From_a_Process.html#starting-a-process-from-tempo-or-sites) · [Autoscale — When to use autoscale](https://docs.appian.com/suite/help/latest/autoscale-processes.html#when-to-use-autoscale) · [Autoscale — Activity chaining](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html#activity-chaining-in-autoscaled-processes)

**✅ Process model security: its own role map (it does NOT inherit), by groups, minimum Initiator to start it.**
The process model **does not inherit** security from its parent folder: you must set it on each
model individually. Use **groups, not users** (so you control access by moving group
membership, not by re-editing the role map). To **start** the process — including via the Start
Process smart service or a record action — **Initiator** is enough. The role map's six roles:
**Initiator** (start only; cannot see the model or reports), **Viewer** (view model/reports and
reassign their own tasks), **Manager** (also reassign others' tasks and update PVs), **Editor**
(also edit/save/complete others' tasks), **Administrator** (everything: security, deletion,
in-flight changes, publishing) and **Deny** (blocks everything, useful for excluding a group
nested inside another group that has access).
- ❌ Anti-pattern: granting permissions to named users in the role map, or leaving the model on
  inherited security expecting the folder to cover it (it doesn't).
- Source: [Process Model Object — Process model security](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security) · [Object Security — Groups and role maps](https://docs.appian.com/suite/help/latest/object-security.html#groups-and-role-maps)

**⚠️ Initiator is enough to start a process, not to read its result.**
`a!startProcess()` run by an Initiator-only user starts the process, but PV and model values in
`fv!processInfo` need Viewer (with a synchronous start, `onIncomplete` fires instead). And a user who opens more than 10 invalid
tasks (completed, deleted or not permitted) in 15 minutes is locked out of **all** tasks for 15 minutes:
don't leave stale task links in emails or custom lists (doc 13 §1).
- Source: [Start Process Smart Service](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html) · [KB-2360](https://community.appian.com/application-design-33/kb-2360-a-user-is-locked-out-due-to-accessing-an-invalid-task-too-many-times-1406)

---

## 8. When NOT to use a process

**✅ Pure business logic → expression rule, not a process model.**
A model that contains only **script tasks and gateways** should be replaced with an expression
rule (unless you need to audit the logic). The division of labor: **processes for
orchestration, rules for business logic**. Rules run much faster and with much less overhead
than processes, and support *unit tests*. The risk rises if the model has many nodes or sits on
a critical or high-volume path.
- Source: [Health Check — Process model that could be replaced by a rule](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#process-model-that-could-be-replaced-by-a-rule)

**✅ Avoid chains of script tasks in series.**
Three or more chained script tasks can usually be a rule. Two, for readability, is acceptable
(low risk). The risk spikes if they sit inside a loop or at a performance-sensitive point where
the user is waiting. Use the Script Task's Inputs and Outputs tabs to reduce their number, and
move complex expressions into testable rules.
- Source: [Health Check — Sequential script tasks](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#sequential-script-tasks)

**✅ To read data, use an expression rule; to modify it, use a process model.**
Platform doctrine: use an expression to **read** (query, business logic) and a process model to
**modify** (write to the database, generate documents).
- Source: [Design Patterns (RPA) — Leveraging the low-code power of Appian](https://docs.appian.com/suite/help/latest/rpa-9.25/design-patterns.html#robotic-task-design-patterns)

---

## 9. Performance, archiving and monitoring

**✅ Every process lives in memory until it's archived or deleted.**
The execution engine's memory is proportional to the **total number of instances**: running,
completed, stale and unarchived. Set an aggressive retention policy on the model's **Data
Management** tab.
- Source: [Process Model Object — Data Management tab](https://docs.appian.com/suite/help/latest/process-model-object.html#data-management-tab) · [KB-1248 — Process Execution Engines](https://community.appian.com/how-to-36/kb-1248-how-to-address-high-memory-usage-in-self-managed-appian-environments-536)

**✅ Auto-archive by default (7 days); auto-delete only if the data will never be needed.**
Auto-archive: for processes whose data isn't needed after completion, with the option to
unarchive if regulation requires it (default 7 days, configurable; `0` archives instantly).
Auto-delete: only for processes that will never need their data/metadata viewed afterward — no
trace remains, maximum savings. **Subprocesses do not inherit** the parent's configuration. The
Health Check flags cleanup delays above **7 days**. Archiving frees engine memory, but much of it
stays reserved as pre-allocated space that new processes reuse (the engine file doesn't shrink
by the same amount), so volume control starts in the design, not in the archiving policy.
- Source: [Considerations for Archiving Processes](https://docs.appian.com/suite/help/latest/Archiving_Processes.html) · [Health Check — Long cleanup delay for completed processes](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#long-cleanup-delay-for-completed-processes) · [Configuring Archived Processes](https://docs.appian.com/suite/help/latest/Configuring_Archived_Processes.html)

**⚠️ Keep the cleanup delay longer than whoever reads the process afterwards.**
A Web API that returns `fv!processInfo`, a report or a monitoring screen fails with "Does not exist:
Process" if the instance was already archived or deleted.
- Source: [KB-2111](https://community.appian.com/application-design-33/kb-2111-does-not-exist-process-error-thrown-when-accessing-a-process-instance-1104)

**✅ Archiving frees memory but breaks reporting.**
Data from an archived process **stops being available** for process reports. If you need
historical KPIs, map that data to a **separate reporting process** or export it to an RDBMS
table: don't rely on process archiving for business reporting.
- Source: [Considerations for Archiving Processes — Policy / Historical data](https://docs.appian.com/suite/help/latest/Archiving_Processes.html)

**✅ Identify memory consumers with the Health Check and monitor with the Monitor view.**
The Appian Health Check (*Sizing* section) flags which models generate large instance volumes
or have a large footprint. The **Monitor view / Process Activity** gives visibility into which
processes consume the most and lets you archive/delete ad hoc.
- Source: [KB-2011 — Optimize process models](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047) · [Monitoring view](https://docs.appian.com/suite/help/latest/monitoring_view.html)

**✅ High volume from outside Appian → Web API + `a!startProcess()`, with batching.**
The best way to start autoscale processes from an external system is a **web API** calling
`a!startProcess()`. Frequent calls load the server; use **batching**. The autoscale process
queue accepts a maximum of **700/minute** (the overflow is queued up to 1 million).
- Source: [Autoscale Patterns and Best Practices — Starting large numbers of autoscaled processes](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html)

---

## 10. Email and notifications

> Applies when the solution sends email from the process flow (invitations, reminders, result
> notices). Everything below applies to the **Send E-Mail smart service** inside a process.

**✅ Plain text is the most predictable; rich formatting gets lost.**
**Plain text** emails are the easiest to configure and the ones that look the same across the
widest range of clients. Emails sent from Appian do **not** support: **inline images,
indentation, dividing lines or nested lists**. Design the body assuming plain text; if you need
HTML, test it in several clients before relying on it.
- ❌ Anti-pattern: laying out the invitation with an inline logo, indentation and a nested list
  of requirements.
- Source: [Working with Email — Using the Send E-Mail smart service](https://docs.appian.com/suite/help/latest/email-in-appian.html#sending-emails-from-appian)

**✅ Templates with substitution keys; base template + runtime template pattern.**
To standardize emails, use a **`.txt` or `.html`** template with substitution keys in the
**`###key###`** format: the node scans the template, populates the key grid and replaces each
one with the result of an expression (e.g. a PV). The pattern is a **base template** (the one
that gets scanned) plus a **runtime template** (an expression that returns the `docId` of the
template to use at runtime); that way a single configuration **chooses the template at
runtime**, which is the standard mechanism for **ES/EN localization**. Upload the templates to a
folder and reference them by **constant**. Every key present in the runtime template must also
exist in the base template.
- ❌ Anti-pattern: one Send E-Mail per language on separate process branches, instead of a
  runtime template that picks the template.
- Source: [Send E-Mail Smart Service — Using a template](https://docs.appian.com/suite/help/latest/Send_Email_Smart_Service.html#using-a-template)

**✅ Deliverability: custom sender + a domain with SPF/DKIM/DMARC.**
To avoid landing in spam, configure a **custom sender** and use a "from" domain you are
**authorized to use**, with valid **SPF, DKIM and DMARC** records that include your
environment's mail servers (Cloud or self-managed). **Never** use domains you don't own or
domains that don't exist: SMTP doesn't authenticate them and mail clients flag the message as
suspicious. Without *Email Sender Authentication* set up for the domain, Appian builds the
headers so the email appears sent "on behalf of" (via), precisely so it doesn't look like
spoofing.
- ❌ Anti-pattern: sending from `@gmail.com` or any domain the organization doesn't control.
- Source: [Configuring Custom Email Senders](https://docs.appian.com/suite/help/latest/Configuring_Custom_Email_Senders.html) · [Email on Appian Cloud — Deliverability / DKIM](https://docs.appian.com/suite/help/latest/Email_on_Appian_Cloud.html)

**✅ Reply-To pointed at a monitored mailbox.**
The default address of an email originating from a process is
`<process-instance>@<site-url>`, which **cannot receive replies**. Configure the **Reply To**
field to point at a real mailbox someone monitors, or recipients' replies get lost.
- Source: [Send E-Mail Smart Service — Email Configuration (Reply To)](https://docs.appian.com/suite/help/latest/Send_Email_Smart_Service.html#email-configuration-section) · [Working with Email](https://docs.appian.com/suite/help/latest/email-in-appian.html#sending-emails-from-appian)

**✅ Choose the From field with judgment; watch out for "Undisclosed Recipients".**
The **From** field accepts: **Process, Process Model, Process Initiator, Process Designer** or
**Custom Sender** (which requires a *Sender Display Name* and *Sender Email Address*). If you
send to a **Personal, Restricted or High Privacy Policy** group, the other recipients show up as
**"Undisclosed Recipients"** in the delivered email's To: field — flag that if the business
expects to see the list of recipients.
- Source: [Send E-Mail Smart Service — Email Configuration section](https://docs.appian.com/suite/help/latest/Send_Email_Smart_Service.html#email-configuration-section)

**✅ Sending is sensitive to volume; measure the spam score and add a test toggle.**
Performance depends on **volume** of emails, **size** (attachments especially) and **number of
recipients**. Test with **several email clients** to verify the formatting, measure the **spam
score** with free online tools, and add an application **toggle** to enable/disable sending in
test environments.
- ❌ Anti-pattern: leaving Send E-Mail active in the test environment, firing at real end-user
  addresses.
- Source: [Working with Email — Best practices](https://docs.appian.com/suite/help/latest/email-in-appian.html#sending-emails-from-appian)

**✅ Recipients, senders and mail servers.**
A To field typed as Text fails with "No valid recipients resolved" — wrap it in `toemailrecipient()`;
take the sender address from a constant (a hard-coded sender travels unchanged between environments);
after changing the site domain or the sender, add the site's SPF include; don't relay through an Exchange
Online mailbox (3 concurrent connections) — use the Appian Cloud mail server. More symptoms in doc 13 §4.
- Source: [KB-1046](https://community.appian.com/application-design-33/kb-1046-no-valid-recipients-resolved-error-thrown-when-using-send-email-359) · [KB-1197](https://community.appian.com/application-design-33/kb-1197-custom-email-senders-send-from-old-email-addresses-and-do-not-use-new-values-487) · [KB-2181](https://community.appian.com/cloud-35/kb-2181-emails-from-appian-not-received-by-end-users-after-changing-site-domain-and-or-custom-email-sender-1141) · [KB-1981](https://community.appian.com/infrastructure-37/kb-1981-send-email-smart-service-fails-to-send-emails-for-some-processes-with-a-sender-thread-limit-exceeded-error-978)

---

## 11. Activity chaining

**✅ What it is: chains nodes so the user sees the next screen without returning to their list.**
**Activity chaining** connects two attended nodes through their flow connector (Flow Properties
→ *Enable Activity-Chaining*) so that, on completing a task, the user goes straight to the next
one **without passing through their Task Inbox**. It only chains into **synchronous
subprocesses** (asynchronous ones don't support it — see §2). By default, whoever completes the
first task gets assigned the next ones in the chain; disable that with *Override assignment* on
the connector.
- Source: [Common Recipes — Using activity-chaining to display multiple forms](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html#enabling-activity-chaining)

**✅ Exceeding the limit breaks the chain and produces stale data.**
Between two chained attended tasks, only a limited number of **unattended nodes** (without a
form) fit: `CHAINED_EXECUTION_NODE_LIMIT`, default **50**, maximum **100**, cannot be disabled.
Once you exceed it, the Health Check raises *"Activity chaining limit reached"* and three
symptoms appear:
- The user **doesn't see the next task**: they must accept it from their task list (a source of
  confusion).
- **Dashboards show stale data**, because required nodes haven't finished before the screen
  loads.
- **Web APIs that start processes return stale data**, for the same reason.

The chain also breaks if more than **10 minutes** pass between attended tasks, or in the face of
a receive message / rule / timer event. **MNI** over chained unattended nodes is the typical
cause of exceeding the limit (a separate finding, *"Number of activity chained unattended nodes
using MNI"*).
- ❌ Anti-pattern: an MNI that inserts N rows one at a time between two chained forms.
- Source: [Health Check — Activity chaining limit reached](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#design) · [Post-Install Configurations — Activity-chain limits](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#maximum-activity-instances)

**✅ Mitigation: reduce the chained nodes in the affected processes.**
Review the flagged processes and **reduce the number of nodes with activity chaining enabled**.
Flatten operations (insert all rows at once instead of by MNI), or insert a simple
**"Continue"** form that deliberately breaks the chain before hitting the limit.
- Source: [Health Check — Number of activity chained unattended nodes using MNI](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#number-of-activity-chained-unattended-nodes-using-mni)

---

## 12. Changing a process model with instances in flight

Running instances keep the version of the model they started with; publishing (or importing a package)
only affects **new** instances. When a fix must reach running ones, Appian's **Process Upgrade** moves
them to a newer version, and **Edit Process** changes a single instance; when it doesn't need to reach
them, design the change so both versions can coexist (N/N-1, see doc 08 §3 and doc 11 §7).

**⚠️ A subprocess always starts the LATEST published child — even from parents already running.**
This holds even if the child was republished after the parent started, or after the user accepted an
attended subprocess task. Changing a child's inputs/outputs therefore hits every in-flight parent the
moment it reaches the node: keep child interfaces backward compatible (add, don't rename or retype),
and pass CDTs through input/output variables, not by reference (§2).
- Source: [Subprocess — Usage considerations](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html#usage-considerations)

**✅ Design every change to be backward compatible.**
Running instances keep their process model and CDT versions, but the rules, interfaces and constants they
call run the **latest** version — so logic kept in rules (not in gateway conditions or node inputs) lets a
fix reach in-flight work, and a changed interface can break tasks already open. Therefore: no new
**required** inputs on subprocesses, Receive Message events or task interfaces; new inputs are
null-safe; never delete or rename CDT fields running instances use; add a new rule instead of changing
a signature. Before deploying, start instances on every changed path in a Production-like environment on
the old version, deploy, and complete them.
- Source: [Appian Max — Backward Compatible Design](https://community.appian.com/architecture-29/backward-compatible-design-planning-for-subsequent-deployments-1309) · [Appian Max — Antipatterns](https://community.appian.com/architecture-29/antipatterns-solution-design-mistakes-to-avoid-in-appian-1225) · [Appian Max — In-Flight Testing](https://community.appian.com/delivery-28/in-flight-testing-1335) · [KB-1175](https://community.appian.com/application-design-33/kb-1175-processes-fail-with-could-not-find-variable-ac-variable-error-470)

**✅ Pick the right in-flight tool.**
| Need | Tool | Watch out |
|---|---|---|
| Fix every running instance of a version | **Process Upgrade** | Requirements below; one source version per run |
| Fix one instance | **Edit Process** (Monitor → Edit Process View) | Opening it **pauses** the instance; needs Administrator on the instance |
| Move a stuck task | Monitor → node → **View Node Details** → change assignee | *Reassign Automatically* sends it back to all original assignees |
| Retry a node canceled by exception | Fix the cause, **Resume** the process, then **Start** the node | Check the node is idempotent before re-running it |
| Stop instances | Cancel / Cancel Process | Does **not** cancel synchronous processes started with Start Process, nor autoscaled synchronous subprocesses |

Edit Process details: changes affect an instance only when it reaches the edited node; an already
**activated timer keeps its schedule** (delete and recreate the event to change it); *Apply Changes*
touches only this instance, *Save New Version* also creates a version that must be published. Every
modified instance keeps its own model version in engine memory: use Edit Process sparingly, and prefer a
hotfix or roll-forward for defects that affect many instances ([Appian Max — Addressing a Production Application Defect](https://community.appian.com/delivery-28/addressing-a-production-application-defect-1290)).
- Source: [Monitoring and Editing Processes — Edit mode / Monitor mode](https://docs.appian.com/suite/help/latest/Monitoring_and_Editing_Processes.html#edit-mode) · [Cancel Process Smart Service](https://docs.appian.com/suite/help/latest/Cancel_Process_Smart_Service.html)

**⚠️ Pausing has side effects.**
While an instance is paused its tasks disappear from users' lists and can't be submitted, **messages
sent to it are lost** (not queued), and recurring nodes/timers keep generating instances that all run on
resume (pause 10 minutes with a 1-minute recurrence → 10 executions). Keep pauses short and check
recurring nodes before resuming.
- Source: [Monitoring and Editing Processes — Pausing a process](https://docs.appian.com/suite/help/latest/Monitoring_and_Editing_Processes.html#pausing-a-process)

**✅ Process Upgrade requirements — check them before promising it.**
It runs through Appian's public **Java API** (a custom plug-in or tool), not from Designer. The user needs
**Administrator** rights on the target model; the processes can't be locked or open in Edit/Monitor
mode. Existing PVs must keep name, type and multiplicity (keep obsolete PVs as **hidden** instead of
deleting them); alerts must not reference PVs or `pp!` properties. New PVs get the type's **default
value** (set real values afterwards through the API); nodes missing from the target are **canceled**,
but canceling a subprocess node does **not** cancel the subprocess. When models exchange messages,
upgrade the **receiving** model first. A recurring node can't be changed in place: copy it, modify the
copy, remove the original. Only one source version is upgraded per run.
- Source: [Process Upgrade Guidance — Requirements / Impact on the upgraded processes](https://docs.appian.com/suite/help/latest/Process_Upgrade.html#requirements-for-upgrade)

**✅ Before a Process Upgrade: off-peak window, full backup, and documentation of the source model.**
Process Upgrade requires recreating the analytics engines afterwards, so plan an outage and run it
off-peak (especially when upgrading several related models). Take a full backup, and generate the
**process model documentation of the source version** first: after the upgrade, Edit Mode shows the
target configuration even for tasks that keep the old one.
- Source: [Process Upgrade Guidance — Best practices](https://docs.appian.com/suite/help/latest/Process_Upgrade.html#best-practices)

**❌ Don't upgrade with the models open or nodes being moved by hand.**
Close Monitor Mode and Edit Mode on every process to be upgraded (a locked process makes the upgrade
fail), and don't manually start or cancel nodes until the whole upgrade finishes, so tasks created by it
use the upgraded configuration.
- Source: [Process Upgrade Guidance — Best practices](https://docs.appian.com/suite/help/latest/Process_Upgrade.html#best-practices)

**✅ A process model used as an AI agent tool follows extra rules** — single task, no child processes,
record type input for writes, errors returned as output instead of terminating. They are in
`12-ai-agents-and-skills.md` §3 and §6.

---

## 13. Messaging, timers and scheduled starts

**✅ Target messages at a process ID; filter with conditions, not expressions.**
Set `DestinationProcessID` on the Send Message event (Design Guidance *"No target process for send
message event"*): only that process's receivers are scanned, instead of every active receiver. On
Receive Message and Rule events, use **conditions** rather than expressions: they are cheaper to evaluate
(on Receive Message, conditions are evaluated together and expressions one by one). Keep the number of active listeners low.
- Source: [Messaging Best Practices](https://docs.appian.com/suite/help/latest/Messaging_Best_Practices.html) · [Health Check — Send Message events not targeting a process instance](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#send-message-events-not-targeting-a-process-instance) · [Rule Event](https://docs.appian.com/suite/help/latest/Rule_Event.html)

**❌ Don't use messaging as a synchronous or guaranteed channel.**
Avoid message loops that mimic request/response between processes and cascades where one message
triggers several more: both create race conditions and message growth. A message is **lost** if no
matching receiver is active, if its conditions don't match, or if the target process is paused. When
delivery matters, persist the state (database/record) and let the receiver read it. Receive and Send
Message are not compatible with autoscale.
- Source: [Messaging Best Practices — Avoid message loops / cascading messages](https://docs.appian.com/suite/help/latest/Messaging_Best_Practices.html#improving-messaging-efficiency) · [Receive Message Event — Usage considerations](https://docs.appian.com/suite/help/latest/Receive_Message_Event.html#usage-considerations) · [Send Message Event](https://docs.appian.com/suite/help/latest/Send_Message_Event.html)

**✅ Timers and schedules: know how they behave after you change them.**
- Interval recurrence has a **5-minute minimum**; for a delay under a minute use an expression
  (`now() + intervalds(0,0,x)`); use `a!addDateTime(..., useProcessCalendar: true)` to skip non-working
  days.
- A recurring Start Event keeps firing once the model has been published; to stop it, **republish
  without the schedule**.
- A node on the Scheduling tab restarts at every interval **even if earlier instances are still
  running** — guard against overlap.
- Autoscale: no timer on the Start Event and no recurrence; standalone timers (minimum delay 60 s)
  and, ⓥ from 26.5, timer exceptions (§6).
- A constant used as a recurring start interval is read at publish: republish after changing it
  ([KB-1835](https://community.appian.com/application-design-33/kb-1835-constant-based-process-model-start-intervals-do-not-update-with-a-new-constant-value-956)). Durations beyond ~24.8 days overflow `intervalds()` — use days or `a!addDateTime()`
  (doc 04 §11), and pass rule arguments **by position** inside event expressions (doc 04 §2).
- Source: [Timer Event](https://docs.appian.com/suite/help/latest/Intermediate_Event_-_Timer.html) · [Start Event — Timer recurrence](https://docs.appian.com/suite/help/latest/Start_Event.html#configuring-a-timer-trigger-on-a-start-event) · [Process Node Properties — Scheduling tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#scheduling-tab)

---

## Sources

Official documentation (`latest` redirects to the latest release, published monthly):

1. [Appian Design Guidance — Process model design guidance](https://docs.appian.com/suite/help/latest/appian-recommendations.html#process-model-design-guidance) — Too many nodes, Too many process variables, Unused process variable, Task display name not dynamic, Asynchronous subprocess, Data types passed by reference, Gateway nodes with multiple incoming flows, Misconfigured error alerts.
2. [Understanding the Health Check Report](https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html) — Max process variables per model, Process model that could be replaced by a rule, Sequential script tasks, Simple wrapper process model, Activity chaining limit reached, Number of activity chained unattended nodes using MNI.
3. [Subprocess](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html) — synchronous/asynchronous, same engine, reuse recommendation.
4. [Start Process Smart Service](https://docs.appian.com/suite/help/latest/Start_Process_Smart_Service.html) · [Ways to Start a Process](https://docs.appian.com/suite/help/latest/Ways_to_Start_a_Process_From_a_Process.html).
5. [Gateways](https://docs.appian.com/suite/help/latest/Gateways.html) · [Common Process Model Workflows and Recipes](https://docs.appian.com/suite/help/latest/Process_Model_Recipes.html) — multiple outgoing flows, parallel flows / keep PVs synchronized, using activity-chaining to display multiple forms, **escalating a task** (four actions, chained levels, `a!addDateTime` with `useProcessCalendar`).
6. [Looping Recipes — Multi-node instances](https://docs.appian.com/suite/help/latest/looping.html#multi-node-instances).
7. [Write Records Smart Service](https://docs.appian.com/suite/help/latest/Write_Records_Smart_Service.html) · [Configure Data Sync Options](https://docs.appian.com/suite/help/latest/records-data-sync.html) · [Troubleshooting Process Models](https://docs.appian.com/suite/help/latest/Testing_and_Debugging_Problems_with_Process_Models.html).
8. [Start Event](https://docs.appian.com/suite/help/latest/Start_Event.html) · [End Event](https://docs.appian.com/suite/help/latest/End_Event.html) · [Process Modeling Tutorial](https://docs.appian.com/suite/help/latest/Process_Modeling_Tutorial.html).
9. [Autoscale Patterns and Best Practices](https://docs.appian.com/suite/help/latest/autoscale-patterns-practices.html).
10. [Considerations for Archiving Processes](https://docs.appian.com/suite/help/latest/Archiving_Processes.html) · [Process Model Object — Data Management tab](https://docs.appian.com/suite/help/latest/process-model-object.html#data-management-tab) · [Monitoring view](https://docs.appian.com/suite/help/latest/monitoring_view.html).
11. [Design Patterns for Production AI Agents](https://docs.appian.com/suite/help/latest/agent-studio-design-patterns.html) · [Design Patterns (Appian RPA)](https://docs.appian.com/suite/help/latest/rpa-9.25/design-patterns.html) · [Prepare process models for AI agent tools](https://docs.appian.com/suite/help/latest/create-and-configure-ai-agent.html).
12. [Working with Email](https://docs.appian.com/suite/help/latest/email-in-appian.html) · [Send E-Mail Smart Service](https://docs.appian.com/suite/help/latest/Send_Email_Smart_Service.html) · [Configuring Custom Email Senders](https://docs.appian.com/suite/help/latest/Configuring_Custom_Email_Senders.html) · [Email on Appian Cloud](https://docs.appian.com/suite/help/latest/Email_on_Appian_Cloud.html) — plain text limits, base + runtime templates with substitution keys, custom sender / SPF-DKIM-DMARC, Reply To, From options and "Undisclosed Recipients", performance and test best practices.
13. [Post-Install Configurations — Activity-chain limits](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html#maximum-activity-instances) — `CHAINED_EXECUTION_NODE_LIMIT` (default 50, max 100, cannot be disabled) and `MAX_NODE_INSTANCES`.
14. [Process Node Properties](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html) — [Escalation tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#escalation-tab) (four actions, attended nodes only, chained levels) and [Exceptions tab](https://docs.appian.com/suite/help/latest/Process_Node_and_Smart_Service_Properties.html#exceptions-tab) (Receive Message / Timer / Rule, interrupts and reroutes, no activity chaining; autoscale support for rule exceptions from 26.4 and timer exceptions from 26.5) · [a!addDateTime()](https://docs.appian.com/suite/help/latest/fnc_date_and_time_adddatetime.html).
15. [Process Errors](https://docs.appian.com/suite/help/latest/Process_Errors.html) — unattended node doesn't pause vs. attended task "Paused by Exception" vs. transient errors · [Automatic Error Handling](https://docs.appian.com/suite/help/latest/Automatic_Error_Handling.html) — `safeToRetry`, retry intervals 32 s→18 h, Query Database is not retried.
16. [Process Model Object — Process model security](https://docs.appian.com/suite/help/latest/process-model-object.html#process-model-security) (does not inherit from the folder, minimum Initiator, roles Initiator/Viewer/Manager/Editor/Administrator/Deny) · [Object Security — Groups and role maps](https://docs.appian.com/suite/help/latest/object-security.html#groups-and-role-maps) (use groups, not users).

17. [Process Upgrade Guidance](https://docs.appian.com/suite/help/latest/Process_Upgrade.html) — requirements, impact on upgraded processes, best practices (off-peak, backup, source documentation, closed Monitor/Edit modes, no manual node changes during the upgrade) · [Monitoring and Editing Processes](https://docs.appian.com/suite/help/latest/Monitoring_and_Editing_Processes.html) — Edit Process, pausing side effects, node actions · [Subprocess — Usage considerations](https://docs.appian.com/suite/help/latest/Sub-Process_Activity.html#usage-considerations) — latest published child · [Cancel Process Smart Service](https://docs.appian.com/suite/help/latest/Cancel_Process_Smart_Service.html).
18. [Messaging Best Practices](https://docs.appian.com/suite/help/latest/Messaging_Best_Practices.html) · [Send Message Event](https://docs.appian.com/suite/help/latest/Send_Message_Event.html) · [Receive Message Event](https://docs.appian.com/suite/help/latest/Receive_Message_Event.html) · [Rule Event](https://docs.appian.com/suite/help/latest/Rule_Event.html) · [Timer Event](https://docs.appian.com/suite/help/latest/Intermediate_Event_-_Timer.html) · [Tasks](https://docs.appian.com/suite/help/latest/Tasks.html) · [Post-Install Configurations](https://docs.appian.com/suite/help/latest/Post-Install_Configurations.html) — `MAX_NODE_INSTANCES`, `MAX_RECIPIENTS`.

Appian Community:

19. [KB-1248 — High memory usage (self-managed)](https://community.appian.com/how-to-36/kb-1248-how-to-address-high-memory-usage-in-self-managed-appian-environments-536).
20. [KB-2011 — High memory usage (Appian Cloud)](https://community.appian.com/how-to-36/kb-2011-how-to-address-high-memory-usage-in-appian-cloud-environments-1047).
21. [Playbook — Advance your Process Models](https://community.appian.com/architecture-29/advance-your-process-models-1364) (an index of guides; the detail lives in the linked guides).
22. [KB-2182 — Reassigned task inherits reassignment permissions of previous assignee](https://community.appian.com/application-design-33/kb-2182-reassigned-task-inherits-reassignment-permissions-of-previous-assignee-1133).
