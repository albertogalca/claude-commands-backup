---
name: frontend-dev-guidelines
description: Frontend development guidelines for Inertia.js + Laravel + React/TypeScript applications. Modern patterns including Tailwind CSS v4, Inertia routing, server-side props, lazy loading, file organization, performance optimization, and TypeScript best practices. Use when creating components, pages, features, styling, routing, or working with frontend code.
---

# Frontend Development Guidelines

## Purpose

Comprehensive guide for Inertia.js + Laravel + React development with Tailwind CSS v4, emphasizing server-side rendering, proper file organization, and performance optimization.

## When to Use This Skill

- Creating new Inertia pages or components
- Building new features
- Working with Inertia props and forms
- Setting up routing with Laravel routes + Inertia
- Styling components with Tailwind CSS v4
- Performance optimization
- Organizing frontend code
- TypeScript best practices

---

## Quick Start

### New Component Checklist

Creating a component? Follow this checklist:

- [ ] Use `React.FC<Props>` pattern with TypeScript
- [ ] Lazy load if heavy component: `React.lazy(() => import())`
- [ ] Use Tailwind CSS classes for styling
- [ ] Extract complex styles to component classes or CSS
- [ ] Use `useCallback` for event handlers passed to children
- [ ] Default export at bottom
- [ ] Use `cn()` utility for conditional classes
- [ ] Follow Tailwind v4 best practices

### New Inertia Page Checklist

Creating an Inertia page? Follow this checklist:

- [ ] Create Laravel route in `routes/web.php`
- [ ] Return Inertia response from controller: `Inertia::render('PageName', $props)`
- [ ] Create page component in `resources/js/Pages/`
- [ ] Type Inertia props with TypeScript interface
- [ ] Use `useForm` for forms with validation
- [ ] Use `router.visit()` or `Link` component for navigation
- [ ] Lazy load heavy components within the page
- [ ] Handle loading states with Inertia progress indicators

---

## Import Aliases Quick Reference

| Alias | Resolves To | Example |
|-------|-------------|---------|
| `@/` | `resources/js/` | `import { cn } from '@/lib/utils'` |
| `@/Components` | `resources/js/Components` | `import { Button } from '@/Components/Button'` |
| `@/Pages` | `resources/js/Pages` | `import Dashboard from '@/Pages/Dashboard'` |
| `@/types` | `resources/js/types` | `import type { User } from '@/types'` |

Defined in: `tsconfig.json` or `vite.config.ts`

---

## Common Imports Cheatsheet

```typescript
// React & Lazy Loading
import React, { useState, useCallback, useMemo } from 'react';
const Heavy = React.lazy(() => import('./Heavy'));

// Inertia.js
import { Head, Link, router, useForm } from '@inertiajs/react';
import type { PageProps } from '@/types';

// Tailwind Utilities
import { cn } from '@/lib/utils'; // classnames utility

// Project Components
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';
import { Card, CardHeader, CardContent } from '@/Components/ui/card';

// Layouts
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';

// Types
import type { User, Post } from '@/types';
```

---

## Topic Guides

### 🎨 Component Patterns

**Modern React components use:**
- `React.FC<Props>` for type safety
- `React.lazy()` for code splitting heavy components
- Tailwind CSS classes for styling
- Named const + default export pattern

**Key Concepts:**
- Lazy load heavy components (DataGrid, charts, editors)
- Use `cn()` utility for conditional class names
- Component structure: Props → Hooks → Handlers → Render → Export
- Keep components focused and composable

**[📖 Complete Guide: resources/component-patterns.md](resources/component-patterns.md)**

---

### 📊 Data Fetching with Inertia

**PRIMARY PATTERN: Server-Side Props**
- Data passed from Laravel controller via Inertia props
- Type-safe with TypeScript interfaces
- No client-side data fetching needed for initial render
- Use `usePage<PageProps>()` to access shared props

**Controller Example:**
```php
return Inertia::render('Posts/Index', [
    'posts' => Post::with('author')->paginate(10),
    'filters' => $request->only(['search', 'status']),
]);
```

**Page Component:**
```typescript
interface Props {
    posts: PaginatedData<Post>;
    filters: { search?: string; status?: string };
}

export default function Index({ posts, filters }: Props) {
    // Data is already available, no loading state needed
}
```

**[📖 Complete Guide: resources/data-fetching.md](resources/data-fetching.md)**

