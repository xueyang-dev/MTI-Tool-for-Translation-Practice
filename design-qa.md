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

## TransPraxis brand integration — 2026-08-14

- Source visual truth: `/Users/xueyang/Downloads/ChatGPT Image 2026年8月14日 17_34_58.png`.
- Implementation screenshots: `tmp/transpraxis-step01-final.png` and `tmp/transpraxis-step02-final.png`.
- Focused comparison: `tmp/brand-qa/reference-vs-sidebar.png`.
- Desktop viewport: 1280 × 720 CSS px; narrow-window check: 900 × 720 CSS px.

### Brand fidelity

- Sidebar uses a source-derived infinity translation mark beside the exact names `TransPraxis` and `译践`; the subtitle remains `Translation Practice Workspace`.
- The logo keeps its original blue/cyan artwork and is rendered in a measured 46 × 24px slot rather than shrinking the full square source image.
- The favicon is a square source crop centered on the logo's `A` translation loop, so the mark remains identifiable at browser-tab scale.
- Deep blue is limited to primary actions and active/selected states; cyan appears as a restrained accent for upload and focus feedback. Neutral canvas, surface, text, and borders remain unchanged.

### Interaction and responsive evidence

- Browser title and all visible product-brand text use `TransPraxis / 译践`.
- Selected Standard preset renders with `#062b9a` border and `#eef3ff` tint; active workflow steps and enabled toggles use the same deep-blue family.
- At 1280px and 900px viewport widths, document width equals viewport width with no horizontal page overflow.
- At 900px, the sidebar remains 236px wide, the 46 × 24px mark and `TransPraxis` lockup remain fully visible, and horizontal overflow is clipped within the sidebar shell.

### Findings

No actionable P0/P1/P2 visual differences remain for the requested branding integration. Existing information architecture, page layout, workflow behavior, and neutral UI density are preserved.

final result: passed

## Step 02 final density pass — 2026-08-14

- Source visual truth: `/var/folders/70/m56f428103j8mb2ssqj6zr4c0000gn/T/codex-clipboard-9d15dd9d-3ed0-490e-97a0-07731992a5ca.png`, `/var/folders/70/m56f428103j8mb2ssqj6zr4c0000gn/T/codex-clipboard-595e013d-768a-4259-98ec-405c59237227.png`, and the user's annotated target behavior in this task.
- Implementation screenshots: `tmp/step-02-collapsed-final.png` and `tmp/step-02-expanded-final.png`.
- Viewport and density: browser viewport 2048 × 1180 CSS px; implementation captures 1752 × 1180 encoded pixels from the in-app browser. Source captures are 2940 × 1694 pixels and include Chrome UI; full-view comparison normalized both source captures to 1752px content width and padded them to the implementation height. Browser chrome and the user's requested density changes were treated as intentional differences.
- States: Standard preset with Advanced Settings collapsed and expanded.

### Full-view comparison evidence

- Preset cards retain the frozen three-card structure, selected state, recommendation badge, and workflow copy while shrinking from 180px to 160px.
- The collapsed Advanced control is a single 52px left-aligned row. It exposes `自动术语 · 翻译记忆 · 基础检查` without requiring expansion.
- The expanded panel is approximately 425px high versus the previous roughly 505px state. Four controls are rendered as compact settings rows with labels/helpers on the left and switches on the right.
- Typography keeps the approved hierarchy: preset workflow text is 13px/600 in `#374151`; OFF labels remain primary and readable while only the switch track uses neutral gray.
- Colors and tokens remain international blue, white surfaces, neutral borders, green always-on status, and no new shadow, gradient, or red selection state.
- No image assets are required by this settings screen. Material Symbols remain the only functional icon set.
- Copy separates translation evidence preparation from report generation: Academic Enhanced now says `为 MTI 实践报告准备完整过程证据`.

### Focused region comparison evidence

- Collapsed row measured 52px and all preset cards measured 160px in the browser.
- Expanded group labels each reserve 28px; the settings body uses a 4px layout gap and four 52px setting rows.
- The two OFF controls retain label opacity `1`; their switch tracks render white with `#98A2B3` borders rather than disabled opacity.
- `基础一致性检查` and `始终开启` share the same title line.
- Bottom navigation DOM order is `← 上一步` and `下一步 →`; both buttons keep native accessible controls and focus behavior.

### Comparison history

1. P1 — Preset cards and collapsed Advanced control were oversized for their content.
   - Fix: reduced cards to 160px and replaced the 80px two-line Advanced block with one 52px summary row.
   - Post-fix evidence: final collapsed screenshot and browser measurements.
2. P1 — Advanced switches preceded their labels and OFF settings appeared disabled.
   - Fix: rendered each option as a two-column setting row and collapsed the native toggle label visually while preserving its accessible label.
   - Post-fix evidence: final expanded screenshot; browser reports right-aligned tracks and full-opacity labels.
3. P2 — The first compact pass compressed section headings into adjacent rows.
   - Fix: restored explicit 28px group-label tracks and a 4px body gap.
   - Post-fix evidence: revised expanded screenshot shows distinct Translation Assistance, Quality Control, and Terminology Governance groups.

