# Best practices — Interfaces and SAIL

> Official Appian doctrine for designing interfaces with SAIL: structure, data querying, responsive layouts, forms, grids, charts, rich text, accessibility, performance, multilingual text and offline forms. Every rule is anchored to official Appian documentation (`docs.appian.com/suite/help/latest/…`). The links use the `latest` alias, which always redirects to the most recently published release.

Markers: ✅ do · ❌ avoid · ⚠️ trap · ⓥ version-dependent · ⓣ tier-dependent. Each block closes with its source.

**Contents:** 1. Interface structure · 2. Querying data in interfaces
· 3. Responsive layouts and mobile design · 4. Forms · 5. Grids · 5A. Charts · 6. Rich text, icons and styles
· 7. UX: consistency, loading states and empty states · 8. Performance anti-patterns (actionable summary)
· 9. Accessibility · 10. Multilingual interfaces: translation sets
· 11. Offline forms (Appian Mobile; ⓥ Appian for Windows from 26.6) · Sources

---

## 1. Interface structure

### 1.1 Expensive calculations and queries go in `a!localVariables`, not in component parameters
- ✅ Put every function or rule that takes time to evaluate (a query, an aggregation) inside a local variable with `a!localVariables()`.
- ❌ Don't put it directly in a component parameter (`value`, `data`, etc.).
- **Why:** every time an evaluation fires (the user types, clicks a button…) **all** components are re-evaluated, so whatever lives in a parameter gets recalculated on every interaction. A local variable, by default, is only re-evaluated when the interface loads, when it is updated in a `saveInto`, or when another local variable it references changes.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#local-variable-best-practices

### 1.2 Never put a component inside a local variable
- ❌ Don't use a component (`a!textField(...)`, `a!cardLayout(...)`) as the **value** of a local variable.
- ✅ To reuse a component, define it in a **new interface** (an interface rule) and invoke it.
- **Why:** it doesn't throw a visible error, but produces unexpected or inconsistent behavior.

Source: https://docs.appian.com/suite/help/latest/Local_Variables.html#components-in-local-variables

### 1.3 Split into reusable interfaces and custom components
- ✅ Extract repeated fragments into reusable interfaces; a change is reflected instantly in every object that calls them.
- ✅ When wrapping an input component in a generic rule (e.g. a `dollarField`), use a `value` rule input and a `saveInto` one; the one that maps to `saveInto` must be of type **array of Save**, so `a!save()` can be used.
- **Why:** it reduces redundant expressions, eases maintenance, and enforces a consistent design standard and UX. Naming the rule inputs `value` and `saveInto` is the convention that helps others configure the component correctly.

Source: https://docs.appian.com/suite/help/latest/using_interfaces_in_appian.html#reusability

### 1.4 Give each local variable a unique name
- ✅ Name every local variable uniquely, including those inside loop functions (`a!forEach()`).
- **Why:** renaming from the Local Variables grid in design mode can, through a name collision, affect variables defined inside loops, causing unintended changes.

Source: https://docs.appian.com/suite/help/latest/interface_object.html#local-variables

### 1.5 In children, query at the top and pass through a rule input
- ✅ Query the data in a local variable in the **parent interface** and pass it to the child through a rule input (`ri!`).
- ❌ Don't query data inside a child interface or a rule called from the parent.
- **Why:** in offline synchronization only the parent's data is downloaded; querying in the child causes an error in Appian Mobile. Also, typing the rule inputs correctly makes the component's data contract explicit. The rest of the offline rules are in §11.

Source: https://docs.appian.com/suite/help/latest/offline-mobile-design-best-practices.html#query-data-for-child-interfaces-or-rules-at-the-top-of-the-parent-interface

---

## 2. Querying data in interfaces

> **Where the depth lives.** Query mechanics —fields, paging, filters, aggregations, relationships and
> their ceilings— are specified once for this skill in **`05-performance.md` § 2**, and in full by the
> official Appian skill in `references/query-record-type-patterns.md`. This section keeps only what is
> specific to querying *from an interface*.

### 2.1 Choose the query function for the case
- ✅ List of records from a **record type** → `a!queryRecordType()`.
- ✅ A **single** record (and its related ones) for summary views or related actions → `a!queryRecordByIdentifier()`.
- ✅ Grid or chart fed by a record type (including aggregations) → `a!recordData()` in the component's `data` parameter.
- ✅ List or aggregation from a **data store entity** (not a record type) → `a!queryEntity()` with `a!query()`.
- **Why:** if the data lives in a record type, `a!queryRecordType()` / records-powered components are the preferred route; `a!queryEntity()` is left for entities without a record type.

Source: https://docs.appian.com/suite/help/latest/about-queries.html#how-to-query-data · https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html#usage-considerations

### 2.2 Fields, paging and the N+1: the rules live in `05-performance.md` § 2

Specify the exact `fields`, page with `a!pagingInfo()`, never run an unbounded query, and never query
inside a loop. Those four rules, their ceilings and their traps —the empty-`fields` trap on
`a!queryRecordByIdentifier()` among them— are stated once in **`05-performance.md` § 2**. They are not
repeated here, because the same rule written twice drifts into two versions of itself.

What is specific to an interface, and only lives here:

- **An interface re-evaluates.** A query inside an interface runs again on every interaction that
  touches its variable, so an expensive query costs once in a rule and costs *per click* here. This is
  why § 1.1 puts queries in `a!localVariables` and § 8.3 limits interactions on data-heavy screens.
- **Record type queries time out after 65 seconds** (`a!queryRecordType`, `a!recordData`, records-powered
  components). That is a ceiling, not a budget: on a screen the query sits on the user's click path, so
  anything over ~500 ms belongs in async loading (§2.3). On a timeout, reduce the batch, the fields, or
  tighten the filters.
  Source: https://docs.appian.com/suite/help/latest/fnc_system_queryrecordtype.html#query-timeout

