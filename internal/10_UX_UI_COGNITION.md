# 10 — UX/UI Cognition (Phase 4 — Planned)

🔵 **ยังไม่ implemented** — เอกสารนี้เป็น spec

## ทำไมต้องมี

AI gen UI ปัจจุบัน → modal style ไม่ตรง design system, spacing arbitrary, dark mode พัง

**Insight:** UI consistency = product trust. AI breaking design system = product looks amateur

## สิ่งที่ต้อง detect

### Design tokens

- Color palette (Tailwind config, CSS vars)
- Spacing scale (4/8/16/24 vs arbitrary)
- Font sizes (xs/sm/base/lg/xl scale)
- Border radius scale
- Shadow scale

### Component patterns

- Modal: `<Dialog>` raw หรือ `<Sheet>` from shared/ui?
- Form: react-hook-form + zod? formik? plain useState?
- Table: TanStack? raw `<table>`? ag-grid?
- Toast/Notification: sonner? react-hot-toast? custom?
- Date picker: react-day-picker? mui? native?

### Layout patterns

- Page structure (header/sidebar/content)
- Grid system (CSS grid vs flex vs container queries)
- Responsive breakpoints

### Interaction patterns

- Loading states (skeleton vs spinner vs progress)
- Empty states (illustration + CTA)
- Error states (inline vs toast vs page)
- Confirmation (modal vs inline vs toast undo)

### Dark mode

- class-based (`next-themes`) vs media query
- Token approach (CSS vars vs Tailwind `dark:`)

### Animation

- Library (framer-motion / motion / CSS only)
- Common durations / easings

## Implementation plan

```text
src/knowlyx/design/
  scanner.py           — scan tailwind.config, theme files, shared/ui
  token_extractor.py   — extract design tokens
  pattern_detector.py  — detect modal/form/table patterns
  enforcer.py          — return violations for gen'd code
```

## New MCP tools

| Tool | use |
| --- | --- |
| `get_design_system(repo_path)` | tokens + components + patterns |
| `validate_ui_code(code, repo_path)` | check violations before write |
| `get_design_patterns(component_type, repo_path)` | how this team builds modals/forms/etc |

## Real-world usage (planned)

**Scenario:** Dev ขอ "create settings page"

```text
[Claude]
1. tool: get_design_system("/path/to/web")
   ← spacing: 4/8/16/24 scale only
   ← page layout: <AppShell> wrapper required
   ← form: react-hook-form + zod (NOT formik, NOT plain state)
   ← button: <Button variant="primary"> (NOT custom)
   ← input: <Input> from @/components/ui/input
   ← dark mode: class-based via next-themes

2. tool: get_reusable_assets("settings")
   ← SettingsLayout component exists
   ← useUpdateProfile mutation hook exists

3. Writes:
   <AppShell>
     <SettingsLayout>
       <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
         <Input {...register("name")} />
         <Button variant="primary" type="submit">Save</Button>
       </form>
     </SettingsLayout>
   </AppShell>

[Validation pre-write]
4. tool: validate_ui_code(<above>, "/path/to/web")
   ← ✅ uses AppShell + SettingsLayout
   ← ✅ uses Button variant
   ← ✅ spacing in scale (space-y-6 = 24px)
   ← ✅ react-hook-form + Input pattern
```

→ First-try UI ตรง design system, no rework