### Primary interactions and checks

- Browser: source upload, Step 01 → Step 02 navigation, preset rendering, Advanced expand/collapse, right-side switches, button direction, and console errors (none).
- Automated: Python compile, AppTest workflow/state coverage, and whitespace diff check passed.

### Findings

No actionable P0/P1/P2 differences remain for this Step 02 density target.

### Follow-up polish

- P3: the in-app browser's capture excludes part of the explicit 2048px viewport width, so comparison uses measured DOM dimensions for the exact 160px/52px component targets.

final result: passed

## Output and confirmation polish — 2026-08-13

- Source visual truth: the user's prioritized Step 02–04 refinement specification in this task, grounded in the existing frozen TransPraxis / 译践 shell.
- Implementation screenshots: `tmp/polish-step02-final.jpg`, `tmp/polish-step03.jpg`, `tmp/polish-step03-academic-final2.jpg`, and `tmp/polish-step04-final3.jpg`.
- Viewport and density: 1280 × 720 CSS px; screenshots are 1280 × 720 encoded pixels; browser device pixel ratio 2. Source truth is a structural/text specification rather than a raster mock, so no image-density normalization was required.
- States: Step 02 Standard preset with Advanced Settings expanded; Step 03 default output; Step 03 Practice Report enabled; Step 04 with an unconfigured AI engine.

### Full-view comparison evidence

- Step 03 now reads in the intended result-first order: Translation Style, Output Content, then Academic Output. Preset style rules are rendered as a compact explanatory card rather than an editable prompt-like textarea.
- Step 04 is divided into Task Configuration, Deliverables, and Runtime Environment. The unconfigured engine state has explicit status text, warning semantics, a direct Settings action, and a disabled Start Task CTA.
- Step 02 retains the existing preset architecture while reducing Advanced Settings density; always-on deterministic checking is represented as a read-only status rather than a disabled checkbox.
- Sidebar node/label tracks remain aligned; completed/current/pending states now differ through icon, text color, and weight without adding a selected background block.
- Typography remains Manrope with the established 30/19/14/12px hierarchy. Helper text is secondary but labels remain primary and readable.
- Layout follows the existing 236px sidebar, 1040px content region, 8–24px rhythm, white surfaces, neutral borders, and 8–10px radii. Step 04 fits the 720px desktop viewport without main-content overflow after the final compact-grid pass.
- Colors remain token-driven international blue for interactions, green for completion, amber for required setup, and red only for errors. The Practice Report toggle was explicitly corrected from Streamlit's inherited red selected state to brand blue.
- No raster imagery is required. All visible icons use the existing Material Symbols family; no emoji, handcrafted SVG, or decorative asset substitutes were added.
- Copy is now consistent around `等待解析`, `开始任务`, `翻译模式`, `输出内容`, `生成实践报告`, and `运行环境`.

### Focused region comparison evidence

- Step 03 style card contains three scannable effects of the selected style; custom style alone exposes an editable text area.
- `双语译文` uses a `默认生成` status badge, and `基础一致性检查` uses `始终开启`, so neither looks optionally disabled.
- Step 03 academic settings stay hidden until `生成实践报告` is enabled, then reveal Theory Framework and optional Literature Evidence.
- Step 04 deliverables accurately reflect output switches; Task Configuration includes source, language, mode, style, termbase, and effective workflow.
- Browser inspection confirmed the setup banner text is visible at full opacity in `rgb(120, 53, 15)` and the selected report switch uses `rgb(37, 99, 235)`.

### Comparison history

1. P1 — Step 03 looked like a prompt/configuration editor rather than an output decision screen.
   - Fix: replaced preset textareas with a style explanation card and separated style, file outputs, and academic outputs.
   - Post-fix evidence: `tmp/polish-step03.jpg` and conditional academic state capture.
2. P1 — Step 04 lacked a decisive summary and actionable engine status.
   - Fix: added configuration/deliverable/runtime sections, explicit readiness states, a warning banner, and `前往设置`.
   - Post-fix evidence: `tmp/polish-step04-final3.jpg` and DOM interaction snapshot.
3. P2 — The first confirmation layout pushed runtime/banner content behind the persistent action bar.
   - Fix: changed the top summary to a compact two-column card grid and the configuration fields to three columns.
   - Post-fix evidence: final browser measurement reports main height equal to the 720px viewport.
4. P2 — Streamlit's selected Practice Report toggle remained red outside the Step 02 scope.
   - Fix: extended brand-blue selected-state rules to Step 03 widget-key containers.
   - Post-fix evidence: computed selected switch background is `rgb(37, 99, 235)`.

### Primary interactions and checks

- Browser: Advanced Settings expansion, Step 02 → Step 03 → Step 04 navigation, Practice Report conditional reveal, sidebar states, engine warning and disabled Start state, desktop overflow, and console errors (none).
- Automated: Python compile, AppTest workflow/state coverage, provider/exchange/config semantics, GUI launcher, and whitespace diff check.

### Findings

No actionable P0/P1/P2 differences remain against the refinement target.

### Follow-up polish

