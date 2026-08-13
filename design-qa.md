# Design QA — Four-step Translation Workflow

- Source visual truth: user-provided ASCII wireframe and follow-up UX/design specification in the current task.
- Implementation: `app.py`, browser-rendered at `http://127.0.0.1:8517`.
- Viewport: 1280 × 720 CSS px, device pixel ratio 2.
- State captures reviewed: Step 01 Document, Step 02 Translation Strategy, AI Provider Settings, Task Workspace.
- Density normalization: source is a structural text wireframe, so comparison used viewport proportions and visible hierarchy rather than pixel-level raster matching.

## Full-view comparison evidence

- Persistent left navigation matches the requested hierarchy: new task, four numbered steps, history, terminology/memory, settings.
- Step 01 contains only source upload, target language, and an optional termbase status/add control.
- Provider credentials are absent from task creation and live on a dedicated Settings page.
- Step 02 uses three preset cards and one collapsed Advanced Settings control.
- Task Workspace replaces configuration after start/open and shows a pipeline beside current-stage progress.

## Focused region comparison evidence

- Typography: 30px page title, 19–20px section headings, 14px body, 12–13px helper text; Manrope with CJK system fallbacks.
- Spacing: 300px left rail, 32px main gutter, 10px card radius, 8px control radius, no decorative shadows.
- Color: canvas `#F7F8FA`, surfaces `#FFFFFF`, text `#111827`, secondary `#6B7280`, border `#E5E7EB`, primary `#2563EB`.
- Assets/icons: no raster imagery is required by the wireframe. Core workflow controls use native Streamlit/material glyphs rather than emoji decoration.
- Copy: task actions use user language (`下一步`, `开始任务`, `任务会自动保存`) and Provider terminology is isolated to settings.

## Comparison history

1. P1 — Hero and one-page configuration dominated the first screen.
   - Fix: removed Hero entirely; replaced with restrained page title and a four-step stateful workflow.
   - Post-fix evidence: Step 01 renders only document inputs and task-level language/termbase choices.
2. P1 — Provider/API configuration occupied the primary task path.
   - Fix: moved Provider, Model, API Key, Base URL, and connection test to Settings.
   - Post-fix evidence: Step 01 has no Provider fields; Settings renders the complete connection form.
3. P1 — Run state continued to expose configuration.
   - Fix: starting/opening a task switches `app_view` to `workspace` and clears the setup container.
   - Post-fix evidence: browser interaction confirmed `Task Workspace` visible and Step 01 helper text absent.
4. P2 — Large secondary termbase dropzone and heavy blue sidebar selection increased noise.
   - Fix: replaced termbase dropzone with a compact status/add row; changed active navigation to a light-blue state.
   - Post-fix evidence: final Step 01 screenshot shows one dominant dropzone and restrained navigation.

## Primary interactions tested

- Four sidebar steps switch the creation view.
- Preset selection defaults to Standard and exposes Advanced Settings progressively.
- Settings opens Provider configuration without task fields.
- History opens an existing task in Task Workspace.
- Task Workspace hides setup fields and displays pipeline/progress.
- Browser console error log: empty.

## Findings

No actionable P0/P1/P2 differences remain against the supplied structural target.

## Follow-up polish

- P3: native Streamlit uploader button text remains English (`Upload`) under the current locale.
- P3: token/time/cost estimation is intentionally omitted until provider pricing and document tokenization can produce trustworthy figures.

## Refinement pass — 2026-08-13

- Source visual truth: the user's second-round written wireframe and the prior browser-rendered Step 01 state supplied in this task.
- Implementation screenshot: `tmp/refinement-implementation.png`.
- Viewport: 1280 × 720 CSS px; screenshot 1280 × 720 pixels at device pixel ratio 1.
- State: New Task → Document, empty source and optional termbase.

### Full-view comparison evidence

- Main content now uses a 1040px working width beside a 236px sidebar; controls no longer stretch across the full canvas.
- The source dropzone is 156px tall and its label, guidance, file limit, and select action form one centered visual group.
- New Task is a bordered creation action; Current Task is a separate vertical stepper with completed, current, and pending states.
- Target language is constrained to 340px. The termbase uses Add, attached-file, Remove, and file-picker states without a switch.
- A persistent bottom action bar keeps autosave status and Back/Next actions tied to every setup step.
- Sidebar UI labels are Chinese except for the product name, provider name, model identifier, and file-format names.

### Focused region comparison evidence

- Sidebar: connector, status icons, active-state highlight, library grouping, and lightweight provider status remain visible at 720px height.
- Form: source label/dropzone, language field, termbase helper/action, and bottom action bar fit above the fold at 1280 × 720.
- Typography and colors retain the approved Manrope/CJK stack, `#111827` primary text, `#667085` secondary text, `#2563EB` primary, and low-elevation white surfaces.
- Images/assets: this workspace state has no raster imagery; interface icons use Streamlit Material Symbols rather than emoji or handcrafted SVG.