### 2.3 For slow data, load asynchronously
- ✅ Use `a!asyncVariable()`, or the `loadDataAsync` parameter on read-only grids, charts and KPIs fed by records, when the data is slow to load.
- **Why:** it's one of the most effective ways to improve perceived performance: the user interacts with the rest of the screen while the slow data loads behind a placeholder (skeleton). Note: in offline mobile and portals, async data loads together with everything else, not in the background.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#use-asynchronous-loading-for-slow-data

---

## 3. Responsive layouts and mobile design

### 3.1 `a!isPageWidth()` and `stackWhen` are the responsiveness tools
- ✅ Use `a!isPageWidth()` (with `if`) to change sizes, spacing or layout based on page width, and the `stackWhen` parameter of `a!columnsLayout()` / `a!sideBySideLayout()` to control when they stack.
- ❌ Don't use `a!isNativeMobile()` for responsive layout decisions.
- **Why:** `a!isNativeMobile()` only detects whether the user is in the Appian Mobile app or a browser, not screen size; reserve it for app-specific functionality. Breakpoints: `PHONE` ≤480px, `TABLET_PORTRAIT` 481-768, `TABLET_LANDSCAPE` 769-1024, `DESKTOP_NARROW` 1025-1280, `DESKTOP` 1281-1680, `DESKTOP_WIDE` ≥1681.

Source: https://docs.appian.com/suite/help/latest/responsive_design.html

### 3.2 Don't fix the width of every column
- ❌ Don't give a fixed width to every column of an `a!columnsLayout()`.
- ✅ Use relative widths, or combine empty `AUTO` columns on the sides to center the content; check that any fixed width fits every target screen size.
- **Why:** not every user has the same screen; fixed widths don't fit all of them. Mind the negative space: more content isn't better — avoid filling the whole screen if it doesn't add value.

Source: https://docs.appian.com/suite/help/latest/sail/ux-columns-layout.html#style-guidelines

### 3.3 Design "small screen first" and touch-friendly
- ✅ Stack columns on narrow screens, limit horizontal scrolling and ensure comfortable touch targets.
- **Why:** on mobile, columns stack by default; the interface must stay usable at the smallest width it supports.

Source: https://docs.appian.com/suite/help/latest/responsive_design.html

### 3.4 Content from outside Appian: HTTPS and framing
- ⚠️ The iOS app enforces App Transport Security: images and resources over HTTP (or TLS < 1.2) don't load, even on Appian Cloud.
- ⚠️ A Web Content component shows nothing if the source sends `X-Frame-Options`, isn't publicly reachable or isn't HTTPS, and it isn't supported on Safari.