- P3: the narrow 1280px capture keeps the Step 03 academic detail below the initial fold by design; the persistent action bar remains visible and the page scrolls normally.

final result: passed

## Strategy / output configuration refactor — 2026-08-13

- Source visual truth: the user's repository-grounded configuration model and Step 02 / Step 03 wireframes in this task.
- Implementation screenshots: `tmp/config-refactor-step02.jpg` and `tmp/config-refactor-step03-report-final.jpg`.
- Viewport and density: 1280 × 720 CSS px, 1280 × 720 screenshot pixels reported by the in-app browser capture, browser device pixel ratio 2; both source truth and implementation were evaluated at the same desktop layout/state, so no crop or rescale normalization was needed.
- States: Step 02 with the Standard preset and Advanced Settings expanded; Step 03 with Practice Report enabled and the evidence-constrained Theory Framework visible.

### Full-view comparison evidence

- Step 02 keeps the frozen workspace shell, three preset cards, progressive disclosure, and bottom action bar. Preset copy now exposes the effective workflow rather than internal flags.
- Advanced Settings contains only translation-process controls: automatic terminology extraction, TM reuse, always-on deterministic consistency checks, independent review, and strict terminology governance.
- Step 03 owns style, bilingual output, annotated output, practice report, theory preference, and literature evidence. Report-only fields are conditionally hidden until the report switch is enabled.
- Fonts and typography retain the existing Manrope hierarchy, readable secondary text, and consistent control labels/helpers.
- Spacing and layout retain the 236px sidebar, 932px content region, 8–24px spacing rhythm, 8–10px radii, and border-only elevation.
- Colors and tokens remain white surfaces, neutral borders, international blue interaction state, green completion state, and no error-red selection affordances.
- Image/assets: neither target state requires raster imagery; existing Material Symbols are consistent and no emoji or handcrafted replacement assets were introduced.
- Copy/content matches the backend responsibilities: `重点标注版` is no longer presented as academic case mining, and report/theory copy states its evidence constraint.

### Focused region comparison evidence

- Step 02 Advanced: visible helper text explains each control; `基础一致性检查` is disabled and checked to communicate that it is always active.
- Step 03 Output: `重点标注版` and `实践报告` are independent switches; enabling the latter reveals `理论框架` with `自动推荐（建议）` plus optional literature evidence.
- Step 03 text-area state was specifically recaptured after correcting a dark inherited surface; computed colors are white background (`rgb(255,255,255)`) and primary text (`rgb(17,24,39)`).
- Stepper completion/current nodes remain aligned and semantically consistent across both screens.

### Comparison history

1. P1 — Strategy and output responsibilities were mixed in one effective config.
   - Fix: split `_PRESET_CONFIGS` from `_PRESET_OUTPUTS`, moved annotation/report/theory/literature into Step 03, and made the Step 04 summary derive its workflow from both effective configs.
   - Post-fix evidence: Step 02 DOM contains no output switches; Step 03 DOM contains both output switches and conditionally reveals Theory Framework.
2. P1 — Enabling Practice Report implicitly selected quality mode, document profiling, and terminology freeze behavior.
   - Fix: added the explicit `strict_terminology_governance` pipeline input and removed report-driven mode derivation.
   - Post-fix evidence: the provider/mode regression test completes a report with `profile_done=false` and `quality_mode=false`.
3. P2 — The Step 03 rules text area inherited a dark third-party surface, breaking the established design system.
   - Fix: explicitly applied the shared white surface, primary text, caret, and placeholder tokens to text areas.
   - Post-fix evidence: `tmp/config-refactor-step03-report-final.jpg` and computed-style inspection show the corrected white control.

### Primary interactions and checks

- Browser: expanded Advanced Settings, moved from Step 02 to Step 03, enabled Practice Report, verified conditional Theory Framework and Literature Evidence, checked 1280px desktop overflow, and checked browser console errors (none).
- Automated: Python compile; AppTest Step 01–03 workflow/state coverage; provider/exchange/config semantics; terminology governance; GUI launcher; whitespace diff check.

### Findings

No actionable P0/P1/P2 differences remain against the configuration-model target.

### Follow-up polish

- P3: the CLI option remains named `--quality` for command-line familiarity, but its help and backend mapping now accurately describe strict terminology governance.

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
- Advanced Settings is a white bordered continuation of the workspace, not a black console panel. Its grouped controls use the same blue interaction tokens as the rest of TransPraxis / 译践.

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
   - Post-fix evidence: browser reports `.tp-provider.is-unverified` in the untouched state; AppTest asserts it is not green by default.
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

## TransPraxis sidebar and brand-color refinement — 2026-08-14

- Source visual truth: the user's four-point refinement specification and `tmp/transpraxis-step01-final.png`.
- Implementation screenshots: `tmp/transpraxis-brand-refinement-final.png` and `tmp/transpraxis-brand-refinement-step02.png`.
- Focused before/after comparison: `tmp/brand-qa/sidebar-before-after-refinement.png`.
- Desktop viewport: 1280 × 720 CSS px; narrow-window check: 900 × 720 CSS px.
- State: Step 01 brand shell and Step 02 selected/expanded interaction state.