### Comparison history

1. P1 — New Task and Step 01 previously appeared as two selected navigation items.
   - Fix: New Task became a separate outlined action; only the workflow step carries current-state emphasis.
   - Evidence: final capture shows one active Step 01 row and an unselected New Task button.
2. P1 — Dropzone and full-width short fields made the page feel sparse and demo-like.
   - Fix: reduced the dropzone to 156px, centered its contents, constrained the language field, and reduced section spacing.
   - Evidence: all Step 01 controls and the action bar fit within one 720px viewport.
3. P1 — Termbase attachment used switch semantics.
   - Fix: replaced it with Add Termbase, picker, attached-file summary, and Remove states.
   - Evidence: browser interaction exposes the picker and reports zero switch controls.
4. P2 — Workflow progress and actions lacked continuity.
   - Fix: added a vertical connector, Material status icons, completed/current/pending states, and a fixed action bar.
   - Evidence: Step 02 interaction changes Step 01 to completed and Step 02 to current; Back/Next stay visible.

### Primary interactions tested

- New Task returns to Step 01.
- Steps update completed/current/pending state.
- Add Termbase opens the supported-format picker with no toggle control.
- Provider Manage opens the localized AI Engine settings page.
- Advanced Settings remains available on Step 02.
- Browser console error log: empty.

### Findings

No actionable P0/P1/P2 differences remain against the refinement target.

### Follow-up polish

- P3: Streamlit's uploader accessibility snapshot still includes the native English token `Upload`; the visible button is localized as `选择文件`.

final result: passed

## Step 01 alignment correction — 2026-08-13

- Source visual truth: `/var/folders/70/m56f428103j8mb2ssqj6zr4c0000gn/T/codex-clipboard-1e4bc285-7b67-4b31-a1e4-360c40d22c19.png` and the user's two annotated defects.
- Implementation screenshot: `tmp/step01-alignment-fix.png`.
- Viewport and density: 1600 × 930 CSS px; implementation capture 1600 × 930 encoded pixels while the browser reported device pixel ratio 2.
- State: Step 01 with one uploaded DOCX.

### Full-view and focused comparison evidence

- The four workflow nodes now share one fixed 18px grid track. Browser measurements report identical node center X coordinates: `[37, 37, 37, 37]`; labels also begin on one shared track.
- The connector runs through that node center from Step 01 to Step 04.
- The remove control is now a 36px transparent icon button inside the file card's right edge. Its center differs from the 74px file-card center by 0px and it no longer overlaps the target-language field.
- The incorrect black default button surface is explicitly overridden; the control now uses transparent background, neutral icon color, and a subtle red hover state only.

### Findings

No actionable P0/P1/P2 alignment differences remain for the two reported defects.

### Checks

- Browser measurement and visual capture passed at the reported wide-screen layout.
- Browser console errors: none.
- Python compile, AppTest, and whitespace checks passed.

final result: passed

## Step 02 workflow pass — 2026-08-13

- Source visual truth: the user's Step 01 state-machine correction and Step 02 preset/advanced-settings wireframe and behavior specification in this task.
- Implementation screenshots: `tmp/step01-status-machine.png`, `tmp/step02-presets.png`, `tmp/step02-advanced-default.png`, and `tmp/step02-advanced-adjusted.png`.
- Viewport and density: 1280 × 720 CSS px; implementation captures 1280 × 720 encoded pixels while the browser reported device pixel ratio 2. The source is a written product specification, so the comparison used rendered hierarchy, component states, and workflow behavior rather than pixel overlay.
- States: source uploaded and waiting for parse; Standard preset default; Standard advanced settings expanded; Standard modified with academic report enabled.

### Full-view comparison evidence

- Step 01 keeps the frozen structure and now shows one coherent state: `已上传 · 等待解析` with the right-side state `已上传`. The remove action is an icon-only control inside the file card.
- Step 02 presents three equal workflow cards. Each card states intended use, concrete pipeline, and relative speed/cost trade-off; Standard has a distinct light-blue `推荐` badge.
- Selected state uses an international-blue radio node, blue border, and subtle blue surface. Unselected cards remain white with neutral borders and readable dark text; no red selection semantics remain.
- Advanced Settings is a white bordered continuation of the workspace, not a black console panel. Its grouped controls use the same blue interaction tokens as the rest of MTI Tool.

### Focused region comparison evidence

