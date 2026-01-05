# Routing Guide - Inertia.js + Laravel

Routing with Inertia.js using Laravel's routing system and React components.

---

## Overview

**Inertia.js Routing:**
- Server-side routes defined in Laravel
- Client-side navigation feels like SPA
- Type-safe route helpers
- No client-side router needed

---

## Laravel Routes

### Defining Routes

Routes are defined in `routes/web.php`:

```php
<?php

use App\Http\Controllers\PostController;
use Illuminate\Support\Facades\Route;

// Simple route
Route::get('/posts', [PostController::class, 'index'])->name('posts.index');

// Route with parameter
Route::get('/posts/{post}', [PostController::class, 'show'])->name('posts.show');

// Resource routes (CRUD)
Route::resource('posts', PostController::class);

// Authenticated routes
Route::middleware(['auth'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index'])->name('dashboard');
    Route::get('/profile', [ProfileController::class, 'edit'])->name('profile.edit');
});
```

### Controller Returns Inertia Response

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
            'posts' => Post::latest()->paginate(10),
        ]);
    }

    public function show(Post $post)
    {
        return Inertia::render('Posts/Show', [
            'post' => $post->load('author', 'comments'),
        ]);
    }

    public function create()
    {
        return Inertia::render('Posts/Create');
    }

    public function store(Request $request)
    {
        $validated = $request->validate([
            'title' => 'required|string|max:255',
            'content' => 'required|string',
        ]);

        Post::create($validated);

        return redirect()->route('posts.index')
            ->with('success', 'Post created successfully');
    }
}
```

---

## Page Components

### Directory Structure

```
resources/js/
  Pages/
    Posts/
      Index.tsx          # /posts
      Show.tsx           # /posts/{post}
      Create.tsx         # /posts/create
      Edit.tsx           # /posts/{post}/edit
    Dashboard.tsx        # /dashboard
    Profile/
      Edit.tsx           # /profile/edit
```

### Basic Page Component

```typescript
import { Head } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import type { PageProps } from '@/types';

interface Post {
    id: number;
    title: string;
    content: string;
}

interface Props extends PageProps {
    posts: Post[];
}

export default function Index({ auth, posts }: Props) {
    return (
        <AuthenticatedLayout user={auth.user}>
            <Head title="Posts" />

            <div className="mx-auto max-w-7xl px-4 py-8">
                <h1 className="text-3xl font-bold">Posts</h1>

                <div className="mt-6 space-y-4">
                    {posts.map((post) => (
                        <div
                            key={post.id}
                            className="rounded-lg border bg-white p-6"
                        >
                            <h2 className="text-xl font-semibold">{post.title}</h2>
                            <p className="mt-2 text-gray-600">{post.content}</p>
                        </div>
                    ))}
                </div>
            </div>
        </AuthenticatedLayout>
    );
}
```

---

## Client-Side Navigation

### Link Component

```typescript
import { Link } from '@inertiajs/react';

export default function PostCard({ post }: { post: Post }) {
    return (
        <div className="rounded-lg border bg-white p-6">
            <Link
                href={`/posts/${post.id}`}
                className="text-xl font-semibold text-blue-600 hover:underline"
            >
                {post.title}
            </Link>

            <Link
                href={`/posts/${post.id}/edit`}
                className="mt-4 inline-block rounded bg-blue-600 px-4 py-2 text-white hover:bg-blue-700"
            >
                Edit Post
            </Link>
        </div>
    );
}
```

### Route Helper (Ziggy)

Use Laravel's named routes with the `route()` helper:

```typescript
import { Link } from '@inertiajs/react';

// Install ziggy: composer require tightenco/ziggy

<Link href={route('posts.index')}>
    All Posts
</Link>

<Link href={route('posts.show', post.id)}>
    View Post
</Link>

<Link href={route('posts.edit', post.id)}>
    Edit Post
</Link>

// With query parameters
<Link href={route('posts.index', { search: 'query', status: 'published' })}>
    Search Posts
</Link>
```

### Programmatic Navigation

```typescript
import { router } from '@inertiajs/react';

function handleDelete(postId: number) {
    if (confirm('Are you sure?')) {
        router.delete(`/posts/${postId}`, {
            onSuccess: () => {
                // Handle success
            },
        });
    }
}

function handleCreate(data: PostData) {
    router.post('/posts', data, {
        onSuccess: () => {
            router.visit('/posts');
        },
    });
}

// Navigate with options
router.visit('/posts', {
    method: 'get',
    data: { search: 'query' },
    preserveState: true,
    preserveScroll: true,
});
```

---

## Navigation Options

### Preserve State and Scroll

```typescript
import { Link, router } from '@inertiajs/react';

// Link with options
<Link
    href="/posts"
    preserveState
    preserveScroll
    only={['posts']}
>
    Refresh Posts
</Link>