### Full-view comparison evidence

- Sidebar information architecture and working area remain unchanged; only the brand lockup and semantic interaction colors changed.
- The main CTA now visibly uses TransPraxis deep blue `#062B9A`, selected cards use the same border with `#EEF3FF` tint, and the current workflow node uses source-sampled cyan-blue `#057AFD`.
- Neutral canvas, white surfaces, gray text, success green, and danger red remain semantic and are not recolored as brand decoration.

### Focused region comparison evidence

- The logo slot increased from 46 × 24px to 52 × 27px, and `TransPraxis` increased from 16px to 18px.
- `译践` remains directly below the English name but is reduced to 10.5px and lower weight, keeping the English wordmark as the visual center.
- `Translation Practice Workspace` is retained as requested but reduced to a 9.5px caption with lower contrast.
- Link hover decoration and focus rings use cyan accents; upload hover/focus uses cyan border and soft cyan surface, while text remains deep blue for accessible contrast.

### Responsive and interaction evidence

- At 900px viewport width the page has no horizontal overflow; the sidebar remains 236px, the mark remains 52 × 27px, and the English wordmark remains untruncated.
- Browser-rendered Step 02 confirms the enabled Next button is `rgb(6, 43, 154)`, selected card border is the same deep blue, and the current step node is `rgb(5, 122, 253)`.
- Existing navigation, upload, preset selection, advanced settings, and bottom actions remain functional.

### Findings

No actionable P0/P1/P2 visual differences remain against this refinement target. The subtitle wording is intentionally unchanged; a future copy-positioning change can be evaluated separately.

final result: passed

## Final visual polish — 2026-08-15

- Source visual truth: `/Users/xueyang/.codex/attachments/3bcbdb91-cec9-4afb-a050-3352e1e51c98/goal-objective.md` (37-point final polish spec).
- Implementation screenshots:
  - `tmp/final-polish-2048x1180.png`, `tmp/final-polish-1440x900.png`,
    `tmp/final-polish-1280x800.png`, `tmp/final-polish-1024x768.png`
  - `tmp/final-polish-step02-1280x800.png` (selected card, recommended badge,
    switches, stepper, primary CTA)
  - `tmp/final-polish-expanded-1280x720.png` (verified expanded-state capture
    with the final 44 × 44px square mark)
- Viewport matrix: 2048 × 1180, 1440 × 900, 1280 × 800, 1024 × 768 CSS px.

### Full-view comparison evidence

- Sidebar stays 236px wide with 24px horizontal padding; brand lockup starts
  at y=68 (48px below the sidebar top) with a 44 × 44px square mark,
  18px/700 TransPraxis wordmark, 11px 译践, and an 11px caption subtitle.
- Main content keeps its wide workbench feel: 80px gutters at ≥1440px, 48px at
  1280px, 32px at 1024px, with no horizontal overflow at any tested width.
- Main content top spacing is 72px; page max-width remains 1152px per the
  "沿用当前值" allowance.
- The 60px Streamlit header placeholder is neutralized: the collapse control
  is visible, colored `#7C8799`, and the brand block no longer starts 96px+ down.

### Focused region comparison evidence

- Brand tokens are layered per spec: navy `#001471` (identity), interaction
  blue `#1267E8` / hover `#0D57CE` / active `#0A49B4`, cyan `#09A7FD` limited
  to the upload icon and active step node.
- Stepper rows are 56px with 18px nodes; active label uses `#15379A` at
  600 weight; the active node is cyan `#057AFE`.
- New Task is a 44px white outline button; library rows are 48px with 18px
  icons; provider footer uses 13px/600 provider name, 11px model, blue Manage.
- Selected workflow card: `1.5px solid #4E93F4` on `#F5F9FF`; recommended
  badge `#E7F1FF` on `#1267E8` at 6px radius.
- Toggles render 36 × 20px with a 16px handle; checked state uses `#1267E8`,
  unchecked `#C6CEDA`, with a brand focus ring on keyboard focus.
- Primary CTA is 48px tall, 180px min-width, 9px radius, `#1267E8`; disabled
  state uses `#D9E5F6` on `#8CA2C0` without opacity blur.
- Inputs and selects are 44px with `#DCE2EA` borders and brand focus rings.

### Interaction and responsive evidence

- Step 01 empty state disables Next with the spec'd disabled palette; uploading
  a document enables the primary CTA and switches to the file card.
- Step 02 preset selection, advanced settings toggles, and the enabled Next
  button all render with the interaction-blue family; keyboard focus on
  switches shows the `rgba(18,103,232,.22)` ring.
- Sidebar collapse control is visible at 32 × 32px, colored `#7C8799`, with a
  hover surface. Expanded layout verified at 1280 × 720; the in-app-browser
  sandbox persisted a collapsed sidebar across reloads, so the collapsed
  toggle's expansion interaction is noted as an environment limitation rather
  than an app defect.

### Findings