- Presets: `快速` exposes `翻译`; `标准` exposes `翻译 → 质量检查`; `学术增强` exposes `翻译 → 独立审校 → 证据分析`.
- Effective configuration: changing a control updates the shared `strategy_config` used at runtime and changes the state label to `标准 · 已调整`.
- Reset behavior: choosing any preset restores that preset's defaults and shows a lightweight toast rather than a modal.
- Contextual disclosure: `案例分析理论` is absent when report generation is off and appears with `自动推荐` only when `生成实践报告` is enabled. The custom option also exposes a real free-text theory field.
- Translation memory: the UI switch now controls backend TM reads/writes; it is no longer a disabled decorative setting.
- Typography/tokens/assets: Manrope/CJK fallbacks, 12–15px card hierarchy, white surfaces, `#E5E7EB` borders, `#2563EB` interactions, Material Symbols, and 8/10px radii match the established system. No raster imagery is required for this workflow screen.

### Comparison history

1. P1 — Preset cards did not explain what users were choosing.
   - Fix: replaced terse captions with intended use, explicit workflow, and cost/time trade-off on each card.
   - Post-fix evidence: `tmp/step02-presets.png` shows all three workflows without requiring Advanced Settings.
2. P1 — Advanced Settings inherited dark/default component styles and exposed unrelated fields.
   - Fix: replaced the old expander treatment with a white grouped panel and contextual report settings.
   - Post-fix evidence: `tmp/step02-advanced-default.png` contains only Translation Assistance defaults; the academic theory field is absent.
3. P1 — Preset labels could disagree with modified runtime flags.
   - Fix: introduced one effective configuration object, explicit `已调整` state, and preset reset behavior.
   - Post-fix evidence: `tmp/step02-advanced-adjusted.png` shows `标准 · 已调整` after report generation is enabled.
4. P2 — File status copy mixed waiting and ready semantics, while removal had excessive visual weight.
   - Fix: added uploaded/parsing/parsed/error states and moved removal into a subtle icon-only card action.
   - Post-fix evidence: `tmp/step01-status-machine.png` shows one unambiguous uploaded state and no large danger button.

### Primary interactions and checks

- Browser: Step 01 upload, file status, Next activation, Step 02 card selection, Advanced open/closed, default controls, report toggle, adjusted state, and conditional theory field.
- Browser console errors: none.
- Automated: AppTest state relationships, preset reset, contextual disclosure, backend TM off behavior, Python compile, GUI launcher, provider/exchange/mode/color tests, and whitespace checks passed.

### Findings

No actionable P0/P1/P2 differences remain against the Step 02 workflow specification.

### Follow-up polish

- P3: source parsing begins when the task starts, so the pre-run file card correctly remains at `已上传 · 等待解析`; after deterministic parsing, saved state advances it to `解析完成` and adds PDF page count when available.

final result: passed

## Step 01 freeze pass — 2026-08-13

- Source visual truth: the user's final Step 01 density, polish, state, and micro-interaction specification in this task.
- Implementation screenshots: `tmp/step01-polish-empty.png` and `tmp/step01-polish-file-state.png`.
- Viewport and density: 1280 × 720 CSS px; screenshots 1280 × 720 encoded pixels while the browser reported device pixel ratio 2. Source is a written product specification, so comparison used rendered proportions, states, and component behavior rather than raster overlay.
- States: Step 01 empty source; Step 01 source file ready; Step 02 after successful progression.

### Full-view comparison evidence

- Main vertical spacing is compressed without changing the frozen information architecture; the complete empty state and bottom action bar remain above the fold.
- Source input is now a labeled, 148px clickable dropzone with a real Material upload icon, blue hover/focus affordance, and centered two-line guidance.
- Sidebar library actions use one aligned icon/label grid, while the workflow connector runs through the centers of all four step nodes.
- Target language retains its approved 340px width and now renders as one border box rather than nested bordered surfaces.
- The default provider marker is outlined and neutral; only a successful connection test changes it to green, and a failed test changes it to red.

### Focused region comparison evidence

- Empty source: `原文` is visible immediately above the dropzone; Next is disabled gray-blue and autosave copy reads `更改会自动保存`.
- File-ready state: the empty dropzone is replaced by a file summary card with filename, total size, parse readiness, remove action, green ready status, and `已保存` feedback. Next becomes the sole solid brand-blue CTA.
- Step progression: moving to Step 02 changes Step 01 from current radio node to completed check node and Step 02 to the current node.
- Typography, tokens, and assets: the approved Manrope/CJK stack, international-blue token system, 8/10px radii, native Material Symbols, and no gradients/emoji/decorative cards are retained.
- Copy: termbase copy is shortened to `术语库` and `可选 · 用于保持术语与专名一致`.

### Comparison history

1. P2 — The upload area lacked an obvious clickable affordance.
   - Fix: added a 20px Material upload icon, full-zone pointer target, hover/focus blue border and subtle blue surface.
   - Post-fix evidence: final empty-state capture shows a coherent interactive unit rather than an informational panel.