// Router with options
router.get('/posts', { search: 'query' }, {
    preserveState: true,      // Keep component state
    preserveScroll: true,      // Keep scroll position
    only: ['posts'],           // Only reload 'posts' prop
    onSuccess: () => {},
    onError: () => {},
});
```

### Replace vs Push

```typescript
// Default: push to history
router.visit('/posts');

// Replace current history entry
router.visit('/posts', { replace: true });
```

---

## Layouts

### Persistent Layouts

Use layouts that persist across page changes:

```typescript
// Layouts/AuthenticatedLayout.tsx
import { PropsWithChildren } from 'react';
import type { User } from '@/types';

interface Props extends PropsWithChildren {
    user: User;
}

export default function AuthenticatedLayout({ user, children }: Props) {
    return (
        <div className="min-h-screen bg-gray-100">
            <nav className="border-b bg-white">
                <div className="mx-auto max-w-7xl px-4">
                    <div className="flex h-16 items-center justify-between">
                        <Link href="/dashboard">Dashboard</Link>
                        <div className="flex items-center gap-4">
                            <span>{user.name}</span>
                            <Link href="/logout" method="post">
                                Logout
                            </Link>
                        </div>
                    </div>
                </div>
            </nav>

            <main className="py-6">
                {children}
            </main>
        </div>
    );
}

// Usage in page
export default function Dashboard({ auth }: PageProps) {
    return (
        <AuthenticatedLayout user={auth.user}>
            {/* Page content */}
        </AuthenticatedLayout>
    );
}
```

---

## Middleware & Guards

### Protected Routes

```php
// routes/web.php
Route::middleware(['auth', 'verified'])->group(function () {
    Route::get('/dashboard', [DashboardController::class, 'index']);
    Route::resource('posts', PostController::class);
});

Route::middleware('guest')->group(function () {
    Route::get('/login', [AuthController::class, 'create']);
    Route::post('/login', [AuthController::class, 'store']);
});
```

### Handle Redirects

```php
// Handle unauthorized access
protected function redirectTo($request)
{
    return $request->expectsJson()
        ? null
        : route('login');
}
```

---

## Form Methods

### HTTP Methods via Links

```typescript
import { Link } from '@inertiajs/react';

// DELETE request
<Link
    href={`/posts/${post.id}`}
    method="delete"
    as="button"
    onBefore={() => confirm('Are you sure?')}
    className="text-red-600 hover:underline"
>
    Delete
</Link>

// POST request
<Link
    href="/logout"
    method="post"
    as="button"
>
    Logout
</Link>
```

---

## Active Links

### Highlight Current Page

```typescript
import { Link, usePage } from '@inertiajs/react';
import { cn } from '@/lib/utils';

export default function NavLink({ href, children }: NavLinkProps) {
    const { url } = usePage();
    const isActive = url === href || url.startsWith(href + '/');

    return (
        <Link
            href={href}
            className={cn(
                "px-3 py-2 rounded-md transition-colors",
                isActive
                    ? "bg-blue-600 text-white"
                    : "text-gray-700 hover:bg-gray-100"
            )}
        >
            {children}
        </Link>
    );
}
```

---

## Breadcrumbs

### Dynamic Breadcrumbs

```typescript
import { Link, usePage } from '@inertiajs/react';

interface Breadcrumb {
    label: string;
    href: string | null;
}

export default function Breadcrumbs() {
    const { breadcrumbs } = usePage<{ breadcrumbs: Breadcrumb[] }>().props;

    return (
        <nav className="flex items-center gap-2 text-sm">
            {breadcrumbs.map((crumb, index) => (
                <div key={index} className="flex items-center gap-2">
                    {index > 0 && <span className="text-gray-400">/</span>}
                    {crumb.href ? (
                        <Link href={crumb.href} className="text-blue-600 hover:underline">
                            {crumb.label}
                        </Link>
                    ) : (
                        <span className="text-gray-900">{crumb.label}</span>
                    )}
                </div>
            ))}
        </nav>
    );
}

// In controller
return Inertia::render('Posts/Show', [
    'post' => $post,
    'breadcrumbs' => [
        ['label' => 'Home', 'href' => '/'],
        ['label' => 'Posts', 'href' => '/posts'],
        ['label' => $post->title, 'href' => null],
    ],
]);
```

---

## Summary

**Inertia Routing Patterns:**
1. **Laravel Routes**: Define in `routes/web.php`
2. **Inertia::render()**: Return page components from controllers
3. **Link Component**: Client-side navigation
4. **route() Helper**: Use named routes with Ziggy
5. **router Object**: Programmatic navigation
6. **Layouts**: Persistent layouts across pages
7. **Middleware**: Protect routes with Laravel middleware

**See Also:**
- [data-fetching.md](data-fetching.md) - Server-side props
- [loading-and-error-states.md](loading-and-error-states.md) - Progress indicators
- [complete-examples.md](complete-examples.md) - Full routing examples