No actionable P0/P1/P2 visual differences remain against the 37-point spec.
The only residual item is asset format: mark/favicon are high-resolution PNGs
with transparent mark output; formal SVG mark/lockup files are not yet
provided by the brand owner and are noted as follow-up.

final result: passed

## Sidebar brand lockup correction — 2026-08-15

- Source visual truth: user feedback that the sidebar logo was too small and
  `Translation Practice Workspace` was overlapped by the `新建任务` button.
- Root cause: Streamlit injects `margin-bottom: -16px` on every
  `stMarkdownContainer` (its default compensation for paragraph margins). The
  brand block has no paragraph margin, so the container's flow height
  collapsed by 16px and the button was drawn 8px into the subtitle. The logo
  additionally looked small because the square 1024×1024 PNG contained ~62%
  transparent vertical padding, leaving only a ~64 × 27px visible graphic.
- Fix:
  - `transpraxis-mark.png` cropped to its alpha content plus 12px padding
    (now 932 × 414px), so the visible mark fills the element.
  - The mark is displayed at 116 × 52px (previously ~64 × 27px visible).
  - The brand markdown container's negative bottom margin is neutralized with
    `:has(.tp-brand)`, and the brand block adds a 14px bottom margin,
    producing a 22px gap between the subtitle and the New Task button.
  - Sidebar width is pinned to the 236px design token with `!important` so it
    no longer varies by frontend default (300px in some runs).
- Measured in headless Chrome (1600 and 1024 CSS px viewports): mark
  116 × 52px centered, subtitle 136–150px, button top at 172px (22px clear
  gap, no overlap), document scroll width equals the viewport (no overflow).
- Existing AppTest boot, GUI launcher, and core smoke suites all pass.

final result: passed

## Bottom action bar clearance and spacing tightening — 2026-08-15

- Source visual truth: user feedback that the fixed bottom action bar covered
  the `术语库` helper text and `添加术语库` button on Step 01.
- Root cause: the fixed bar (67px) sat at `bottom: 0` while the scrollable
  `stMain` container only reserved 64px (`4rem`) of bottom padding; at full
  scroll the last real content fell into the bar's overlay band.
- Fix (desktop keeps `position: fixed`, per spec):
  - New token `--action-bar-height: 80px`; the bar now has `min-height: 80px`,
    `padding: 15px 0`, `border-top: #E3E8EF`, `background: rgba(247,248,250,.96)`
    and `backdrop-filter: blur(8px)`.
  - `stMainBlockContainer` bottom padding changed from `4rem` to
    `calc(var(--action-bar-height) + 40px)` (120px), so no form content can be
    hidden behind the bar at any viewport size.
  - Brand lockup tightened: mark-to-wordmark gap reduced from 10px to 4px.
  - Page title to first section spacing set to 36px.
- Measured in headless Chrome (1280 × 720 and 1024 × 768 CSS px): bar height
  80px, main bottom padding 120px, and after full scroll the termbase section
  clears the bar by 56px; title-to-section gap is 36px; no horizontal
  overflow at either width.
- Existing AppTest boot suite still passes.

final result: passed

## Action bar moved into document flow (sticky) — 2026-08-15

- Source visual truth: follow-up requirement that the bottom action bar must
  never cover form content, resolved at the layout layer rather than by
  section margins; `fixed` was to be replaced where architecture allows.
- Root cause recap: the bar was `position: fixed; bottom: 0` and floated over
  the scroll container (`stMain`); content could only clear it via a manual
  bottom-padding compensation, which is easy to break and does not express the
  intended layout.
- Change: the bar's flow wrapper (the `stLayoutWrapper` containing
  `st-key-task_action_bar`) is now `position: sticky; bottom: 0; z-index: 20`.
  Sticky must sit on that wrapper, not on the bar itself: the bar's own
  containing block is only ~128px tall, which would prevent it from being
  pulled up to the scrollport bottom. With the wrapper sticky, the bar
  participates in document flow, docks at the bottom while scrolling, and
  rests at its natural position at full scroll — nothing is ever hidden at
  rest. The bar keeps its 80px min-height, 48px rest gap (`margin-top` on the
  bar), `#E3E8EF` top border, 96%-canvas background, and 8px backdrop blur.
- The main container's bottom padding is reduced to a normal 40px (no
  fixed-footer compensation needed anymore); non-step pages (settings,
  history, workspace) are unaffected and have no bar.
- Verified in headless Chrome at 2048 × 1180, 1440 × 900, 1280 × 800,
  1024 × 768, and 480 × 800: after full scroll the last form section clears
  the bar by 64px (≥ 32px required), the bar is visible and operable at every
  scroll position, `stMain` remains the only scroll container (no double
  scrollbars), the sidebar is untouched, and there is no horizontal overflow.
- Step 02 (presets + advanced settings) and the Settings page were also
  checked with a real uploaded file; both are clean.
- Existing AppTest boot and GUI launcher suites pass.

final result: passed

## Step 02 preset card hierarchy and hit-area fix — 2026-08-15

- Source visual truth: user spec defining a four-level visual hierarchy for the
  three workflow preset cards (title / summary / flow / meta) with exact type
  sizes, spacing rhythm (12 / 8 / 6), and distinct selected vs. hover states.