2. P2 — Uploaded files did not replace the empty-state prompt or visibly activate the workflow.
   - Fix: added file-ready summary, remove action, saved feedback, and brand-blue CTA activation.
   - Post-fix evidence: file-state capture shows `ui-state-sample.docx`, `36 KB · 已添加，等待解析`, `文件已就绪`, `已保存`, and enabled Next.
3. P2 — Provider status was visually truthful only by convention.
   - Fix: status now starts unverified, resets on credential/model/base changes, turns connected only after a successful test, and uses error semantics on failure.
   - Post-fix evidence: browser reports `.mti-provider.is-unverified` in the untouched state; AppTest asserts it is not green by default.
4. P2 — Users could attempt to jump to later steps without actionable feedback.
   - Fix: sidebar step requests are gated by source completion and show `请先上传原文。`; the completed node appears only after a file exists.
   - Post-fix evidence: AppTest verifies blocked and completed flows, and browser verification confirms the Step 01 completed node on Step 02.

### Primary interactions and checks

- Browser: empty source, real DOCX upload, file-ready state, enabled Next, transition to Step 02, completed/current step nodes, and provider unverified state.
- Browser console errors: none.
- Automated: Python compile, AppTest workflow/state checks, GUI launcher tests, provider/exchange/mode/color tests, and diff whitespace check passed.

### Findings

No actionable P0/P1/P2 differences remain against the Step 01 freeze specification.

### Follow-up polish

- P3: drag-over replacement copy (`释放以上传`) remains provided by Streamlit's native uploader behavior rather than a separately scripted overlay.

final result: passed

## Component-language pass — 2026-08-13

- Source visual truth: the user's seven-point component specification and accompanying control-state wireframe in this task.
- Implementation screenshot: `tmp/component-language-final.png`.
- Viewport and density: 1280 × 720 CSS px, 1280 × 720 screenshot pixels, device pixel ratio 1.
- State: Step 01, no source file, Next disabled.

### Full-view comparison evidence

- Ordinary controls now share one language: white surface, `#E5E7EB` border, `#111827` text, 8px radius.
- Add Termbase remains a white outline action; the full source dropzone is the file-selection target without a separate solid button.
- Next is the only brand-colored workflow CTA. Its empty-state appearance is explicitly disabled gray-blue and changes to enabled after `task_files` is populated.
- The main vertical rhythm uses the existing 8/12/16/24px scale; no new layout, card, header, gradient, or decoration was introduced.
- Current Step 01 uses a status node and blue text without a second blue selection block; the connector is visually behind the nodes.
- Brand subtitle is reduced to `Translation Practice Workspace` on one restrained line.

### Focused region comparison evidence

- Target language: label is visible at full contrast and its 340px control is white with an outlined border and dark chevron.
- Upload: one centered instruction plus one supporting format/size line inside a 152px clickable dropzone.
- Termbase: white outline button with attachment icon; no black fill or switch semantics.
- Action bar: copy reads `更改会自动保存`; disabled Next is semantically disabled and visually distinct from enabled primary blue.
- Images/assets: no raster imagery is required in this state; existing Material Symbols remain the only interface icons.

### Comparison history

1. P1 — Select and secondary controls appeared as dark surfaces against a light workspace.
   - Fix: targeted Streamlit's current React Aria Select DOM and applied shared white-surface tokens; reinforced outline-button tokens.
   - Post-fix evidence: final screenshot shows white Select and termbase button, with Next as the sole colored CTA.
2. P1 — Upload content read as a four-layer mechanical stack.
   - Fix: removed the separate visible chooser button and reduced copy to one instruction plus one support line.
   - Post-fix evidence: the final 152px dropzone reads as one clickable unit.
3. P2 — Current step duplicated emphasis with both a filled background and status node.
   - Fix: removed the filled current-row background while retaining blue node/text and completed check states.
   - Post-fix evidence: Step 01 is clear without becoming another CTA.
4. P2 — Disabled Next looked ambiguously pale and the autosave wording was unnatural.
   - Fix: established explicit gray-blue disabled tokens and changed copy to `更改会自动保存`.
   - Post-fix evidence: browser reports Next disabled in the empty state; AppTest confirms it becomes enabled after a source file enters session state.

### Primary interactions and checks

- Browser: target-language label visible, Add Termbase visible, Next disabled, console errors empty.
- AppTest: Next disabled before source input and enabled after source input.
- App boot, GUI launcher, provider/exchange modes, Python compile, and diff whitespace checks passed.

### Findings

No actionable P0/P1/P2 differences remain against the component-language target.

### Follow-up polish

- P3: Streamlit retains its native file-upload accessibility name internally, while the visible dropzone copy is fully localized.

final result: passed
