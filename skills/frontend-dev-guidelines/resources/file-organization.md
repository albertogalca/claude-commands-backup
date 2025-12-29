# File Organization - Inertia.js + Laravel

Proper file and directory structure for maintainable Inertia.js + Laravel applications.

---

## Laravel + Inertia Structure

### Overview

```
app/
  Http/
    Controllers/         # Laravel controllers
  Models/               # Eloquent models

resources/
  js/
    Pages/              # Inertia page components
    Components/         # Reusable UI components
    Layouts/            # Layout components
    types/              # TypeScript type definitions
    lib/                # Utility functions
    app.tsx             # Inertia app setup

routes/
  web.php               # Laravel routes
```

---

## Pages Directory

### Purpose

**Inertia page components** rendered from Laravel controllers.

**Structure:**
```
resources/js/Pages/
  Posts/
    Index.tsx           # /posts
    Show.tsx            # /posts/{post}
    Create.tsx          # /posts/create
    Edit.tsx            # /posts/{post}/edit
    Partials/           # Page-specific components
      PostCard.tsx
      PostFilters.tsx
      CommentList.tsx
  Dashboard.tsx         # /dashboard
  Profile/
    Edit.tsx            # /profile/edit
    Partials/
      UpdateProfileForm.tsx
      UpdatePasswordForm.tsx
```

**Key Points:**
- One directory per resource (Posts, Users, etc.)
- CRUD pages at top level (Index, Show, Create, Edit)
- Page-specific components in `Partials/`
- Each page corresponds to a Laravel controller method

---

## Components Directory

### Purpose

**Truly reusable UI components** used across multiple pages.

**Structure:**
```
resources/js/Components/
  ui/                   # Generic UI primitives
    button.tsx
    input.tsx
    card.tsx
    dialog.tsx
    dropdown.tsx
    badge.tsx
  forms/                # Form components
    FormField.tsx
    FormError.tsx
    SearchInput.tsx
  layout/               # Layout components
    Navbar.tsx
    Sidebar.tsx
    Footer.tsx
  shared/               # Shared business components
    UserAvatar.tsx
    PostPreview.tsx
```

**When to use:**
- Component used in 3+ pages
- Generic UI element
- No page-specific logic
- Reusable pattern

---

## Layouts Directory

### Purpose

**Persistent layouts** that wrap page content.

**Structure:**
```
resources/js/Layouts/
  AuthenticatedLayout.tsx   # For logged-in users
  GuestLayout.tsx           # For guests
  AdminLayout.tsx           # For admin pages
```

**Example:**
```typescript
// Layouts/AuthenticatedLayout.tsx
import { PropsWithChildren } from 'react';
import { Link } from '@inertiajs/react';
import type { User } from '@/types';

interface Props extends PropsWithChildren {
    user: User;
}

export default function AuthenticatedLayout({ user, children }: Props) {
    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="border-b bg-white">
                {/* Navigation */}
            </nav>
            <main>{children}</main>
        </div>
    );
}
```

---

## Types Directory

### Purpose

**TypeScript type definitions** for the application.

**Structure:**
```
resources/js/types/
  index.d.ts            # Global types and interfaces
  models.d.ts           # Laravel model types
  inertia.d.ts          # Inertia-specific types
```

**Example:**
```typescript
// types/index.d.ts
export interface User {
    id: number;
    name: string;
    email: string;
    created_at: string;
}

export interface Post {
    id: number;
    title: string;
    content: string;
    author: User;
    created_at: string;
}

export interface PageProps {
    auth: {
        user: User;
    };
    flash: {
        success?: string;
        error?: string;
    };
}

export interface PaginatedData<T> {
    data: T[];
    links: PaginationLink[];
    current_page: number;
    last_page: number;
    per_page: number;
    total: number;
}
```

---

## Lib Directory

### Purpose

**Utility functions and helpers**.

**Structure:**
```
resources/js/lib/
  utils.ts              # General utilities (cn, formatDate, etc.)
  api.ts                # API client configuration
  constants.ts          # App constants
  validators.ts         # Custom validation functions
```

**Example:**
```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}

export function formatDate(date: string): string {
    return new Date(date).toLocaleDateString('en-US', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
    });
}

export function truncate(str: string, length: number): string {
    return str.length > length ? str.slice(0, length) + '...' : str;
}
```