---

### 📁 File Organization

**Inertia/Laravel Structure:**
```
resources/js/
  Pages/           # Inertia page components
  Components/      # Reusable UI components
  Layouts/         # Layout components
  types/           # TypeScript types
  lib/             # Utilities and helpers
```

**Page Organization:**
- Group related pages in subdirectories (`Pages/Posts/`, `Pages/Users/`)
- Keep page-specific components in same directory
- Extract truly reusable components to `Components/`

**[📖 Complete Guide: resources/file-organization.md](resources/file-organization.md)**

---

### 🎨 Styling with Tailwind CSS v4

**Primary Method: Utility Classes**
```typescript
<div className="flex items-center gap-4 rounded-lg bg-white p-6 shadow-sm">
  <Button className="bg-primary text-white hover:bg-primary/90">
    Click me
  </Button>
</div>
```

**Conditional Classes with `cn()`:**
```typescript
import { cn } from '@/lib/utils';

<div className={cn(
  "base-classes",
  isActive && "active-classes",
  variant === "primary" && "primary-classes"
)} />
```

**Custom Components:**
```typescript
// Extract to component when reused
export function Card({ className, children, ...props }) {
  return (
    <div
      className={cn("rounded-lg border bg-card p-6", className)}
      {...props}
    >
      {children}
    </div>
  );
}
```

**[📖 Complete Guide: resources/styling-guide.md](resources/styling-guide.md)**

---

### 🛣️ Routing with Inertia

**Laravel Routes + Inertia:**
```php
// routes/web.php
Route::get('/posts', [PostController::class, 'index'])->name('posts.index');
Route::get('/posts/{post}', [PostController::class, 'show'])->name('posts.show');
```

**Navigation with Link Component:**
```typescript
import { Link } from '@inertiajs/react';

<Link href="/posts" className="text-blue-600 hover:underline">
  View Posts
</Link>

// Or with route helper
<Link href={route('posts.show', post.id)}>View Post</Link>
```

**Programmatic Navigation:**
```typescript
import { router } from '@inertiajs/react';

router.visit('/posts');
router.get('/posts', { search: 'query' });
router.post('/posts', data);
```

**[📖 Complete Guide: resources/routing-guide.md](resources/routing-guide.md)**

---

### ⏳ Loading & Error States

**Inertia Progress Indicator:**
```typescript
// Inertia automatically shows progress bar for navigation
// Configure in app.tsx/jsx
import { router } from '@inertiajs/react';
import NProgress from 'nprogress';

router.on('start', () => NProgress.start());
router.on('finish', () => NProgress.done());
```

**Form Loading States:**
```typescript
import { useForm } from '@inertiajs/react';

const { data, setData, post, processing, errors } = useForm({
    name: '',
    email: '',
});

<Button type="submit" disabled={processing}>
    {processing ? 'Saving...' : 'Save'}
</Button>
```

**Error Handling:**
- Use Inertia's built-in error handling
- Display validation errors from Laravel
- Toast notifications for success/error messages
- Flash messages via shared props

**[📖 Complete Guide: resources/loading-and-error-states.md](resources/loading-and-error-states.md)**

---

### ⚡ Performance

**Optimization Patterns:**
- `useMemo`: Expensive computations (filter, sort, map)
- `useCallback`: Event handlers passed to children
- `React.memo`: Expensive components
- Debounced search (300-500ms)
- Memory leak prevention (cleanup in useEffect)

**[📖 Complete Guide: resources/performance.md](resources/performance.md)**

---

### 📘 TypeScript

**Standards:**
- Strict mode, no `any` type
- Explicit return types on functions
- Type imports: `import type { User } from '~types/user'`
- Component prop interfaces with JSDoc

**[📖 Complete Guide: resources/typescript-standards.md](resources/typescript-standards.md)**

---

### 🔧 Common Patterns

**Covered Topics:**
- Inertia forms with Laravel validation
- Modal/Dialog components with Inertia
- Authentication with `usePage().props.auth`
- File uploads with Inertia
- Pagination and filtering patterns
- Flash messages and notifications

**[📖 Complete Guide: resources/common-patterns.md](resources/common-patterns.md)**

---

### 📚 Complete Examples

**Full working examples:**
- Inertia page component with TypeScript
- Form with validation and error handling
- CRUD operations with Inertia
- Reusable Tailwind components
- Layout components
- Modal dialogs

