# Best practices — ALM, testing, naming conventions and development approach

> Official Appian doctrine on how to name, structure, test, version and deploy applications,
> and how to govern their quality over time. Every rule is anchored to `docs.appian.com/suite/help/latest/…`.
> Links with `latest`: an alias that redirects to the newest release, so they never expire.

**Contents:** 1. Object naming · 2. Application structure · 3. ALM / deployment across environments
· 4. Testing · 5. Development approach and methodology · 6. Documentation and maintainability of objects
· 7. Continuous quality control (Health Check, design guidance, technical debt) · Sources

---

## 1. Object naming

The official **Standard Object Names** page defines a standard per object type. It is adaptable to your
organization, but its backbone — application prefix + case convention per type — is not something to
improvise.

✅ **Give each application a short, unique prefix, and start every technical object's name with it.**
Domain initials (e.g. `HRO` for *HR Onboarding*). It's configured when creating the app and pre-fills the
name of new objects.
- **Why:** the prefix visually groups an app's objects in a shared environment and avoids
  name collisions (which must be unique across the environment for data stores, CDTs and record types).
- **Anti-pattern:** objects with no prefix mixed in with those of 458 other apps in the environment;
  impossible to tell at a glance what's yours.
- Source: <https://docs.appian.com/suite/help/latest/Standard_Object_Names.html> · <https://docs.appian.com/suite/help/latest/creating-applications.html>

✅ **Respect the case Appian prescribes for each object type:**

| Object | Convention | Official example |
|---|---|---|
| Application (unpublished) | Title Case with spaces + version suffix | `HRO HR Onboarding All Contents v1.0` |
| Data Store | Title Case with spaces | `HRO Employee Data` |
| Custom Data Type | Title Case with underscores + own namespace | `HRO_Employee_Data` (`urn:appian:hro`) |
| Record Type | Singular, descriptive | `HRO Employee` |
| Constant | UPPERCASE with underscores, optional secondary prefix | `HRO_IMG_CAREER_HISTORY_ICON` |
| Decision | PascalCase | `HRO_DetermineEligibilityStatus` |
| Expression Rule | PascalCase, optional secondary prefix | `HRO_ComputeBaseSalary` |
| Integration | PascalCase | `HRO_GetApplicationInformation` |
| Interface | PascalCase | `HRO_AddNewEmployee` |
| Process Model | Title Case with spaces | `HRO Onboard New Employee` |
| Web API | Spaces allowed | `HRO Get LinkedIn Profile` |
| Folder / Group / Site (internal) | Title Case with spaces | `HRO Process Models` |

- **Why:** the case communicates the object type before you even open it; an `HRO_ComputeBaseSalary`
  reads as a rule, an `HRO Employee Data` reads as data.
- Source: <https://docs.appian.com/suite/help/latest/Standard_Object_Names.html>

❌ **Don't put the application prefix on objects the end user sees.** Published applications,
sites (visible name), business groups, reports, actions and feeds use a descriptive, meaningful
name, without a prefix.
- **Why:** Appian uses the published app's name to group actions in Tempo; a technical prefix
  leaks straight into the user's face. Example: internal site `HRO Onboarding`, visible name `Onboarding`.
- Source: <https://docs.appian.com/suite/help/latest/Standard_Object_Names.html>

✅ **Use singular, descriptive names for record types; Appian generates the visible plural.** `HRO Employee`
→ the user sees "Employees".
- Source: <https://docs.appian.com/suite/help/latest/Standard_Object_Names.html>

✅ **Give record types a business display name, not the technical abbreviation.** Prefer
`Case Managers` / `Human Resource Employees` over `CM Employee` / `HR Employees`.
- **Why:** the display name appears in Process HQ and feeds AI features; clear business terms make
  data more usable and better for AI.
- Source: <https://docs.appian.com/suite/help/latest/build-best-data-fabric.html>

❌ **Don't change an app's prefix after creating objects expecting a mass rename.** Appian does **not**
bulk-update existing names; you have to edit every object by hand.
- Source: <https://docs.appian.com/suite/help/latest/creating-applications.html>

⚠️ **Renaming is not free:** dependents that reference an object by name can miss the rename ("Invalid function"); rename back, re-save the dependents and rename again. Object names can't be translated — user-facing text belongs in translation sets ([KB-2024](https://community.appian.com/infrastructure-37/kb-2024-invalid-function-error-and-missing-dependents-after-object-rename-1052), [Appian Max — Frequently Reused Appian Components](https://community.appian.com/delivery-28/frequently-reused-appian-components-1219)).

---

## 2. Application structure

✅ **One application per business solution.** *CRM*, *Employee Onboarding* and *Sales Opportunities* are
three apps, not one.
- **Why:** it's the unit of deployment and security; splitting by domain keeps packages
  small and dependencies clear.
- Source: <https://docs.appian.com/suite/help/latest/creating-applications.html>

✅ **Remember the app is a list of associated objects, not an exclusive container.** An object can be
associated with several apps; the **Objects** view lists them ignoring that association.
- **Why:** it shapes how you split shared objects and what you pull in when packaging.
- Source: <https://docs.appian.com/suite/help/latest/design-objects.html>