- Changes in `app.py`:
  - Cards are content-height (fixed 160px removed), `padding: 18px 18px 16px`,
    radius 12px, unselected `#DCE2EA` border on white, hover `#C5D1E0` on
    `#FBFCFE`, selected 1.5px `#4E93F4` on `#F7FBFF`.
  - Title 16px/700 `#172033` (selected `#15379A`); summary 14px/400 `#667085`;
    flow 15px/600 `#24324A` (selected `#1E2F4D`); meta 13px/400 `#8A94A6`.
    Summary and meta stay neutral in the selected state.
  - Badge is a pill (`999px`, `#EAF2FF` on `#1267E8`) pushed to the header end.
  - Card-internal rules use `.tp-preset-card .tp-preset-*` selectors with
    `!important` on flow/meta font sizes, because Streamlit's
    `[data-testid="stMarkdownContainer"] p` rule zeroes `margin-top` and the
    global `p { font-size: 14px !important }` rule would flatten the hierarchy.
  - Equal heights: the stretched `stColumn` chain is made flex so every card
    fills its column, and the hidden preset-button container is excluded from
    flex-grow so all three cards match even when the academic flow wraps on
    narrow viewports.
  - Hit-area fix: Streamlit gives the button's `stElementContainer` a default
    `position: relative`, which made the absolute transparent overlay button
    use that 16 × 22px container as its containing block — the card was only
    clickable on a thin strip at its left edge. The container is set to
    `position: static`, so the overlay covers the entire card. Verified by
    real mouse clicks on the card center selecting 快速 / 标准.
- Measured in headless Chrome: at 1440 × 900 all three cards are 131px tall
  with 12 / 8 / 6px gaps; at 1024 × 768 (where the academic flow wraps to two
  lines) all three cards are 173px and equal; hover state applies the spec'd
  colors; no horizontal overflow.
- Existing AppTest boot suite passes.

final result: passed

## Step 02 preset cards: fixed four-slot grid + tag metadata — 2026-08-16

- Source visual truth: user spec replacing the flexible card layout with a
  fixed four-slot structure (header / two-line summary / two-line workflow /
  compact tags) so the three cards can be compared row by row, and replacing
  the long gray metadata sentence with two pill tags.
- Changes:
  - `.tp-preset-card` is now a CSS grid: `min-height: 182px`,
    `padding: 20px 20px 18px`, `grid-template-rows: auto 44px 46px auto`,
    `row-gap: 8px`. All `p` margins are zeroed; the grid gap owns the rhythm,
    and the summary/flow rows are fixed two-line slots (44px / 46px) so rows
    align horizontally across all three cards at every width.
  - Header row is fixed at 22px (`min-height` on `.tp-preset-head`): the
    `推荐` badge is ~22px tall, and without the fixed row the selected card
    was 2px taller than its siblings, breaking row alignment.
  - All cards use the same 1.5px border width (selected card only changes the
    border color), so border-box outer heights are identical; `height: 100%`
    was removed from the card so the grid sizes to its content instead of
    collapsing to `min-height` and squeezing the tag row against the bottom.
  - Metadata is now two pill tags (`.tp-preset-tag`): 3px 8px padding, 6px
    radius, `#F1F4F8` on `#667085`, 11px/500; the selected card tints them
    `#EAF2FF` on `#3C67A8` only.
  - Copy normalized per spec: 快速 `快速生成可读初稿` + `最快 / 成本最低`;
    标准 `兼顾质量与效率` + `术语更一致 / 成本适中`; 学术增强
    `为 MTI 实践报告保留完整证据` + `证据最完整 / 耗时较长`.
- Measured in headless Chrome (1440 × 900, 1024 × 768, 480 × 800): all three
  cards are 198px tall with identical title / summary / flow / tag row
  positions; the tag row keeps ~19px of bottom breathing room; the academic
  flow wraps to two lines inside its fixed 46px slot at 1024 without overflow;
  no horizontal overflow; whole-card click still selects the preset.
- AppTest boot suite updated for the new copy and tag markup, and passes;
  core smoke suite passes.

final result: passed

## Step 02 refinement: academic copy, tag contrast, advanced row, spacing — 2026-08-16

- Source visual truth: four-point user feedback (academic summary wording, tag
  contrast, the collapsed advanced-settings summary being noise, and vertical
  spacing between the page title and the preset cards).
