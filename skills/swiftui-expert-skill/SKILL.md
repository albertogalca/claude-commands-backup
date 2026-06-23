---
name: swiftui-expert-skill
description: Write, review, and improve idiomatic SwiftUI code following Apple's latest architectural recommendations and best practices for state management, view composition, performance, accessibility, macOS and iOS APIs, and iOS 26+ Liquid Glass adoption. Use when building new SwiftUI features, refactoring existing views, reviewing code quality, or adopting modern SwiftUI/Swift 6 patterns on any Apple platform (iOS, macOS, watchOS, tvOS).
---

# SwiftUI Expert Skill

## Operating Rules

- Consult `references/latest-apis.md` at the start of every task to avoid deprecated APIs
- Prefer native SwiftUI APIs over UIKit/AppKit bridging unless bridging is necessary
- Focus on correctness and performance; do not enforce specific architectures (MVVM, VIPER, etc.)
- Encourage separating business logic from views for testability without mandating how
- Follow Apple's Human Interface Guidelines and API design patterns
- Only adopt Liquid Glass when explicitly requested by the user (see `references/liquid-glass.md`)
- Present performance optimizations as suggestions, not requirements
- Use `#available` gating with sensible fallbacks for version-specific APIs

## Writing idiomatic SwiftUI

Write SwiftUI that looks and feels like SwiftUI. The framework has matured -- trust its patterns and don't fight its update mechanism.

- SwiftUI is the default UI paradigm; embrace its declarative nature and let it handle the complexity
- State flows down, actions flow up; keep state as close to where it's used as possible
- Use property wrappers as Apple intends: `@State` (local/ephemeral), `@Binding` (two-way), `@Observable` (shared, iOS 17+), `@Environment` (app-wide dependency injection)
- Extract shared state only when multiple views actually need it
- Default to `async/await`; use the `.task` modifier for lifecycle-aware async work; avoid Combine unless necessary
- Handle loading and error states explicitly (e.g. `isLoading` / `error` / content branches)
- Organize by feature, not by type (avoid blanket `Views/` `Models/` `ViewModels/` folders); break distinct types into separate files
- Use extensions to organize large files; build UI from small, focused, composable views

**DON'T:** create a ViewModel for every view, move state out of views unnecessarily, add abstraction layers without clear benefit, use Combine for simple async, or overcomplicate simple features.

```swift
// Shared state with @Observable (iOS 17+)
@Observable
class UserSession {
    var isAuthenticated = false
    var currentUser: User?
}

struct MyApp: App {
    @State private var session = UserSession()
    var body: some Scene {
        WindowGroup {
            ContentView().environment(session)
        }
    }
}
```

```swift
// Async data loading with explicit loading/error states
struct ProfileView: View {
    @State private var profile: Profile?
    @State private var isLoading = false
    @State private var error: Error?

    var body: some View {
        Group {
            if isLoading { ProgressView() }
            else if let profile { ProfileContent(profile: profile) }
            else if let error { ErrorView(error: error) }
        }
        .task { await loadProfile() }
    }

    private func loadProfile() async {
        isLoading = true
        defer { isLoading = false }
        do { profile = try await ProfileService.fetch() }
        catch { self.error = error }
    }
}
```

## Task Workflow

### Review existing SwiftUI code
- Read the code under review and identify which topics apply
- Flag deprecated APIs (compare against `references/latest-apis.md`)
- Run the Topic Router below for each relevant topic
- Validate `#available` gating and fallback paths for iOS 26+ features

### Improve existing SwiftUI code
- Audit current implementation against the Topic Router topics
- Replace deprecated APIs with modern equivalents from `references/latest-apis.md`
- Refactor hot paths to reduce unnecessary state updates
- Extract complex view bodies into separate subviews
- Suggest image downsampling when `UIImage(data:)` is encountered (optional optimization, see `references/image-optimization.md`)

### Implement new SwiftUI feature
- Design data flow first: identify owned vs injected state
- Structure views for optimal diffing (extract subviews early)
- Apply correct animation patterns (implicit vs explicit, transitions)
- Use `Button` for all tappable elements; add accessibility grouping and labels
- Gate version-specific APIs with `#available` and provide fallbacks

### Topic Router

Consult the reference file for each topic relevant to the current task:

| Topic | Reference |
|-------|-----------|
| State management | `references/state-management.md` |
| View composition | `references/view-structure.md` |
| Performance | `references/performance-patterns.md` |
| Lists and ForEach | `references/list-patterns.md` |
| Layout | `references/layout-best-practices.md` |
| Sheets and navigation | `references/sheet-navigation-patterns.md` |
| ScrollView | `references/scroll-patterns.md` |
| Focus management | `references/focus-patterns.md` |
| Animations (basics) | `references/animation-basics.md` |
| Animations (transitions) | `references/animation-transitions.md` |
| Animations (advanced) | `references/animation-advanced.md` |
| Accessibility | `references/accessibility-patterns.md` |
| Swift Charts | `references/charts.md` |
| Charts accessibility | `references/charts-accessibility.md` |
| Image optimization | `references/image-optimization.md` |
| Liquid Glass (iOS 26+) | `references/liquid-glass.md` |
| macOS scenes | `references/macos-scenes.md` |
| macOS window styling | `references/macos-window-styling.md` |
| macOS views | `references/macos-views.md` |
| Deprecated API lookup | `references/latest-apis.md` |