**[📖 Complete Guide: resources/complete-examples.md](resources/complete-examples.md)**

---

## Navigation Guide

| Need to... | Read this resource |
|------------|-------------------|
| Create a component | [component-patterns.md](resources/component-patterns.md) |
| Fetch data | [data-fetching.md](resources/data-fetching.md) |
| Organize files/folders | [file-organization.md](resources/file-organization.md) |
| Style components | [styling-guide.md](resources/styling-guide.md) |
| Set up routing | [routing-guide.md](resources/routing-guide.md) |
| Handle loading/errors | [loading-and-error-states.md](resources/loading-and-error-states.md) |
| Optimize performance | [performance.md](resources/performance.md) |
| TypeScript types | [typescript-standards.md](resources/typescript-standards.md) |
| Forms/Auth/DataGrid | [common-patterns.md](resources/common-patterns.md) |
| See full examples | [complete-examples.md](resources/complete-examples.md) |

---

## Core Principles

1. **Server-Side First**: Data from Laravel controllers via Inertia props
2. **Lazy Load Heavy Components**: DataGrid, charts, editors
3. **Tailwind for Styling**: Use utility classes, extract to components when needed
4. **TypeScript Everything**: Type all props, responses, and state
5. **Inertia Forms**: Use `useForm()` hook for all forms
6. **Component Composition**: Build reusable components with Tailwind
7. **Progressive Enhancement**: Use Inertia's SPA-like navigation
8. **Laravel Validation**: Leverage backend validation, display errors in frontend

---

## Quick Reference: File Structure

```
resources/js/
  Pages/
    Posts/
      Index.tsx              # List posts page
      Show.tsx               # Single post page
      Create.tsx             # Create post page
      Edit.tsx               # Edit post page
      Partials/              # Page-specific components
        PostCard.tsx
        PostFilters.tsx

  Components/
    ui/                      # Reusable UI components
      button.tsx
      input.tsx
      card.tsx
      dialog.tsx

  Layouts/
    AuthenticatedLayout.tsx  # Layout for authenticated users
    GuestLayout.tsx          # Layout for guests

  types/
    index.d.ts               # Global types

  lib/
    utils.ts                 # Utility functions (cn, etc.)
```

---

## Modern Inertia Page Template (Quick Copy)

```typescript
import React from 'react';
import { Head, Link, useForm } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';
import type { PageProps } from '@/types';

interface Post {
    id: number;
    title: string;
    content: string;
    author: { name: string };
}

interface Props extends PageProps {
    posts: Post[];
}

export default function Index({ auth, posts }: Props) {
    const { data, setData, get, processing } = useForm({
        search: '',
    });

    const handleSearch = (e: React.FormEvent) => {
        e.preventDefault();
        get(route('posts.index'), {
            preserveState: true,
            preserveScroll: true,
        });
    };

    return (
        <AuthenticatedLayout user={auth.user}>
            <Head title="Posts" />

            <div className="mx-auto max-w-7xl px-4 py-8">
                <div className="mb-6 flex items-center justify-between">
                    <h1 className="text-3xl font-bold">Posts</h1>
                    <Link href={route('posts.create')}>
                        <Button>Create Post</Button>
                    </Link>
                </div>

                <form onSubmit={handleSearch} className="mb-6">
                    <Input
                        type="text"
                        value={data.search}
                        onChange={(e) => setData('search', e.target.value)}
                        placeholder="Search posts..."
                        className="max-w-md"
                    />
                </form>

                <div className="grid gap-4">
                    {posts.map((post) => (
                        <div
                            key={post.id}
                            className="rounded-lg border bg-white p-6 shadow-sm"
                        >
                            <h2 className="text-xl font-semibold">{post.title}</h2>
                            <p className="mt-2 text-gray-600">{post.content}</p>
                            <p className="mt-4 text-sm text-gray-500">
                                By {post.author.name}
                            </p>
                        </div>
                    ))}
                </div>
            </div>
        </AuthenticatedLayout>
    );
}
```

For complete examples, see [resources/complete-examples.md](resources/complete-examples.md)

---

## Related Skills

- **backend-dev-guidelines**: Laravel backend patterns that Inertia consumes

---

**Skill Status**: Updated for Inertia.js + Laravel + React + Tailwind CSS v4 stack