---

## Page-Specific Components

### Partials Pattern

Keep page-specific components in a `Partials/` subdirectory:

```
Pages/
  Posts/
    Index.tsx
    Partials/
      PostCard.tsx          # Only used in Posts/Index
      PostFilters.tsx       # Only used in Posts/Index
      PostStats.tsx         # Only used in Posts/Index
```

**When to extract to Partials:**
- Component only used in one page
- Makes the main page component cleaner
- Component has substantial logic (>50 lines)

**Example:**
```typescript
// Pages/Posts/Index.tsx
import { Head } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import PostCard from './Partials/PostCard';
import PostFilters from './Partials/PostFilters';

export default function Index({ auth, posts }: Props) {
    return (
        <AuthenticatedLayout user={auth.user}>
            <Head title="Posts" />
            <PostFilters />
            <div className="grid gap-4">
                {posts.map(post => <PostCard key={post.id} post={post} />)}
            </div>
        </AuthenticatedLayout>
    );
}
```

---

## Naming Conventions

### Files

- **Pages**: PascalCase, descriptive (`Index.tsx`, `Show.tsx`, `CreatePost.tsx`)
- **Components**: PascalCase, component name matches file (`Button.tsx`, `UserAvatar.tsx`)
- **Layouts**: PascalCase with "Layout" suffix (`AuthenticatedLayout.tsx`)
- **Types**: lowercase with `.d.ts` extension (`index.d.ts`, `models.d.ts`)
- **Utils**: camelCase (`utils.ts`, `formatDate.ts`)

### Directories

- Lowercase for general directories (`components/`, `lib/`, `types/`)
- PascalCase for resource directories in Pages (`Posts/`, `Users/`)

---

## Import Paths

### TypeScript Path Aliases

Configure in `tsconfig.json`:

```json
{
    "compilerOptions": {
        "paths": {
            "@/*": ["./resources/js/*"]
        }
    }
}
```

**Usage:**
```typescript
// ✅ Good - Use alias
import { Button } from '@/Components/ui/button';
import { User } from '@/types';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';

// ❌ Avoid - Relative paths
import { Button } from '../../../Components/ui/button';
```

---

## Component Organization Within File

### Recommended Order

```typescript
// 1. Imports
import { useState } from 'react';
import { useForm } from '@inertiajs/react';
import { Button } from '@/Components/ui/button';
import type { Post } from '@/types';

// 2. Types/Interfaces
interface PostFormProps {
    post?: Post;
    onSuccess?: () => void;
}

// 3. Component
export default function PostForm({ post, onSuccess }: PostFormProps) {
    // Hooks
    const { data, setData, post: submit, processing, errors } = useForm({
        title: post?.title || '',
        content: post?.content || '',
    });

    // Event handlers
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        submit('/posts');
    };

    // Render
    return (
        <form onSubmit={handleSubmit}>
            {/* JSX */}
        </form>
    );
}

// 4. Helper components (if any, keep in same file if small)
function FormActions() {
    return <div>{/* ... */}</div>;
}
```

---

## Laravel Backend Organization

### Controllers

```
app/Http/Controllers/
  PostController.php
  UserController.php
  DashboardController.php
```

**Example:**
```php
<?php

namespace App\Http\Controllers;

use App\Models\Post;
use Inertia\Inertia;

class PostController extends Controller
{
    public function index()
    {
        return Inertia::render('Posts/Index', [
            'posts' => Post::with('author')->latest()->paginate(10),
        ]);
    }
}
```

---

## Summary

**Inertia + Laravel Structure:**
1. **Pages/**: Inertia page components (one per route)
2. **Components/**: Reusable UI components
3. **Layouts/**: Persistent layouts
4. **types/**: TypeScript definitions
5. **lib/**: Utility functions
6. **Partials/**: Page-specific components
7. **@/ alias**: Clean imports

**Organization Principles:**
- Pages mirror Laravel routes
- Partials for page-specific logic
- Components for reusable UI
- Clear separation of concerns

**See Also:**
- [component-patterns.md](component-patterns.md) - Component structure
- [data-fetching.md](data-fetching.md) - Props from controllers
- [routing-guide.md](routing-guide.md) - Laravel routes + Inertia