## Correctness Checklist

These are hard rules -- violations are always bugs:

- [ ] `@State` properties are `private`
- [ ] `@Binding` only where a child modifies parent state
- [ ] Passed values never declared as `@State` or `@StateObject` (they ignore updates)
- [ ] `@StateObject` for view-owned objects; `@ObservedObject` for injected
- [ ] iOS 17+: `@State` with `@Observable`; `@Bindable` for injected observables needing bindings
- [ ] `ForEach` uses stable identity (never `.indices` for dynamic content)
- [ ] Constant number of views per `ForEach` element
- [ ] `.animation(_:value:)` always includes the `value` parameter
- [ ] `@FocusState` properties are `private`
- [ ] No redundant `@FocusState` writes inside tap gesture handlers on `.focusable()` views
- [ ] iOS 26+ APIs gated with `#available` and fallback provided
- [ ] `import Charts` present in files using chart types

## Review checklist

When reviewing SwiftUI code, walk these checks in order, loading only the relevant reference files for a partial review. Report only genuine problems -- do not nitpick or invent issues.

1. Deprecated API -- compare against `references/latest-apis.md` (e.g. `foregroundColor()` -> `foregroundStyle()`)
2. Views, modifiers, and animations written optimally -- `references/view-structure.md`, `references/performance-patterns.md`, animation references
3. Data flow configured correctly (property wrappers, ownership) -- `references/state-management.md`; flag fragile `Binding(get:set:)` in view bodies (prefer `@State` + `.onChange`)
4. Navigation updated and performant (`NavigationStack`/`NavigationSplitView`, sheets, dialogs) -- `references/sheet-navigation-patterns.md`
5. Accessibility and HIG compliance -- Dynamic Type, VoiceOver, Reduce Motion, labeled controls -- `references/accessibility-patterns.md` (icon-only buttons need a text label)
6. Performance -- hot paths and unnecessary updates -- `references/performance-patterns.md`
7. Swift correctness and concurrency (target Swift 6.2+, modern concurrency) -- run against the Correctness Checklist above
8. Code hygiene -- one primary type per file, feature-based structure, no unrequested third-party frameworks

### Review output format

Organize findings by file; skip files with no issues. For each issue: state the file and line(s), name the rule being violated, and show a brief before/after fix. End with a prioritized summary (highest-impact first), tagged by severity.

```swift
// Line 24: Icon-only button is invisible to VoiceOver -- add a text label.
// Before
Button(action: addUser) { Image(systemName: "plus") }
// After
Button("Add User", systemImage: "plus", action: addUser)
```

## References

- `references/latest-apis.md` -- **Read first for every task.** Deprecated-to-modern API transitions (iOS 15+ through iOS 26+)
- `references/state-management.md` -- Property wrappers, data flow, `@Observable` migration
- `references/view-structure.md` -- View extraction, container patterns, `@ViewBuilder`
- `references/performance-patterns.md` -- Hot-path optimization, update control, `_logChanges()`
- `references/list-patterns.md` -- ForEach identity, Table (iOS 16+), inline filtering pitfalls
- `references/layout-best-practices.md` -- Layout patterns, GeometryReader alternatives
- `references/accessibility-patterns.md` -- VoiceOver, Dynamic Type, grouping, traits
- `references/animation-basics.md` -- Implicit/explicit animations, timing, performance
- `references/animation-transitions.md` -- View transitions, `matchedGeometryEffect`, `Animatable`
- `references/animation-advanced.md` -- Phase/keyframe animations (iOS 17+), `@Animatable` macro (iOS 26+)
- `references/charts.md` -- Swift Charts marks, axes, selection, styling, Chart3D (iOS 26+)
- `references/charts-accessibility.md` -- Charts VoiceOver, Audio Graph, fallback strategies
- `references/sheet-navigation-patterns.md` -- Sheets, NavigationSplitView, Inspector
- `references/scroll-patterns.md` -- ScrollViewReader, programmatic scrolling
- `references/focus-patterns.md` -- Focus state, focusable views, focused values, default focus, common pitfalls
- `references/image-optimization.md` -- AsyncImage, downsampling, caching
- `references/liquid-glass.md` -- iOS 26+ Liquid Glass effects and fallback patterns
- `references/macos-scenes.md` -- Settings, MenuBarExtra, WindowGroup, multi-window
- `references/macos-window-styling.md` -- Toolbar styles, window sizing, Commands
- `references/macos-views.md` -- HSplitView, Table, PasteButton, AppKit interop