✅ **Treat shared objects (subprocesses, groups, folders, common rules) as a risk zone.**
Changing or importing them can have side effects on other apps in the environment.
- **Why:** the impact of a shared object propagates outside your app; review it with dependents
  analysis before touching it.
- Anti-pattern: editing a "common" rule for your use case and silently breaking another
  application that reuses it.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

✅ **Before any significant change, run dependents and precedents analysis (impact analysis).**
Dependents = blast radius (everything that needs to be re-tested); precedents = everything the
object references (and that you must include in the package).
- **Why:** it avoids deploying with missing precedents and breaking the target.
- Source: <https://docs.appian.com/suite/help/latest/Trace_Relationships_for_Impact_Analysis.html> · <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>

✅ **Generate the standard groups and folders when creating the app** (security checkbox) to organize
and secure objects from minute zero.
- Source: <https://docs.appian.com/suite/help/latest/creating-applications.html>

✅ **Shared objects have an owner.** Keep common objects in a common-objects application with a documented owner, usage and notify list; owners are Administrators, everyone else Viewer; a change goes request → dependents check → temporary grant → regression. With several teams on one platform: prefer one shared Dev environment, hide unreleased shared changes behind boolean feature-toggle constants or restrictive role maps, keep the deployer group small, and never release the same app from two teams at once.
Source: [Appian Max — Shared Object Management Overview](https://community.appian.com/architecture-29/shared-object-management-overview-1293) · [Appian Max — Managing Multiple Concurrent Delivery Teams](https://community.appian.com/delivery-28/managing-multiple-concurrent-delivery-teams-1287)

---

## 3. ALM / deployment across environments

### Environment model

✅ **Always promote from lower to higher: Dev → Test → Production.** Supported deployment paths
include Dev→Test, Dev1→Dev2, Break/Hotfix→Dev and Test→Prod.
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

❌ **Never modify objects directly in Production.** Changes are born in Dev and travel by
package. The only exception is a Break/Fix (hotfix) flow, which additionally **flows back into Dev**
so the fix isn't lost.
- **Why:** a direct change in Prod isn't versioned in the pipeline and gets lost in the next
  deployment from Dev, which overwrites it.
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

⚠️ **Deploy only from an earlier to the same or a later Appian version, never in reverse** (same version
with different hotfixes is fine). On Appian Cloud environments can sit on different releases: schedule
upgrades so Test and Production are never on an earlier version than Dev while packages are flowing.
DocCenter is stricter still: same platform version (doc 12 §10.3).
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

⚠️ **Security and load tests on Appian Cloud need planning with Appian.** Penetration/vulnerability tests
require notice through a support case at least **3 business days** before; a snapshot/restore around a
test also needs a support case 3 days ahead. Performance testing before a production launch is strongly
recommended (Support doesn't help with the tools).
- Source: <https://docs.appian.com/suite/help/latest/Appian_Cloud_FAQ.html#performance-security-and-encryption>

✅ **Grow the environment chain after the first go-live** (Appian Max): add a production-like release-candidate environment (≥ 4 environments), and a Prod-Fix environment when several teams release often. Default to one shared platform; separate installations only for a mission-critical 24x7 high-volume app, strict regulatory isolation, sensitive data mixed with public-facing use, or fully separate users and data.
- Source: [Appian Max — Recommended Environments](https://community.appian.com/platform-30/recommended-environments-1221) · [Appian Max — When to Consider Exceptions to a Shared Environment](https://community.appian.com/platform-30/when-to-consider-exceptions-to-an-appian-shared-environment-1303)

### Packages

✅ **Start a package for the application from the beginning of development** instead of deploying the
whole app every time.
- **Why:** a package scopes the change, makes deployment more agile and flexible, and enables
  incremental Compare & Deploy.
- Source: <https://docs.appian.com/suite/help/latest/creating-applications.html> · <https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html>

✅ **Prefer Compare & Deploy (direct) between connected environments.** Appian offers three methods:
direct (compare and deploy), programmatic (deployment APIs, for CI/CD) and manual (export/import ZIP).
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

✅ **Review the package with object comparison before promoting.** Compares version to version and
surfaces missing precedents.
- Source: <https://docs.appian.com/suite/help/latest/prepare-deployment.html#comparing-across-environments> · <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>

✅ **Package hygiene that prevents failed imports:** only the **published** process model version is exported (Save & Publish first); every child model must be published; include the record type behind any record action component; add the plug-ins the application references; deploy shared precedent apps first, and allow no circular dependencies between apps. Toward pre-production and Production, deploy the whole application with the same package, DDL, plug-ins and ICF.
- Source: [KB-1254](https://community.appian.com/application-design-33/kb-1254-latest-changes-in-a-process-model-are-not-included-in-an-export-540) · [KB-1237](https://community.appian.com/application-design-33/kb-1237-generic-error-thrown-when-attempting-to-start-a-process-with-sub-processes-525) · [KB-2104](https://community.appian.com/application-design-33/kb-2104-record-action-component-fails-to-import-properly-due-to-a-missing-precedent-1100) · [KB-2260](https://community.appian.com/how-to-36/kb-2260-how-to-export-application-packages-without-missing-precedents-1244) · [Appian Max — Application Deployment Guide](https://community.appian.com/platform-30/application-deployment-guide-1222)

⚠️ **A 502/504 in the import dialog doesn't mean the import failed:** imports run in the background (since 21.4); confirm in the News feed and Admin Console › Import History, which keeps 30 days — archive the evidence.
- Source: [KB-1747](https://community.appian.com/infrastructure-37/kb-1747-import-dialog-timed-out-error-thrown-when-importing-an-application-or-patch-890) · [KB-1738](https://community.appian.com/how-to-36/kb-1738-how-to-check-whether-an-application-import-was-successful-884) · [KB-1282](https://community.appian.com/administration-32/kb-1282-incomplete-import-history-in-admin-console-565)

### Programmatic deployment — Deployment REST API (CI/CD)

✅ **For CI/CD, use the native Deployment REST API: six endpoints that automate the full
export → inspect → import cycle.** Called on `https://<domain>/suite/deployment-management/<v#>`:
1. **Export** apps/packages · 2. **Inspect** apps/packages · 3. **Get inspection results** ·
4. **Import (deploy)** · 5. **Get deployment results** · 6. **Get deployment log**. In addition,
**Application Package Details** retrieves the **package UUID** that triggers the export/import.
- **Why:** you build the pipeline once and every deployment runs the same way, without manual errors;
  it integrates with external tools (e.g. Jenkins) and triggers the post-deployment process.
- **Flow:** Appian recommends **always inspecting before deploying**; the `POST` calls distinguish
  import from export with the `Action-Type` header, and the `GET` calls (statuses, log) are available
  **always**, regardless of the Admin Console settings.
- Source: <https://docs.appian.com/suite/help/latest/Deployment_Rest_API.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

✅ **Authenticate the API with an API key or OAuth 2.0 tied to a service account** (the same mechanism
that secures Web API objects); both are created in the Admin Console. For extra security, upload
trusted server certificates and enable **mTLS** (requests over port 8443).
- Source: <https://docs.appian.com/suite/help/latest/Deployment_Rest_API.html> · <https://docs.appian.com/suite/help/latest/admin-certificates.html>

⚠️ **Choose the API version according to your Appian release, and enable it before using it.** There
are three: **V1** (Appian ≤ 23.2), **V2** (≤ 26.4) and **V3** (26.5+). Each version adds flexibility:
**V3** is the only one that supports **multiple packages** in a single deployment and **DB scripts
from different sources**. Endpoints are enabled in **Admin Console → Infrastructure**.
- Source: <https://docs.appian.com/suite/help/latest/Deployment_Rest_API.html> · <https://docs.appian.com/suite/help/latest/admin-infrastructure.html>

### Import Customization File (ICF)

✅ **Use an Import Customization File (ICF) for values that change per environment or aren't
exported.** It's a `.properties` template that Appian generates (you download, edit and upload it) to
fix in the target: credentials/passwords, connected systems, integrations, environment-specific
constants and Admin Console settings. It's also used to **force the update of unchanged objects**
(`importSetting.FORCE_UPDATE=true`) and to **trigger a sync** of a record type
(`recordType.<UUID>.forceSync=true`).
- **Why:** it decouples secrets and per-environment values from the object package; the same package
  gets promoted to Test and to Prod by only changing the ICF.
- Source: <https://docs.appian.com/suite/help/latest/Managing_Import_Customization_Files.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

⚠️ **Watch the ICF syntax: `#` comments out (ignored), and uncommenting a valid property without
setting a value leaves it `null` in the target.** Every line of the template comes commented out by
default; uncomment only what you want to change and put the value after the `=`. **A single ICF per
deployment**, even when deploying several packages: you have to consolidate everything into one file.
Keep **one ICF per environment** in the pipeline (non-applicable properties are ignored). For
constants used as a feature toggle or counter, **leave the line commented out** so you don't overwrite
the target's value.
- Source: <https://docs.appian.com/suite/help/latest/Managing_Import_Customization_Files.html>

### Database scripts in deployment

✅ **Include DB scripts (`.sql`/`.ddl`) in the package and fix their execution order.** Appian runs
**all scripts before deploying any object**; if a script fails, the deployment **stops** (and rolls
back what it can) — check the deployment log. The order **within** a package is persisted in the
package; the order **between** packages is not persisted (check it on every Compare & Deploy). Keep
the DDL versioned in the repository, alongside the rest of the solution's code.
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html> · <https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html>

⚠️ **DB scripts and plug-ins are NOT exported with the object package; they're a separate step that
requires direct deployment permission.** And if the data source is a **connected system** that also
travels in the deployment, you have to **deploy the DB scripts separately from the connected system**.
If a script touches the data of a synced record type that isn't in the package, trigger the sync with
the ICF (`forceSync`).
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html> · <https://docs.appian.com/suite/help/latest/data-source-connected-systems.html>

✅ **Scripts that can run twice.** `CREATE TABLE IF NOT EXISTS`, `CREATE OR REPLACE VIEW`, `DROP … IF EXISTS` before `CREATE`, `ALTER` guarded by an `INFORMATION_SCHEMA` check, `INSERT IGNORE`/`ON DUPLICATE KEY UPDATE`; don't drop columns that running code or instances still use; write DDL incrementally and never edit a script that has already been released.
- Source: [Appian Max — SQL Scripts that can be Rerun](https://community.appian.com/architecture-29/sql-scripts-that-can-be-rerun-1300) · [Appian Max — Deployment Automation](https://community.appian.com/platform-30/deployment-automation-1329)

### Deployment gates and automation

✅ **Open the deployment gates in the target environment's Admin Console before promoting scripts or
plug-ins.** The **"Allow deployments with plug-ins"** and **"Allow deployments with database
scripts"** settings must be enabled in the target, or that content won't get in. For high
environments (Production), **require prior review/approval**: with review enabled, the app's
administrators and the reviewer group get an email and approve or reject in the **Deploy** view.
- Source: <https://docs.appian.com/suite/help/latest/admin-infrastructure.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

✅ **Use Appian's own deployment tooling instead of home-grown export/import scripts:** Compare and
Deploy first (Appian's recommendation for most teams), the **deployment REST APIs** for CI/CD, and the
DevOps Quick Start and Automated Versioning Manager for version control. ⚠️ The Automated Import
Manager described in the older Deployment Automation guide is retired: the docs say to deploy with the
REST APIs instead.
- Source: <https://docs.appian.com/suite/help/latest/devops-with-appian.html> · <https://docs.appian.com/suite/help/latest/deployments-view.html#view-the-deployments-grid> · <https://community.appian.com/platform-30/appian-devops-quick-start-1256>

⚠️ **Environment-specific settings are NOT deployed: API keys and certificates are configured by hand
in each environment.** The ICF covers object secrets (credentials, connected systems), but these
platform settings don't travel in the package.
- Source: <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html> · <https://docs.appian.com/suite/help/latest/Appian_Administration_Console.html>

⚠️ **Validate AppMarket plug-ins BEFORE a platform upgrade, and test them thoroughly before
Production.** Plug-ins and shared components are used **at your own risk** and Appian doesn't
guarantee they work; in a **shared** cloud environment with other applications, an incompatible
plug-in after the upgrade can affect everyone.
- Source: <https://docs.appian.com/suite/help/latest/plugindisclaimer.html>

✅ **Production defects: hotfix, then roll forward, restore last.** Hotfix only critical issues, with a patch that contains only the hotfix objects; if Dev has moved on, build it in an environment that matches Production; log it, merge it back and run regression. Next option: roll forward to the previous application version. Restoring a backup reverts the **whole site** and loses data for every app (doc 13 §10).
- Source: [Appian Max — Deploying an Application Hotfix](https://community.appian.com/delivery-28/deploying-an-application-hotfix-1278) · [Appian Max — Addressing a Production Application Defect](https://community.appian.com/delivery-28/addressing-a-production-application-defect-1290)

✅ **Cloud upgrades:** upgrade Test first, then Production, then Dev; review deprecations before; deployments pause during the upgrade; set default maintenance windows and put a distribution list on maintenance notices. A CI/CD runner needs its public IP in Trusted IPs. Version control: trunk-based (Dev is the branch), a git tag per deployed environment, secrets in a vault.
- Source: [Appian Max — Manage Your Appian Cloud Upgrade](https://community.appian.com/platform-30/manage-your-appian-cloud-upgrade-1240) · [KB-2248](https://community.appian.com/security-42/kb-2248-how-to-configure-default-maintenance-windows-1236) · [KB-1568](https://community.appian.com/cloud-35/kb-1568-errors-when-deploying-application-to-appian-cloud-site-from-the-command-line-using-deployment-automation-manager-785) · [Appian Max — Appian DevOps Quick Start](https://community.appian.com/platform-30/appian-devops-quick-start-1256)

### ALM for Report and Dashboard objects

❌ **Don't deploy a report whose dataset filter or quick filter points to a user, group or document**
(nor a dashboard with a **process KPI**): inspection flags it as an **error** and blocks the
deployment, both direct and via manual export. To deploy them you must belong to the **Data
Fabric Report Creators** system group and **add the object to the application** first.
- Source: <https://docs.appian.com/suite/help/latest/deploy-to-production.html> · <https://docs.appian.com/suite/help/latest/report-and-dashboard-objects.html>

⚠️ **A report/dashboard edited by a business user in the target becomes protected: the deployment
does NOT overwrite it.** By default that version is authoritative. If your change governance requires
the source to win, force the overwrite per object in the ICF with
`report.<UUID>.forceOverrideProtection=true` / `dashboard.<UUID>.forceOverrideProtection=true`. These
objects cannot go in a post-deployment process.
- Source: <https://docs.appian.com/suite/help/latest/Managing_Import_Customization_Files.html> · <https://docs.appian.com/suite/help/latest/deploy-to-production.html>

### Objects with their own deployment rules

⚠️ **Some objects don't travel whole with the package; check them before promoting:**
- **AI agents** — the configuration moves, the **tools don't**: package the process models, rules,
  record types, documents, folders and MCP connected systems they use, and verify the initiator's
  permissions in the target (`12-ai-agents-and-skills.md` §9).
- **DocCenter models** — include the **`AIA deployment`** document; with manual deployment, run the
  deployment from DocCenter in the target. ⚠️ Unlike the general rule below (source version equal to or
  earlier than the target), DocCenter requires source and target on the **same** platform version
  (`12-ai-agents-and-skills.md` §10.3).
- **Translation sets** — strings deleted in the source are **not** deleted in the target, and a name that
  collides with a rule, constant, interface, integration or function makes the import fail
  (`02-interfaces-sail.md` §10.2).
- Source: [Deploy AI Agents Between Environments](https://docs.appian.com/suite/help/latest/deploy-ai-agents.html) · [Translation Set Object — Deployment](https://docs.appian.com/suite/help/latest/translation-set-object.html#deployment) · [Deployment Best Practices — Rules](https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html#rules)

### Deployment behavior rules

✅ **Trust that Appian matches objects between environments by UUID, not by name or Local ID.** If the
UUID exists in the target, it **updates**; if not, it **creates**. Same name with a different UUID =
two different objects.
- **Why:** this is why you **never invent or copy UUIDs between environments** — deployment matching
  depends on them. An invented UUID doesn't update anything: it creates a duplicate object.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

⚠️ **Import has no undo.** Once completed it cannot be rolled back; keep a backup and a stable
window.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

❌ **Don't edit the generated XML or the internal structure of the export ZIP.** It's not supported
and can break the deployment.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

❌ **Don't modify objects in the target environment while an import is in progress**, and don't
deploy onto an environment under maintenance.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

✅ **Import with a shared system administrator account, not a personal one.** A process model
configured to "run as its designer" fails if that account is deactivated.
- **Why:** decoupling deployment and execution from a specific person avoids outages when someone
  leaves the team.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

✅ **When deploying several packages together, align versions of shared objects** (you can't deploy
two versions of the same object) and use a **single ICF** per deployment.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>

✅ **Use a post-deployment process for logic that must run after a direct or external deployment**
(DB updates, refreshes). Auditable in the **Deploy** view.
- Source: <https://docs.appian.com/suite/help/latest/post-deployment-process.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

### Versioning

✅ **Lean on native per-object versioning: every save creates a version.** Compare versions to
review and debug; you can revert.
- **Why:** it's the safety net that makes an `update` reversible, unlike a delete, which isn't.
- Source: <https://docs.appian.com/suite/help/latest/Managing_Object_Versions.html> · <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>

⚠️ **Rollback strategy: per-object versioning and Compare & Deploy are NOT a transactional
rollback.** Reverting an object to its previous version doesn't undo the DB schema, the data, the
groups, the credentials, or the effects of processes already run; and import **has no undo**. Plan
the real reversal: **roll-forward** (a new deployment that fixes things), **N / N-1 compatibility**
between objects and schema so they can coexist during deployment, **compensating scripts** for DB
changes, and **backup/restore** — export the Production objects before promoting so you can restore
if the deployment fails.
- Source: <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html> · <https://docs.appian.com/suite/help/latest/Managing_Object_Versions.html>

✅ **Integrate continuously: frequent, incremental changes, not one big batch at the end.**
- **Why:** it reduces the risk of conflicting changes and eases collaboration between several
  designers.
- Source: <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>

---

## 4. Testing

Appian recognizes three types: **unit** (rules, logic), **user-interface**, and **performance**
testing; its DevOps pipeline adds **accessibility** and **verification** testing as stages. Testing is
continuous, not a final phase.
- Source: <https://docs.appian.com/suite/help/latest/testing-applications.html> · <https://docs.appian.com/suite/help/latest/devops-with-appian.html#the-appian-devops-pipeline>

### Expression rule test cases (unit)

✅ **Write test cases for every expression rule that's important or reused across applications.**
- **Why:** rules are the smallest pieces of the app; their test cases give confidence that a logic
  change doesn't break dependent functionality, and document the expected behavior for the next
  developer.
- Source: <https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html> · <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

✅ **Cover use cases, edge cases and nulls.** Write one test per possible outcome of the rule and
another for unusual inputs that could break it.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

✅ **Test only your logic, not Appian's.** Don't verify that `sum()` adds; do verify that your rule
handles types or nulls.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html> (General guidance)

✅ **Make each test as specific as possible.** Isolate one part of the rule per test; three outcomes =
three tests, not one that checks three things.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

❌ **Avoid the "test 1=1".** If the assertion is identical to the rule's definition, you learn
nothing. A surprisingly easy mistake to make.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

❌ **Don't write brittle tests that depend on external data or the current date/time.** A query
against a transactional table can fail because of a data change unrelated to the rule's logic.
- **Why:** a failure like that doesn't reflect a defect in the rule; it poisons the regression suite's
  signal.
- **Corollary:** for rules that query **transactional** data (different in every environment), don't
  assert values: a smoke case proves the query completes and returns the expected types (`typeof()`,
  doc 04 §8).
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

✅ **Consider TDD: write the test cases before the rule** and use them as the "done" criterion.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

### Interfaces

✅ **Test display and validation logic while building the interface, not at the end.** Use the live
view, ad hoc tests and test scenarios (named sets of rule inputs).
- Source: <https://docs.appian.com/suite/help/latest/interface_object.html> · <https://docs.appian.com/suite/help/latest/testing-applications.html>

✅ **Test every interface with real data AND with the empty/null path.** A newly added rule input
comes in as null; create one scenario with data and another with nulls.
- **Why:** the body of an `a!forEach` over an empty list never gets evaluated, so a broken screen can
  pass all its cases while its lists come in empty. Loading a minimal data set surfaces blockers that
  the empty path hides.
- Source: <https://docs.appian.com/suite/help/latest/interface_object.html> · <https://docs.appian.com/suite/help/latest/null-handling.html>

✅ **Handle nulls explicitly with `a!defaultValue()`, `a!isNullOrEmpty()`, `a!isNotNullOrEmpty()` and
the `applyWhen` parameter in filters.** You can't transform a null string, iterate a null list, or
show a link with a null address.
- **Why:** an unhandled null turns the app into "broken or unstable" in the user's eyes.
- Source: <https://docs.appian.com/suite/help/latest/null-handling.html>

### Regression and cadence

✅ **Run all of the app's rule test cases in bulk at the end of every sprint.** Smart Service
*Start Rule Tests (Applications)*.
- **Why:** a change to one rule can have implications elsewhere; testing just the change, in a
  less-loaded environment, gives fast feedback.
- Source: <https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html>

✅ **Regression-test ALL rules in the system after deploying to Test, before a major release.** Smart
Service *Start Rule Tests (All)*.
- **Why:** many rules are shared across apps; this surfaces impacted dependencies before Prod.
- Source: <https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html>

✅ **Run the package's test cases at least once right before deploying.** When inspecting the package
during a direct deployment, Appian reminds you of missing coverage and invites you to run the tests.
- **Why:** it's the best way to confirm the changes haven't degraded existing rules.
- Source: <https://docs.appian.com/suite/help/latest/testing-applications.html> · <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>

✅ **Watch and close coverage gaps with the Manage Test Cases dialog**, which lists rules without
tests and runs several rules' tests at once.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

✅ **Automate execution with a CI tool (e.g. Jenkins)** via the test smart services.
- Source: <https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html>

### Processes

✅ **Debug process models by starting processes in debug mode as you add nodes.** Don't wait until
the end.
- Source: <https://docs.appian.com/suite/help/latest/testing-applications.html>

### Testing practices from Appian Max

- ✅ Never test as a system administrator or a multi-role user; tests assert **outputs**, not just "no error"; wrap decision logic in expression rules so it can have test cases; unit-test subprocesses before their parents.
- ✅ **UAT** by real users from outside the project, covering every persona, starting as soon as an end-to-end scenario is Done; keep UAT data separate by naming convention or a dedicated environment.
- ✅ **Exploratory testing** with time-boxed charters: zero, one and many rows against the batch size; delete the last row of the last page and check paging; record-level security across role combinations.
- ✅ **System integration testing** from both sides — Appian calling out, and external systems calling Appian's Web APIs — including invalid values.
- ✅ A **hardening sprint** (~2 weeks) before go-live: no new features, a Test-like environment (never Dev), production-like data volume, load tests of high-volume Web APIs, and a fresh look at the Security Summary.
- Source: [Appian Max — User Story Testing Checklist](https://community.appian.com/delivery-28/user-story-testing-checklist-1252) · [Appian Max — Functional Testing](https://community.appian.com/delivery-28/functional-testing-1331) · [Appian Max — User Acceptance Testing Overview](https://community.appian.com/delivery-28/user-acceptance-testing-overview-1332) · [Appian Max — Exploratory Testing](https://community.appian.com/delivery-28/exploratory-testing-1334) · [Appian Max — System Integration Testing](https://community.appian.com/delivery-28/system-integration-testing-1336) · [Appian Max — How to Undergo a Hardening Sprint](https://community.appian.com/delivery-28/how-to-undergo-a-hardening-sprint-1333)

---

## 5. Development approach and methodology

✅ **Follow an agile methodology (Initiate → Build → Release → Optimize).** Appian explicitly
recommends Agile and its Appian Delivery Methodology.
- Source: <https://docs.appian.com/suite/help/latest/introduction-to-application-building.html> · <https://community.appian.com/delivery-28/the-appian-delivery-methodology-1189>

✅ **Design data-driven: model with record types and data fabric as the foundation.** Every record
type represents a business concept (Products, Orders, Customers…); relate several for a unified view.
- **Why:** it unifies, secures and optimizes the data without migrations or custom APIs, and speeds
  up development.
- Source: <https://docs.appian.com/suite/help/latest/Record_Type_Object.html> · <https://docs.appian.com/suite/help/latest/data-fabric.html>

✅ **Use synced record types whenever you can.** They unlock automatic performance optimization,
relationships, custom record fields and row-level security.
- Source: <https://docs.appian.com/suite/help/latest/build-best-data-fabric.html>

✅ **Reuse objects instead of duplicating logic.** Reference an interface from a record, a common rule
from several interfaces.
- **Why:** builds faster and is easier to maintain; fewer places to touch when something changes.
- **Trade-off:** reuse increases the dependents blast radius — hence the impact analysis (§2).
- Source: <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>

✅ **Do design reviews before building.** Wireframing/prototyping with SAIL, technical design
documentation, and **fix naming and structure standards as part of the design**, not after the fact.
- **Why:** Appian places "Determining coding standards" (naming, structure, documentation) within
  the design phase, before the build.
- Source: <https://docs.appian.com/suite/help/latest/introduction-to-application-building.html>

✅ **Prefer documented functions.** An unsupported/undocumented function can change or break when
Appian is upgraded (design guidance "Unsupported function detected").
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html>

### Delivery practices from Appian Max

- ✅ **Initiate (1–2 weeks) / Sprint 0 (2–3 weeks), depending on the guide:** backlog with acceptance criteria, release plan for the next 3–6 iterations, Sprint 1 plan, charter; proofs of concept for uncertain features. Capture **non-functional requirements up front**: total and peak concurrent users, response-time thresholds, yearly record counts per key entity, security, accessibility, sizing.
- ✅ **Build:** 2-week iterations in which each story goes from analysis to Done — no separate design, build and test sprints; aim for the first production release around 8 weeks; plan 1–2 weeks of hypercare after go-live.
- ✅ **Definition of Ready:** representative test data received, web service contracts with working sample request/response, dependencies resolved. **Definition of Done:** peer reviewed, tested by someone else, rule tests passing, objects in the package, database scripts attached.
- ✅ **Acceptance criteria** in Given-When-Then, one When each, with negative, edge-case and performance criteria; many criteria means the story should be split.
- ✅ **Estimation:** expect −10 %/+25 %; independent estimates by 3–5 Appian experts, then a consensus session; process complexity bands 5–10 / 10–20 / > 20 steps. Avoid dynamically generated forms and pixel-perfect copies of legacy screens; Appian isn't a BI replacement.
- ✅ Flag stories that need an architect before building (list in doc 00); reserve ~10 % of each sprint for maintenance and Health Check findings.
- ✅ **Support model:** tier 1 business (power users), tier 2 application (developers; monitoring, monthly Health Check), tier 3 platform (administrators).
- Source: [Appian Max — The Appian Delivery Methodology](https://community.appian.com/delivery-28/the-appian-delivery-methodology-1189) · [Appian Max — Initiating an Appian Project (Sprint 0)](https://community.appian.com/delivery-28/initiating-an-appian-project-sprint-0-1288) · [Appian Max — Recommended Delivery Methodology](https://community.appian.com/delivery-28/recommended-delivery-methodology-1308) · [Appian Max — Ready-to-Done](https://community.appian.com/delivery-28/ready-to-done-streamline-user-stories-in-appian-1318) · [Appian Max — Writing Effective Acceptance Criteria](https://community.appian.com/delivery-28/writing-effective-acceptance-criteria-1266) · [Appian Max — How to Estimate your Appian Projects](https://community.appian.com/delivery-28/how-to-estimate-your-appian-projects-1229) · [Appian Max — Platform Health Management](https://community.appian.com/vision-26/platform-health-management-1180) · [Appian Max — Support your Appian Application](https://community.appian.com/vision-26/support-your-appian-application-1182)

---

## 6. Documentation and maintainability of objects

✅ **Write clear descriptions on record types (and key objects).** 1–2 sentences about the purpose,
in business language, including relevant relationships or constraints; understandable to someone
outside the app. You can generate them with AI Copilot.
- **Why:** they feed Process HQ and AI, and are the next developer's onboarding.
- Source: <https://docs.appian.com/suite/help/latest/build-best-data-fabric.html>

✅ **Use test cases as living documentation.** They describe the expected behavior and outcomes of a
rule for whoever modifies it in the future.
- Source: <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>

✅ **Pass arguments by keyword syntax to rules and data constructors.** It protects the expression
against compatibility issues if inputs get added, reordered, removed or renamed. Where the platform
needs position instead (process events, process reports), see doc 04 §2.
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html>

❌ **Don't leave unused local variables, rule inputs or process variables.** They complicate
understanding, debugging and maintenance (and can trigger unnecessary queries). Design guidance flags
them.
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html>

✅ **Name user tasks with a dynamic display name** (an ID or an entered value) to distinguish
instances in Tempo and in task reports.
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html>

✅ **Keep process models small:** under 50 nodes and 100 process variables; split into subprocesses
if they grow past that.
- **Why:** going beyond those thresholds complicates maintenance and consumes more memory (design
  guidance "Too many nodes" / "Too many process variables").
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html>

---

## 7. Continuous quality control (Health Check, design guidance, technical debt)

✅ **Attend to Appian Design Guidance in real time as you develop.** Warnings (triangle) and
recommendations (light bulb) appear on the object and in the Monitor's Health Dashboard.
- **Why:** applying these patterns improves performance and reduces runtime and maintainability
  problems; it's technical debt tackled at the source, when it's cheapest.
- Source: <https://docs.appian.com/suite/help/latest/appian-recommendations.html> · <https://docs.appian.com/suite/help/latest/devops-with-appian.html>

✅ **Schedule Health Check in every environment and review the report regularly — at least once per
sprint.** It covers four areas: **Design, User Experience, Infrastructure, Configuration**, with
high/medium/low risks and mitigation links, plus historical trends.
- **Why:** in build it catches design flaws early and cheaply; in test, functional and performance
  risks; in Prod, it monitors capacity and trends.
- Source: <https://docs.appian.com/suite/help/latest/health-check.html> · <https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html>

⚠️ **Run Health Check outside business hours in active environments.** It increases system load and
can degrade user performance (mind the time zones).
- Source: <https://docs.appian.com/suite/help/latest/health-check.html>

✅ **Also monitor at runtime: application and system performance, and logs.** Check that the app is
functional, efficient, gives a good experience and delivers business value; use logs for non-process
errors (record views, task forms) and usage analysis.
- Source: <https://docs.appian.com/suite/help/latest/devops-with-appian.html>

✅ **Automate Health Check in CI** with a Web API that calls `a!latestHealthCheck()` if you integrate
it into Jenkins.
- Source: <https://docs.appian.com/suite/help/latest/health-check.html>

✅ **Health Check cadence that sticks:** at least monthly in Production with an action plan for High and Medium findings, at the end of each sprint, and after testing before a deployment; each application owner reviews its own findings. The organization's Health Check account password expires every 365 days — a silent reason for missing reports (doc 13 §0).
- Source: [Appian Max — Platform Health Management](https://community.appian.com/vision-26/platform-health-management-1180) · [Appian Max — Application Monitoring Checklist](https://community.appian.com/delivery-28/application-monitoring-checklist-1306) · [KB-2277](https://community.appian.com/how-to-36/kb-2277-how-to-generate-or-reset-health-check-credentials-1351)

---

## Sources

- **Standard Object Names** — <https://docs.appian.com/suite/help/latest/Standard_Object_Names.html>
- **Creating Applications** — <https://docs.appian.com/suite/help/latest/creating-applications.html>
- **Design Objects** — <https://docs.appian.com/suite/help/latest/design-objects.html>
- **Introduction to Application Building** — <https://docs.appian.com/suite/help/latest/introduction-to-application-building.html>
- **Application Deployment Guidelines** — <https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html>
- **Deploy to Target Environments** — <https://docs.appian.com/suite/help/latest/Deploy_to_Target_Environments.html>
- **Deployment REST API** — <https://docs.appian.com/suite/help/latest/Deployment_Rest_API.html>
- **Manage Import Customization Files (ICF)** — <https://docs.appian.com/suite/help/latest/Managing_Import_Customization_Files.html>
- **Deploy to Production (Process HQ / reports & dashboards)** — <https://docs.appian.com/suite/help/latest/deploy-to-production.html>
- **Deploy Report and Dashboard Objects** — <https://docs.appian.com/suite/help/latest/report-and-dashboard-objects.html>
- **DevOps Infrastructure (Admin Console)** — <https://docs.appian.com/suite/help/latest/admin-infrastructure.html>
- **Admin Console — Certificates (mTLS)** — <https://docs.appian.com/suite/help/latest/admin-certificates.html>
- **Data Source Connected Systems** — <https://docs.appian.com/suite/help/latest/data-source-connected-systems.html>
- **Appian Administration Console** — <https://docs.appian.com/suite/help/latest/Appian_Administration_Console.html>
- **Plug-in Disclaimer (test before production)** — <https://docs.appian.com/suite/help/latest/plugindisclaimer.html>
- **Deployment Automation (Appian Max / Community)** — <https://community.appian.com/platform-30/deployment-automation-1329>
- **Prepare Deployment Packages** — <https://docs.appian.com/suite/help/latest/prepare-deployment-packages.html>
- **Prepare the Deployment — Comparing across environments** — <https://docs.appian.com/suite/help/latest/prepare-deployment.html#comparing-across-environments>
- **Post-Deployment Process** — <https://docs.appian.com/suite/help/latest/post-deployment-process.html>
- **Continuous Integration in Appian** — <https://docs.appian.com/suite/help/latest/continuous-improvements-to-your-application.html>
- **DevOps in Appian** — <https://docs.appian.com/suite/help/latest/devops-with-appian.html>
- **Trace Relationships for Impact Analysis** — <https://docs.appian.com/suite/help/latest/Trace_Relationships_for_Impact_Analysis.html>
- **Managing Object Versions** — <https://docs.appian.com/suite/help/latest/Managing_Object_Versions.html>
- **Testing Applications** — <https://docs.appian.com/suite/help/latest/testing-applications.html>
- **Expression Rule Testing** — <https://docs.appian.com/suite/help/latest/Expression_Rule_Testing.html>
- **Automated Testing for Expression Rules** — <https://docs.appian.com/suite/help/latest/Automated_Testing_for_Expression_Rules.html>
- **Interface Object (Testing interfaces)** — <https://docs.appian.com/suite/help/latest/interface_object.html>
- **How to Handle Null Values** — <https://docs.appian.com/suite/help/latest/null-handling.html>
- **Appian Design Guidance** — <https://docs.appian.com/suite/help/latest/appian-recommendations.html>
- **Health Check** — <https://docs.appian.com/suite/help/latest/health-check.html>
- **Understanding the Health Check Report** — <https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html>
- **Build Your Best Data Fabric** — <https://docs.appian.com/suite/help/latest/build-best-data-fabric.html>
- **About Record Types** — <https://docs.appian.com/suite/help/latest/Record_Type_Object.html>
- **Data Fabric** — <https://docs.appian.com/suite/help/latest/data-fabric.html>
- **Use Data Fabric in Existing Apps** — <https://docs.appian.com/suite/help/latest/use-synced-record-types-in-existing-apps.html>
- **The Appian Delivery Methodology (Community)** — <https://community.appian.com/delivery-28/the-appian-delivery-methodology-1189>
- **The Appian Playbook — Appian Testing Essentials (Community)** — <https://community.appian.com/architecture-29/appian-testing-essentials-1365>