Source: [KB-1272](https://community.appian.com/mobile-40/kb-1272-apple-enforcing-app-transport-security-ats-starting-1-january-2017-557) · [KB-1583](https://community.appian.com/web-browser-43/kb-1583-web-content-component-not-rendering-content-795)

---

## 4. Forms

### 4.1 Requiredness with `required`; cross-field validation at the form/section level
- ✅ Mark required fields with `required: true`.
- ✅ When the rule isn't about a single field (e.g. "phone **or** email"), use the `validations` parameter of `a!formLayout()` (or `a!sectionLayout()`) with `a!validationMessage()`.
- **Why:** setting `required` on two fields that are alternatives is incorrect; form-level validation expresses the actual rule. With `validateAfter: "SUBMIT"` the message only appears on submit.
- ⚠️ `a!validationMessage()` works only in form layouts, section layouts, wizard steps and grids, and is **not** compatible with portals or offline interfaces — there, use plain text in `validations`.

Source: https://docs.appian.com/suite/help/latest/recipe-showing-validation-errors-that-arent-specific-to-one-component.html · https://docs.appian.com/suite/help/latest/sail/ux-form-layout.html#behavior-configurations · https://docs.appian.com/suite/help/latest/Validation_Message.html

### 4.2 Conditional requiredness with `validationGroup`
- ✅ To make fields required only if the user clicks a certain button, assign the same `validationGroup` to those fields and to the button; use `requiredMessage` for a custom message.
- **Why:** it defers validation (required and `validations`) until the group is triggered. The `validationGroup` value **cannot contain spaces** (use underscore: `"Future_Hire"`).

Source: https://docs.appian.com/suite/help/latest/recipe-configure-buttons-with-conditional-requiredness.html

### 4.3 `saveInto` with `a!save()` to transform the saved value
- ✅ Use `a!save(target, value)` in `saveInto` when you need to transform the input before saving it (e.g. `todecimal(save!value)`).
- **Why:** it lets the consuming designer always work with the correct type; `save!value` is the value the user entered.
- ⚠️ Inside `a!forEach`, save into `fv!item`, not into `local!list[fv!index]`, or values land in the wrong rows ([KB-1398](https://community.appian.com/application-design-33/kb-1398-a-foreach-does-not-save-inputs-in-the-order-they-are-entered-662)).

Source: https://docs.appian.com/suite/help/latest/using_interfaces_in_appian.html#reusability

### 4.4 `showWhen` to show/hide at no cost
- ✅ Use `showWhen: false` to conditionally hide layouts or components.
- **Why:** when `showWhen` is false the component is hidden **and not evaluated**, saving work.

Source: https://docs.appian.com/suite/help/latest/Columns_Layout.html#main_content

### 4.5 In scrolling dialogs, fix the title bar and buttons
- ✅ Enable "Fix title bar when scrolling" and "Fix buttons to bottom" on long forms, and consider "Automatically focus on first input" to speed up typing.

Source: https://docs.appian.com/suite/help/latest/sail/ux-form-layout.html#behavior-configurations

### 4.6 Choose the form layout based on the flow
- ✅ Single-screen form → `a!formLayout()`; **sequential multi-step** form → `a!wizardLayout()`, which provides a progress bar (milestone), step navigation, a fixed footer and per-step validation.
- ✅ Prefer `a!wizardLayout()` over building a "wizard" by hand with sections toggled by `showWhen`: the native wizard gives you, for free, the progress, navigation and per-step validation that are expensive and fragile to reproduce by hand.
- ✅ With **more than 5 steps**, use a **vertical** step style; for 1–2 steps use the Minimal style with step headings shown.
- ✅ Group related fields with `a!sectionLayout()`; use `a!tabLayout()` when the content consists of **parallel** views, not sequential steps.
- ❌ For a wizard opened from a record action, don't choose **"Auto" dialog height** (a setting of the record action's dialog, not of the wizard): the height jumps between steps. Forms and wizards inside dialogs use "Full" `contentsWidth`.
- **Why:** each layout is built for a different way of moving through the form; picking the right one saves code and gives a consistent UX.

Source: https://docs.appian.com/suite/help/latest/sail/ux-wizard-layout.html#style-guidelines · https://docs.appian.com/suite/help/latest/sail/forms.html · https://docs.appian.com/suite/help/latest/sail/ux-record-actions.html#action-behavior

### 4.7 Progressive disclosure: in sequential flows, disable — don't hide
- ✅ In a **sequential** flow (one step enables the next), show fields that aren't yet available as **disabled** (`disabled: true`), not hidden.
- ✅ Reserve `showWhen` for **conditional** visibility (the field applies or not depending on another answer), not for sequential progression.
- ❌ Don't use `showWhen` to hide steps the user can't fill in yet: it loses the preview of what's coming and how much is left.
- **Why:** seeing disabled fields communicates the structure of the flow; `showWhen` is for conditions, not for order.

Source: https://docs.appian.com/suite/help/latest/sail/ux-progressive-disclosure.html

### 4.8 Pick the input by the number of options
- ✅ Radio buttons / checkboxes for **fewer than 5** choices (preselect one option by default, ideally the most common); a dropdown above that; a **picker** when the list is too long to browse.
- ✅ Dropdown search runs in the browser (cost at load); picker search runs on the server (cost while typing): small sets → dropdown.
- ✅ **Cascading dropdowns:** the child's choices depend on the parent's value, the parent's `saveInto` resets the child (`a!save(child, null)`), and the child stays disabled until the parent has a value.

Source: https://docs.appian.com/suite/help/latest/sail/ux-inputs.html · https://docs.appian.com/suite/help/latest/Dropdown_Component.html#usage-considerations · https://docs.appian.com/suite/help/latest/recipe-configure-cascading-dropdowns.html

### 4.9 Buttons and destructive actions
- ✅ **At most one Solid button per interface** — the primary action. Default style is Outline.
- ✅ An action that **deletes persisted data** uses the **Ghost** style with **Negative** color (not Solid), and adjacent buttons use Secondary color; reserve Negative for real data loss.
- ✅ When an action is destructive or hard to undo, add `confirmHeader` / `confirmMessage` (the `saveInto` runs only on confirm) — the pattern the docs show with Ghost + Negative.

Source: https://docs.appian.com/suite/help/latest/sail/ux-buttons.html · https://docs.appian.com/suite/help/latest/Button_Component.html#usage-considerations

### 4.10 File upload: validate in the form, restrict in the Admin Console
- ✅ Validate with `fv!files` (`size`, `extension`, `name`) in the component's `validations`.
- ✅ Limits: **1 GB** per file, **10 MB** in portals (Support can raise it).
- ✅ In **Admin Console → File Upload**, prefer an **allow list** of extensions plus **file type verification** (block files whose extension doesn't match their content); on Appian Cloud, real-time virus scanning covers files under 25 MB. These settings apply only to the File Upload component, and extension rules don't apply to system administrators.
- ⚠️ A task holding uploaded files **can't be saved as a draft** (except offline tasks in Appian Mobile), and `target` must be a folder constant or a document record type — never the document variable itself, or the file ends in a folder nobody can see ([KB-1480](https://community.appian.com/application-design-33/kb-1480-unable-to-save-changes-on-a-sail-form-if-an-file-upload-component-is-present-with-uploaded-files-719), [KB-1826](https://community.appian.com/application-design-33/kb-1826-documents-cannot-be-downloaded-from-appian-designer-943)).

Source: https://docs.appian.com/suite/help/latest/File_Upload_Component.html#uploaded-file-size-limit · https://docs.appian.com/suite/help/latest/admin-file-upload.html

### 4.11 Record actions: where they open and what refreshes afterwards
- ✅ `"DIALOG"` (default) for quick edits and data entry — the design system's usual choice, with a form layout inside; `"NEW_TAB"` for complex forms or when users need other data open; `"SAME_TAB"` for simple navigation.
- ⚠️ After a dialog action only the launching component refreshes: wrap other data in `a!refreshVariable(refreshAfter: "RECORD_ACTION")` (grids and charts have their own `refreshAfter`). It fires only for actions opened in a dialog.

Source: https://docs.appian.com/suite/help/latest/Record_Action_Component.html#usage-considerations · https://docs.appian.com/suite/help/latest/refresh-behavior-interfaces.html#troubleshooting-refresh-behavior

---

## 5. Grids

### 5.1 Read-only vs. editable: choose by use case
- ✅ Tabular read-only data → read-only grid (`a!gridField()`), which supports search, filter, selection, sort and **pagination**.
- ✅ Fast inline editing of a few records → editable grid (`a!gridLayout()`).
- ❌ Don't use an editable grid for large volumes: **it doesn't support pagination**.
- **Why:** to edit large datasets, use a read-only grid with a per-row link, or a record action that edits each record.

Source: https://docs.appian.com/suite/help/latest/Editable_Grid_Component.html#using-the-editable-grid-component

### 5.2 Performance of large editable grids
- ❌ Don't put too many cells in an editable grid.
- ✅ Reduce the number of components; if you use `a!queryEntity()` as the source, set `fetchTotalCount: true` so `totalCount` is valid (otherwise it can come back as -1).
- **Why:** performance depends on the number of components in the interface; many cells make it feel slow.

Source: https://docs.appian.com/suite/help/latest/Editable_Grid_Component.html#using-the-editable-grid-component

### 5.3 Use the record type as the grid's source
- ✅ Feed the grid from a record type to take advantage of the search field and user filters already defined on the object; apply a logical order that shows what matters most at the top.
- ❌ Don't show long blocks of text in a grid, and don't format cells in the same column differently.
- **Why:** grids exist to scan and decide; consistent per-column formatting maximizes readability.

Source: https://docs.appian.com/suite/help/latest/sail/ux-grids.html

### 5.4 Actions in grids: one per cell, or a toolbar above
- ❌ Don't put several related actions inside a single cell.
- ✅ Use the Record Action component in a column (in "Icon Only" style), or show the actions in "Toolbar" style above the grid when it's backed by a record type.

Source: https://docs.appian.com/suite/help/latest/sail/ux-grids.html

### 5.5 Every grid needs a row header (accessibility)
- ✅ Configure a row header on every grid; the first column with text is usually the right choice.
- **Why:** it's an accessibility requirement so screen readers can associate each row.

Source: https://docs.appian.com/suite/help/latest/Editable_Grid_Component.html#grid-height-and-headers

### 5.6 Page size, total count and export
- ✅ **Batch size:** 5–10 rows when the grid shares the page with other components, 50 when it's alone, 25 if unsure the filters will get users to their rows.
- ✅ ⓥ Since 26.3 the read-only grid on a record type uses `pagingControls: "STANDARD"` by default, which **skips the total-count query**; use `"ROW_COUNT"` (total + first/last page) only for small datasets.
- ⚠️ **Export to Excel:** at most **50 columns** and **100,000 rows** (database or web service source) or **10,000** (process-backed); the button is disabled above the limit, so give users filters that bring the list under it. On Appian Cloud each export must also finish within **5 minutes** (load balancer), so a list under the row limit can still fail — filter or batch ([KB-2293](https://community.appian.com/cloud-35/kb-2293-exporting-a-record-to-excel-fails-due-to-a-network-error-1352)).
- ✅ Sort on something unique last: records-powered grids add a deterministic sort for you; `a!queryEntity` and dictionary data need the primary key as a secondary sort, or rows repeat across pages ([KB-1519](https://community.appian.com/application-design-33/kb-1519-grid-data-duplicated-across-multiple-pages-in-a-grid-when-sorting-on-a-non-unique-column-748)).

Source: https://docs.appian.com/suite/help/latest/sail/ux-grids.html#batch-size · https://docs.appian.com/suite/help/latest/Paging_Grid_Component.html#configuring-grid-paging · https://docs.appian.com/suite/help/latest/Optimizing_Record_Lists_for_Export_to_Excel.html

---

## 5A. Charts

### 5A.1 Choose the chart type by the story the data tells
- ✅ **Parts of a whole** → pie (a single category), stacked bar/column (several categories), stacked area (parts of a whole over time).
- ✅ **Distribution** → column (positive and negative values), bar (many categories), scatter (comparing two measures).
- ✅ **Trend over time** → column or line (few intervals), line or area (many intervals).
- ✅ **Comparing categories** → column, line or area (small datasets), line (large datasets).
- ❌ Don't force the data into your preferred chart type: the type is dictated by the data's story, not by taste.
- **Why:** each type is optimized for a different reading; choosing the wrong one hides the pattern you meant to show. A line chart with more than 5 lines is unreadable (use column instead); an area chart stops making sense with more than 3 series.

Source: https://docs.appian.com/suite/help/latest/sail/ux-charts.html

### 5A.2 Minimize series, categories and colors; short labels
- ✅ Design the chart with the minimum number of dimensions and data points needed; use short labels (long ones shrink the plot area and some get hidden).
- ❌ Don't use more than 5 colors in a chart, and don't leave series/category labels undefined when hiding the axes; group small-value categories into an "Other" bucket.
- ⚠️ A pie with many slices, especially thin ones, hides labels: if you can't avoid it, **enable tooltips** so values show on hover.
- **Why:** simple charts are understood faster and load quicker; include a legend only when there are several series.

Source: https://docs.appian.com/suite/help/latest/sail/ux-charts.html · https://docs.appian.com/suite/help/latest/Tempo_Report_Design.html#usability

### 5A.3 Charts with many data points → single-column layout
- ✅ A chart with **more than 7 data points** looks better in a single-column layout; reserve the two-column layout for small charts being compared side by side.
- **Why:** line and column charts with many data points force horizontal scrolling on the user; giving them the full width avoids that. Keep the same layout (one or two columns) across every section of the dashboard for a balanced result.

Source: https://docs.appian.com/suite/help/latest/Tempo_Report_Design.html#usability

### 5A.4 Records-powered: 5,000-row cap and a 65-second timeout
- ✅ Feed charts and aggregations from the record type with `a!recordData()`; for totals and counts use aggregation (`a!aggregationFields()`), not raw rows.
- ❌ Don't try to render all 5,000 rows: records-powered components show **at most 5,000 rows**, and displaying all of them degrades performance.
- ⚠️ Queries against record types (synced or not) **time out after 65 seconds**, just like grids: if you get a timeout, reduce the batch, the fields, or tighten the filters.
- **Why:** a chart is meant for reading a pattern at a glance; thousands of points are neither readable nor performant.

Source: https://docs.appian.com/suite/help/latest/Column_Chart_Component.html#usage-considerations

### 5A.5 Asynchronous loading and background matched to the card
- ✅ Set `loadDataAsync: true` on records-powered charts that are slow to load: the interface displays without waiting for the chart, which shows a placeholder while it loads in the background (see 2.3).
- ✅ When placing a chart inside a colored card, its background takes on the card's color; text and lines adjust automatically over dark backgrounds.
- ⚠️ In offline mobile and portals, async data does **not** load in the background: it arrives together with the rest of the interface.

Source: https://docs.appian.com/suite/help/latest/Column_Chart_Component.html#usage-considerations

> Chart accessibility (a requirement, not optional): every chart needs an equivalent text/grid representation — see 9.5.

---

## 6. Rich text, icons and styles

### 6.1 Only the styles rich text supports exist (there is no HTML)
- ✅ Format text with `a!richTextItem()` / `a!richTextIcon()` using the supported styles: bold, italic, underline, strikethrough, color, safe links, icons and web images.
- ❌ Don't try to inject HTML or arbitrary styles: SAIL doesn't support them; only each component's enumerated parameters and values exist.
- **Why:** the rich text editor only applies that set of styles; any other formatting must be achieved through the component's parameters (`style`, `size`, `color`).

Source: https://docs.appian.com/suite/help/latest/Rich_Text_Component.html#usage-considerations · https://docs.appian.com/suite/help/latest/Styled_Text_Component.html#main_content

### 6.2 Use valid icons and valid colors
- ✅ The `icon` parameter must be a key from the official "Available Icons" list; `color` accepts hex or the enumerated values `STANDARD`, `ACCENT`, `POSITIVE`, `NEGATIVE`, `SECONDARY` (and `WARN` in recent releases); `size` accepts `STANDARD`/`SMALL`/…/`EXTRA_LARGE`.
- ❌ Don't invent icon keys or color values: an invalid `color` in rich text is not caught by `validateExpression`.
- **Why:** out-of-enum values or nonexistent icons break or silently degrade the screen.

Source: https://docs.appian.com/suite/help/latest/Styled_Icon_Component.html#main_content

### 6.3 Don't overuse "Positive"/"Negative", and don't use color as the only channel
- ✅ Reserve Positive (green) and Negative (red) colors for values with **business meaning** (gain/loss, success/failure).
- ❌ Don't use them as arbitrary decoration, and ensure sufficient contrast over colored backgrounds (billboard, card).
- **Why:** colorblind users or those with low vision don't perceive the difference; critical information must be in the words, not only in the color.

Source: https://docs.appian.com/suite/help/latest/sail/ux-rich-text.html#positive-and-negative-colors

### 6.4 Don't wrap text in rich text if you're not going to style it
- ❌ Don't put text in `a!richTextItem()` if you're not applying any style to it.
- ✅ Limit the number of rich text items, and bulleted and numbered lists per screen.
- **Why:** each item increases server evaluation time, client rendering and transmission; showing many components at once slows things down.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#dont-wrap-text-in-arichtextitem-if-you-dont-need-to-style-it · https://docs.appian.com/suite/help/latest/Rich_Text_Component.html#reducing-render-time

### 6.5 End-user rich text editor: content is data
- ✅ Store the user's HTML in the database, not in process variables; validate with the component's size limit, not text length (markup counts); keep a plain-text copy in its own column for search.
- ✅ Define the allowed formats in a constant and never remove a format after go-live: stored content still uses it.

Source: [Appian Max — End-User Rich Text Editor Component](https://community.appian.com/architecture-29/end-user-rich-text-editor-component-1322)

---

## 7. UX: consistency, loading states and empty states

### 7.1 Don't overload the page
- ✅ Favor larger text, more white space and fewer elements; before adding content, check that its visual cost pays off.
- **Why:** less cluttered pages feel more modern and usable.

Source: https://docs.appian.com/suite/help/latest/sail/employee-home-pages.html#best-practices-for-employee-home-pages

### 7.2 Preserve layout consistency as data changes
- ✅ Set an upper limit on the number of items per section and a minimum card height. On home pages, a highlights list shows typically **5 to 10** items, without paging, with a link to the full list.
- ❌ Don't let a card change height sharply depending on how many items it shows.
- **Why:** layout jumps when the data changes are disorienting.

Source: https://docs.appian.com/suite/help/latest/sail/employee-home-pages.html#best-practices-for-employee-home-pages

### 7.3 Show an empty-state message, not an empty list
- ✅ When there's no data, show an "empty list" message and keep a minimum height that balances the page.
- ❌ Don't leave an empty gap without explanation.
- **Why:** it tells the user there are no items (not that something failed) and keeps the layout balanced.

Source: https://docs.appian.com/suite/help/latest/sail/employee-home-pages.html#best-practices-for-employee-home-pages · https://docs.appian.com/suite/help/latest/sail/lists.html#full-page-empty-state-message

### 7.4 Loading states: automatic placeholders
- ✅ Rely on asynchronous loading (section 2.3): components waiting on async data show skeletons automatically.
- **Why:** the user knows content is loading without the rest of the screen being blocked.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#use-asynchronous-loading-for-slow-data

### 7.5 Organize with cards to reduce visual noise
- ✅ Use `a!cardLayout()` to group related content.
- ❌ Don't use it where it isn't allowed: inside a read-only grid, an editable grid, or a side-by-side.

Source: https://docs.appian.com/suite/help/latest/card_layout.html#main_content

---

## 8. Performance anti-patterns (actionable summary)

### 8.1 In `and()`, `or()`, `match()`, put the expensive part last
- ✅ Place expensive computations as the last argument of `and()`, `or()` and `match()`.
- **Why:** these functions short-circuit; if a cheap condition already decides the result, the expensive one is never evaluated.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#when-using-and-or-and-match-functions-put-expensive-computations-last

### 8.2 Independent queries → parallel evaluation
- ✅ If a query in a local variable references another query in another local variable, rewrite so they **don't** depend on each other.
- **Why:** variables that reference each other are evaluated in series; independent ones are evaluated in parallel, reducing total time.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#for-expensive-queries-that-rely-on-each-other-set-them-up-to-evaluate-in-parallel

### 8.3 Limit interactions on data-heavy interfaces
- ❌ Don't add lots of user interactions (filters, inputs) to dashboards with many queries.
- ✅ Use record action components to update data, and a "MENU" when there are many actions.
- **Why:** every interaction re-evaluates the **entire** interface; with many queries that means repeated waits.

Source: https://docs.appian.com/suite/help/latest/interface-performance.html#dont-add-a-lot-of-user-interactions-to-complex-interfaces-that-display-a-lot-of-data

### 8.4 Don't store large volumes in local variables
- ✅ Page/filter before saving into a local variable; remember that variables with a refresh setting other than `refreshAlways` persist in memory across every evaluation of the interface.
- **Why:** storing a lot of data in a variable keeps it in memory for as long as the variable is alive.

Source: https://docs.appian.com/suite/help/latest/expressions-best-practices.html#designing-memory-efficient-expressions

### 8.5 The number of visible components is the factor that weighs most on rendering
- ✅ Reduce the number of components shown at once: page lists, apply dynamic behavior (show detail on demand), and split large screens into steps/tabs.
- ✅ Wrap alternate branches in `if()` / `choose()` (or `showWhen: false`) so hidden components **aren't evaluated**.
- **Why:** browser processing time is determined almost entirely by the number of visible components, and the Health Check's "SAIL interface size" counts visible components plus their data. Server time is the other half, driven by queries and expressions (§8.1–8.4): a screen is fast only when both are under control.

Source: https://docs.appian.com/suite/help/latest/SAIL_Performance.html#phase4 · https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html#sail-interface-size

---

## 9. Accessibility

> **Where the depth lives.** The official Appian skill carries
> `references/accessibility-audit.md`, `component-checks.md` and `accessibility-reference.md`: the
> audit procedure and the per-component checks. This section keeps the criterion and what closes the
> gate. What this skill adds is that accessibility is *gated* (doc 10, gate 4):
> the part that can be checked from the SAIL or the rendered interface is checked, and the part that
> needs a person with a screen reader is recorded as an owned deferral instead of being quietly skipped.
> **Without that skill installed**, the platform sources cited under each rule are what it is built
> from.

### 9.1 Always a text equivalent
- ✅ Give `altText` to meaningful images and icons; for critical data and controls, express them in text.
- ✅ In read-only grids with conditional background color, add accessibility text explaining the meaning of each color.
- **Why:** screen readers don't read what is purely visual; an image with text only reaches a user who can see the screen.

Source: https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html#always-provide-a-text-equivalent

### 9.2 Don't rely on color to communicate
- ❌ Don't use instructions like "click the red button".
- ✅ Reinforce color with text or icons.
- **Why:** users with low vision or colorblindness can't distinguish the color.

Source: https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html#avoid-relying-on-color-to-communicate-information

### 9.3 Describe inputs explicitly
- ✅ Use `label`, `instructions` and `validations` on every input; if you don't want to show the label, use `labelPosition: "COLLAPSED"` so the screen reader still reads it.
- ✅ Use "Accessibility Text" for extra context (e.g. which section a field belongs to).
- **Why:** accessibility is automatically optimized by using label/instructions/validations; visual proximity isn't enough for a screen-reader user.

Source: https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html#explicitly-describe-form-inputs · https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html#use-accessibility-text-to-provide-supplemental-information

### 9.4 Reference standard: WCAG 2.2 AA / Section 508
- ✅ Design against WCAG 2.2 Level AA and Section 508; test with the recommended browser+reader combinations (Chrome/JAWS, Edge/JAWS, Firefox/NVDA, Safari/VoiceOver).
- ⚠️ What reviews keep catching (Appian Max checklist): text contrast 4.5:1 (3:1 for large text) — check Positive/Warn colors against the theme; a placeholder is not a label; radio and checkbox groups need a group label; chart drill-downs aren't keyboard-operable, so the grid alternative (§9.5) is mandatory. Source: [Appian Max — Accessibility Checklist](https://community.appian.com/architecture-29/accessibility-checklist-1298).
- **Why:** these are the standards Appian validates its product against; testing accessibility requires doing it with a real screen reader, not just reviewing the SAIL.

Source: https://docs.appian.com/suite/help/latest/building_accessible_applications.html#main_content

### 9.5 A chart is only visual: always offer the same information as a grid
- ✅ Every chart needs an equivalent text representation a screen reader can read; the recommended pattern is a **chart↔grid toggle** showing exactly the same data.
- ✅ Implement it with a boolean local variable (e.g. `local!showAsGrid`) and an `a!dynamicLink` that flips it with `not()`; an `if()` decides whether the chart or the grid is rendered.
- ❌ Don't leave a chart as the **only** way to access the data.
- **Why:** charts are built for users who can see the screen; a screen reader doesn't interpret a chart. It's an accessibility requirement, not an optional extra.

Source: https://docs.appian.com/suite/help/latest/recipe-configure-a-chart-to-grid-toggle.html · https://docs.appian.com/suite/help/latest/Tempo_Report_Design.html#usability

### 9.6 Headers with real heading tags (H1–H6), not enlarged rich text
- ✅ Structure headers with **section headers** and **heading fields** (`a!headingField()`), setting their level with the "Accessibility Heading Tag" parameter (`labelHeadingTag` on sections, `headingTag` on `a!headingField()`), not with an `a!richTextItem()` with a larger `size`/`color` that only *looks* like a title.
- ✅ Respect the hierarchy and **correct the default mapping** when nesting: the default tag depends on the label size (Extra Large / Large Plus / Large → H1; Medium Plus / Medium → H2; Small → H3; Extra Small → H4), so a "Large" section nested under an "Extra Large" one must have its heading tag moved from **H1 to H2** (avoid two H1s on the same screen).
- ❌ Don't imitate headers with large colored text: the screen reader doesn't announce it as a header, and the user loses heading-based navigation.
- **Why:** screen readers move through the page by jumping between headings and only recognize them if they carry the semantic heading tag; an enlarged rich text is visually a title but semantically plain text.

Source: https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html#use-accessible-headers · https://docs.appian.com/suite/help/latest/sail/content-structure.html

---

## 10. Multilingual interfaces: translation sets

The Admin Console locale only translates **Appian-generated** text and formats dates, times and numbers;
the text developers write in design objects is translated with the **translation set** object.

### 10.1 Put user-facing text in a translation set from the start
- ✅ If the app is (or may become) multilingual, reference **translation strings** (`translation!…`) for
  labels, instructions, tooltips and messages instead of literals. User-entered data is not translated.
- ✅ **One translation set per application**; up to **5,000 strings** per set — beyond that, a second set.
- ✅ Use **translation variables** (`{name}`, max **30** per string) for dynamic values instead of
  concatenating fragments: word order changes between languages.
- ✅ Fill in **Notes for Translator**, especially to tell apart strings that look duplicated.
- ✅ Hand translations over with **Export strings** to Excel and bring them back with **Import strings**;
  blank cells are not imported, so they don't overwrite existing values.
- **Why:** translating after the fact means reopening every interface; a string edited once updates
  everywhere, and the user sees their locale with fallback to the primary translation locale.

Source: [Translation Set Object](https://docs.appian.com/suite/help/latest/translation-set-object.html) · [Design best practices](https://docs.appian.com/suite/help/latest/translation-set-object.html#design-best-practices) · [Admin Console — Internationalization](https://docs.appian.com/suite/help/latest/admin-internationalization.html)

### 10.2 Locale traps
- ⚠️ Every translation locale must be **enabled as a system locale in every environment** where the set is
  used, or its strings don't show.
- ❌ Don't enable **"Always override users' selected locale"** in the Admin Console: everyone would see the
  primary system locale regardless of their preference.
- ⚠️ Changing the **primary translation locale** requires every string to have a value in the new one.
- ⚠️ **Deployment:** deleting a string in the source does **not** delete it in the target; and a
  translation set's name must not collide with a rule, constant, interface, integration or function in
  the target, or the import fails.

Source: [Translation Set Object — Design best practices / Deployment](https://docs.appian.com/suite/help/latest/translation-set-object.html#deployment) · [Deployment Best Practices — Rules](https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html#rules)

---

## 11. Offline forms (Appian Mobile; ⓥ Appian for Windows from 26.6)

Offline forms are a tier-dependent capability (Advanced/Premium); Appian for Windows is licensed
separately. In the apps, an offline-enabled
interface talks to the server **only during the offline data sync**, even when the user is online;
anything not cached then does not exist on the device.

### 11.1 Load everything at the top
- ✅ Query all data in **local variables (or rule inputs) at the top of the interface**, before any
  component: only those are evaluated and cached during the sync. Child interfaces receive data by rule
  input (§1.5).
- ✅ Grids and charts: query the record type into a local variable and pass it to `data`; ❌ never
  `data: recordType!…` directly (the query moves into the component and fails offline).
- ⚠️ Record lists, record views and records-powered grid features (user filters, search) don't work offline.

### 11.2 Use only compatible functions and components
- ✅ Check compatibility in the **All Functions** table (offline filter) or in design guidance; partially
  compatible functions only work in a top-level local variable.
- ❌ No **plug-ins** and no server-bound components (e.g. user pickers → a dropdown fed at the top).
- ❌ No `a!startProcessLink()` in an offline-enabled interface: the app reports the system as "degraded (stateless)" ([KB-1867](https://community.appian.com/application-design-33/kb-1867-start-process-link-not-displayed-because-the-system-is-in-a-degraded-stateless-status-error-when-starting-processes-in-the-appian-for-mobile-devices-app-966)).

### 11.3 Don't break forms waiting to be submitted
- ⚠️ Changing a **CDT** used offline — deleting or renaming a field, or changing its type — can make
  pending forms fail to submit. Only **add** fields; otherwise create a new CDT. Prefer a map saved into a
  typed rule input over type constructors.
- ⚠️ Writing a CDT updates **every** column: build a CDT with only the fields you write, or you null the rest.
- ⚠️ Don't change a custom **process calendar** while users are working offline, and make sure users have
  permission on the **upload folder** — the form can't check it until it is back online.
- ✅ **Test the whole form in the app itself**, completing every field; the browser evaluates it like a
  normal interface and hides the problems.

Source: [Design Interfaces for Offline Use](https://docs.appian.com/suite/help/latest/offline-mobile-design-best-practices.html) · [Avoiding pending offline form submission failures](https://docs.appian.com/suite/help/latest/offline-mobile-design-best-practices.html#avoiding-pending-offline-forms-submission-failures) · [About Offline Experiences](https://docs.appian.com/suite/help/latest/offline-mobile-overview.html)

---

## Sources

Official documentation pages used above (`docs.appian.com/suite/help/latest/…`, aliased to the latest release); Community and KB articles are cited inline:

- Interface Performance Best Practices — https://docs.appian.com/suite/help/latest/interface-performance.html
- Local Variables — https://docs.appian.com/suite/help/latest/Local_Variables.html
- Interface Object (rule inputs and local variables) — https://docs.appian.com/suite/help/latest/interface_object.html
- Reusing Interfaces — https://docs.appian.com/suite/help/latest/using_interfaces_in_appian.html#reusability
- Offline Mobile Design Best Practices (Design Interfaces for Offline Use) — https://docs.appian.com/suite/help/latest/offline-mobile-design-best-practices.html
- About Offline Experiences — https://docs.appian.com/suite/help/latest/offline-mobile-overview.html
- Translation Set Object — https://docs.appian.com/suite/help/latest/translation-set-object.html
- Admin Console — Internationalization — https://docs.appian.com/suite/help/latest/admin-internationalization.html
- Deployment Best Practices — Rules (translation sets) — https://docs.appian.com/suite/help/latest/Application_Deployment_Guidelines.html#rules
- About Queries — https://docs.appian.com/suite/help/latest/about-queries.html
- a!queryRecordByIdentifier() — https://docs.appian.com/suite/help/latest/fnc_system_a_queryrecordbyidentifier.html
- a!queryRecordType() — https://docs.appian.com/suite/help/latest/fnc_system_queryrecordtype.html
- a!queryEntity() — https://docs.appian.com/suite/help/latest/fnc_system_a_queryentity.html
- Recipes for Querying Records — https://docs.appian.com/suite/help/latest/Query_Recipes.html
- Record Type Query Performance Best Practices — https://docs.appian.com/suite/help/latest/query-best-practices.html
- Expressions Best Practices — https://docs.appian.com/suite/help/latest/expressions-best-practices.html
- Responsive Design — https://docs.appian.com/suite/help/latest/responsive_design.html
- Columns Layout — https://docs.appian.com/suite/help/latest/Columns_Layout.html · Design guidance: https://docs.appian.com/suite/help/latest/sail/ux-columns-layout.html
- Form Layout (design) — https://docs.appian.com/suite/help/latest/sail/ux-form-layout.html
- Forms (design) — https://docs.appian.com/suite/help/latest/sail/forms.html
- Wizard Layout (design) — https://docs.appian.com/suite/help/latest/sail/ux-wizard-layout.html
- Progressive Disclosure (design) — https://docs.appian.com/suite/help/latest/sail/ux-progressive-disclosure.html
- Recipe: Conditional Requiredness — https://docs.appian.com/suite/help/latest/recipe-configure-buttons-with-conditional-requiredness.html
- Recipe: Validation Errors not specific to one component — https://docs.appian.com/suite/help/latest/recipe-showing-validation-errors-that-arent-specific-to-one-component.html
- Editable Grid Component — https://docs.appian.com/suite/help/latest/Editable_Grid_Component.html
- Grids (design) — https://docs.appian.com/suite/help/latest/sail/ux-grids.html
- Charts (design) — https://docs.appian.com/suite/help/latest/sail/ux-charts.html
- Column Chart Component (usage considerations) — https://docs.appian.com/suite/help/latest/Column_Chart_Component.html
- Tempo Report Design (usability) — https://docs.appian.com/suite/help/latest/Tempo_Report_Design.html
- Recipe: Chart-to-Grid Toggle — https://docs.appian.com/suite/help/latest/recipe-configure-a-chart-to-grid-toggle.html
- Rich Text Display Component — https://docs.appian.com/suite/help/latest/Rich_Text_Component.html
- Rich Text Item — https://docs.appian.com/suite/help/latest/Styled_Text_Component.html
- Rich Text Icon — https://docs.appian.com/suite/help/latest/Styled_Icon_Component.html
- Rich Text (design) — https://docs.appian.com/suite/help/latest/sail/ux-rich-text.html
- Card Layout — https://docs.appian.com/suite/help/latest/card_layout.html
- Lists (empty state) — https://docs.appian.com/suite/help/latest/sail/lists.html
- Employee Home Pages (design) — https://docs.appian.com/suite/help/latest/sail/employee-home-pages.html
- Accessibility (design) — https://docs.appian.com/suite/help/latest/sail/ux-accessibility.html
- Content Structure (design) — https://docs.appian.com/suite/help/latest/sail/content-structure.html
- Building Accessible Applications — https://docs.appian.com/suite/help/latest/building_accessible_applications.html
- SAIL Performance — https://docs.appian.com/suite/help/latest/SAIL_Performance.html
- Understanding the Health Check Report (SAIL interface size) — https://docs.appian.com/suite/help/latest/understanding-the-health-check-report.html
- Validation Message — https://docs.appian.com/suite/help/latest/Validation_Message.html
- Inputs (design) — https://docs.appian.com/suite/help/latest/sail/ux-inputs.html · Dropdown Component — https://docs.appian.com/suite/help/latest/Dropdown_Component.html · Recipe: Cascading Dropdowns — https://docs.appian.com/suite/help/latest/recipe-configure-cascading-dropdowns.html
- Buttons (design) — https://docs.appian.com/suite/help/latest/sail/ux-buttons.html · Button Component — https://docs.appian.com/suite/help/latest/Button_Component.html
- File Upload Component — https://docs.appian.com/suite/help/latest/File_Upload_Component.html · Admin Console — File Upload — https://docs.appian.com/suite/help/latest/admin-file-upload.html
- Record Action Component — https://docs.appian.com/suite/help/latest/Record_Action_Component.html · Record actions (design) — https://docs.appian.com/suite/help/latest/sail/ux-record-actions.html · Refresh behavior — https://docs.appian.com/suite/help/latest/refresh-behavior-interfaces.html
- Read-Only Grid (paging) — https://docs.appian.com/suite/help/latest/Paging_Grid_Component.html · Export to Excel limits — https://docs.appian.com/suite/help/latest/Optimizing_Record_Lists_for_Export_to_Excel.html