- Changes:
  - 学术增强 summary now reads `适合需要完整过程证据的任务`.
  - Chips are slightly stronger: `padding: 4px 9px`, `background: #EEF1F5`,
    `color: #5F6B7A` (was 3px 8px / #F1F4F8 / #667085); the selected card
    keeps the `#EAF2FF` / `#3C67A8` tint.
  - The collapsed 高级设置 row no longer renders the right-side config
    summary (`术语治理 · 翻译记忆 · 独立审校 · 基础检查`); only the
    left-aligned `高级设置` trigger remains. The now-unused
    `_strategy_summary()` helper and its CSS were removed.
  - Vertical rhythm tightened: `.tp-title` bottom margin 36 → 24px,
    `.tp-section-sub` bottom margin 24 → 16px, preset-card row top margin
    8 → 0. Measured title-to-section gap is 24px (was 36px).
- Verified in headless Chrome at 1440 × 900: new copy on the academic card,
  4px 9px chips in `#EEF1F5`/`#5F6B7A`, advanced trigger text is only
  `高级设置`, and the tightened title/section/card stack.
- AppTest boot suite updated (new academic copy; collapsed summary must be
  absent) and passes; core smoke suite passes.

final result: passed

## Expanded 高级设置 panel: hierarchy and rhythm — 2026-08-16

- Source visual truth: user spec requiring a professional settings surface —
  separated context line, three visible groups, per-setting visual units,
  aligned toggles, an always-on badge attached to its title, and a
  640px text-column cap. No control semantics or markup structure changed.
- Changes in `app.py` (CSS only, plus no code changes):
  - Panel body: `padding: 20px 24px 24px`, `gap: 0`, and Streamlit's default
    `-16px` markdown-container margin is neutralized inside the panel so the
    declared rhythm renders exactly (previously the context line and group
    titles could visually collide with the next row).
  - Context line (`当前使用「…」默认配置`): 12px/400 `#7C8799`,
    `margin-bottom: 22px`.
  - Group titles: 12px/600 `#6F7B8D` with `letter-spacing: 0.01em`;
    `margin: 24px 0 10px` (first group 0 top margin).
  - Setting rows: `min-height: 62px`, content vertically centered; rows are
    separated by a 1px `#F0F2F5` divider with 14px breathing space (divider
    rules operate on the row wrappers, and the readonly row participates too).
  - Row layout is a grid: `minmax(0, 640px) minmax(48px, auto)` with
    `column-gap: 32px`; text column capped at 640px; toggle column is a
    right-aligned 48px+ column (Streamlit's testid is `stColumn`, and the
    checkbox chain is forced to fill the column so switches align).
  - Title 14px/600 `#202A3A`; description 12.5px/400 `#7A8699` with 4px top
    margin and 1.55 line height.
  - Always-on badge: pill `#EAF8F0` on `#1F8A57`, 10.5px/600, in the same
    flex line as the title (8px gap).
- Measured in headless Chrome at 1440 × 900: context→group 22px, group→first
  setting 10px, row-to-row 15px (14px padding + 1px divider), group-to-group
  24px, rows 62px, switches right-aligned at the panel content edge and
  vertically centered (delta 0), badge inline with the title; toggle clicks
  still flip state.
- AppTest boot suite and core smoke suite pass.

final result: passed

## Quick Profiling + style recommendation + deliverables — 2026-08-16

- Source visual truth: user spec converting the new-task flow into
  `01 文档与画像 / 02 翻译策略 / 03 交付内容 / 04 确认运行`, with a
  lightweight Quick Profiling step that recommends a style from predefined
  profiles (never free-form), a user-override path, versioned profile
  artifacts, and a deliverables-only Step 03.
- New module `transpraxis/style_profile.py`:
  - Seven predefined profiles (academic / technical / professional / literary
    / legal / publicity / general) with Chinese display names, parameter maps,
    and translation rule texts; `profile_to_rules()` renders the selected
    profile (plus 0-100 micro-adjustments) into the pipeline's `style_rules`;
    `style_profile_id()` returns a stable sha256-based version ID.
  - `quick_profile()` reuses `document_profile.distributed_sample` (首/中/尾
    3000-6000 chars), makes a single strict-JSON LLM call returning
    `{document_profile, style_recommendation}`, normalizes both (unknown
    styles clamp to `general`), and degrades deterministically on any failure
    (general + 0 confidence + warning) - never fabricates a recommendation.
- `core.py`: `extract_document_paragraphs()` (PDF text layer, scanned-PDF OCR
  on representative pages via tesseract when available, DOCX via python-docx)
  and `write_profile_artifacts()` (document_profile.json / style_profile.json
  with `style_profile_id` in the job dir).
- Step 01: after upload the page shows a `智能风格建议` card; `开始智能画像`
  runs the quick profile, then the card shows the recommended style name,
  confidence, summary tags, 检测依据 reasons, and `接受推荐 / 调整 / 查看分析`.
  `调整` opens a 7-option base-style radio + 4 sliders (表达正式度 / 术语保守
  程度 / 句法重构幅度 / 原文形式保留) + optional custom rules; selections are
  recorded as `accepted` or `user_override`, and the choice feeds
  `style_rules` / `style_template` used by the pipeline and Step 04 summary.
- Step 03 is now deliverables only: 译文 (纯译文 / 双语对照 DOCX checkboxes,
  PDF preference, 重点标注版 toggle), 语言资产 (术语表 XLSX / TBX / TMX /
  JSONL checkboxes), 研究资产 (实践报告 toggle + 理论框架 + 过程证据 / 案例
  候选 / 学术写作工作区 / 审校报告 checkboxes when report is on). The style
  dropdown is removed from Step 03.
- Run flow: Step-01 profile artifacts are written to the job dir before the
  pipeline, and a non-empty document profile is injected into the job state so
  the strict-governance stage reuses it instead of re-profiling.
- Verified in headless Chrome with a real DOCX: idle card -> quick profile
  (fallback path without API key shows 通用 0% + warning) -> adjust panel
  (7 radios + 4 sliders) -> apply records `user_override` and the card shows
  `已使用用户选择覆盖系统建议`; Step 03 groups and checkboxes render; Step 04
  summary shows `译文风格 通用（用户调整）` and the selected deliverables.
- Tests: AppTest updated (new step names, style-flow fallback assertions,
  deliverables checkboxes, style dropdown absence); new
  `tests/style_profile_test.py` covers profile closure, normalization,
  deterministic fallback, rules/ID stability, and artifact writing. AppTest,
  style profile, smoke, GUI launcher, terminology governance, and red-team
  acceptance suites all pass.

final result: passed

## API 配置跨页丢失 + 首次使用引导 — 2026-08-16

- Reported bug: after entering the API key and choosing a model on the AI
  engine page, switching pages reverted the model to the default and emptied
  the key; there was no explicit save button because the values were expected
  to persist via widget keys.
- Root cause: Streamlit 1.61 removes state for keyed widgets that are not
  rendered in a script run ("stale widget cleanup"). All main views are
  rendered inside one `st.empty()` container, so navigating between views
  unmounts the previous view's widgets and their session state is dropped at
  the end of the run unless the widget opts into persistence. This also
  affected 目标语言 and every other keyed configuration widget (deliverable
  checkboxes, strategy toggles, style sliders, theory select).
- Fix: added `persist_state="session"` to all configuration widgets that must
  survive page/step switches: provider/model/API-key/base-url on the settings
  page, 目标语言 and the style-adjust radio/sliders/text area on Step 01, the
  strategy toggles on Step 02, and all deliverable checkboxes/toggles plus the
  theory select on Step 03. Verified in AppTest and in the live browser: model
  and API key now survive navigation and come back with their values.
- First-run onboarding: `core.is_onboarded()/mark_onboarded()` use a marker
  file (`outputs/.onboarded`); the new-task page shows a three-step guide card
  (选择服务商 → 填写 API 密钥与模型 → 测试连接) with 前往设置 / 暂不配置
  actions while the marker is absent and no key is configured; a successful
  测试连接 writes the marker so the guide never reappears. The settings page
  shows the same hint while not onboarded.
- AppTest extended with a persistence regression check (model + key survive
  settings → new-task → settings); all suites pass in both `.venv` and `venv`.

final result: passed

## 智能风格建议：运行进度 UI — 2026-08-17

- Reported issue: clicking 开始智能画像 ran the profile inside the button
  callback, so the frontend received no updates while the LLM call executed
  and the page appeared frozen/blank.
- Fix: the profile now runs inside the script run (button only sets a
  `running` state and falls through), wrapped in `st.status` with progressive
  step labels: 正在提取文档文本… → 正在抽取首/中/尾样本并分析文体… →
  风格建议已生成（或 未配置 AI 引擎，请手动选择风格）. The result card
  renders in the same run after the status completes, so there is no dead
  time between progress and result.
- Verified in the live browser by sampling the DOM after the click: the
  `stStatusWidget` element is present during the run (80–200ms samples) and
  the result card replaces it on completion; a minimal repro app confirmed
  the status widget stays visible for the whole duration of a slow run and is
  removed only when the script run ends (frontend behavior of this Streamlit
  version).
- AppTest extended: the 开始智能画像 interaction must produce a status
  element; all suites pass in both `.venv` and `venv`.

final result: passed

## API 配置保存按钮 + 画像降级引导 — 2026-08-17

- User request: add an explicit save action to the AI engine settings page,
  and show 前往配置 API Key / 重试 actions on the style-recommendation
  fallback result (`未配置 AI 引擎，无法自动画像`).
- API config persistence:
  - `core.save_provider_config()` / `core.load_provider_config()` write/read
    `outputs/provider_config.json` (chmod 0600) with provider, model, api_key
    and base_url.
  - The settings page now shows 保存配置 (secondary) next to 测试连接
    (primary), both disabled until a key and model are present; saving shows a
    toast. App startup seeds provider/model/key/base-url from the saved file
    when the session has no values yet, so the configuration survives app
    restarts without re-entering the key.
- Style recommendation fallback:
  - The no-key path sets `style_profiling_needs_api`; the result card then
    renders 前往配置 API Key (primary, jumps to settings), 重试 (re-runs the
    profiling with the progress status) and 调整 (manual style pick) instead
    of the accept/analysis row. The flag is cleared on a successful profile
    run and when the source file is removed.
  - Fixed a double-card artifact: on the click run the idle card was rendered
    before the fall-through, leaving two stacked cards; the idle card is now
    skipped when the button was clicked.
- Verified in the live browser: fallback card shows exactly one card with the
  three actions; settings page shows both buttons (disabled without key);
  AppTest covers 重试 → still fallback, 前往配置 API Key → settings page, and
  保存配置 → provider_config.json round-trip. All suites pass in `.venv` and
  `venv`.

final result: passed
