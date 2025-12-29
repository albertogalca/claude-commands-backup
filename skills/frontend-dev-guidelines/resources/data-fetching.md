# Data Fetching with Inertia.js

Modern data fetching using Inertia.js server-side rendering, with data passed as props from Laravel controllers.

---

## PRIMARY PATTERN: Server-Side Props

### Why Server-Side Props?

With Inertia, **all data comes from the server** via controller props:

**Benefits:**
- No client-side loading states on initial render
- SEO-friendly (server-rendered)
- Type-safe with TypeScript
- Automatic CSRF protection
- Leverages Laravel's ORM and relationships
- Simpler mental model

### Basic Pattern

**Laravel Controller:**
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
            'posts' => Post::with('author')
                ->latest()
                ->paginate(10),
        ]);
    }

    public function show(Post $post)
    {
        return Inertia::render('Posts/Show', [
            'post' => $post->load('author', 'comments'),
        ]);
    }
}
```

**React Component:**
```typescript
import React from 'react';
import { Head } from '@inertiajs/react';
import AuthenticatedLayout from '@/Layouts/AuthenticatedLayout';
import type { PageProps } from '@/types';

interface Post {
    id: number;
    title: string;
    content: string;
    author: {
        name: string;
    };
}

interface Props extends PageProps {
    post: Post;
}

export default function Show({ auth, post }: Props) {
    // Data is immediately available - no loading state!
    return (
        <AuthenticatedLayout user={auth.user}>
            <Head title={post.title} />

            <div className="mx-auto max-w-4xl px-4 py-8">
                <h1 className="text-3xl font-bold">{post.title}</h1>
                <p className="mt-2 text-gray-600">By {post.author.name}</p>
                <div className="mt-6">{post.content}</div>
            </div>
        </AuthenticatedLayout>
    );
}
```

**Key Points:**
- Props interface extends `PageProps` for auth/shared data
- Data is **always available** on initial render
- No `isLoading` checks needed
- Type-safe with TypeScript interfaces

---

## Shared Data (Global Props)

### Using Inertia Middleware

Share data across all pages using Inertia middleware:

**Laravel Middleware:**
```php
<?php

namespace App\Http\Middleware;

use Illuminate\Http\Request;
use Inertia\Middleware;

class HandleInertiaRequests extends Middleware
{
    public function share(Request $request): array
    {
        return array_merge(parent::share($request), [
            'auth' => [
                'user' => $request->user(),
            ],
            'flash' => [
                'success' => fn () => $request->session()->get('success'),
                'error' => fn () => $request->session()->get('error'),
            ],
            'app' => [
                'name' => config('app.name'),
            ],
        ]);
    }
}
```

**Access in Components:**
```typescript
import { usePage } from '@inertiajs/react';
import type { PageProps } from '@/types';

export default function MyPage() {
    const { auth, flash, app } = usePage<PageProps>().props;

    return (
        <div>
            <p>Welcome, {auth.user.name}</p>
            {flash.success && (
                <div className="rounded bg-green-100 p-4 text-green-800">
                    {flash.success}
                </div>
            )}
        </div>
    );
}
```

**PageProps Type:**
```typescript
// resources/js/types/index.d.ts
export interface User {
    id: number;
    name: string;
    email: string;
}

export interface PageProps {
    auth: {
        user: User;
    };
    flash: {
        success?: string;
        error?: string;
    };
    app: {
        name: string;
    };
}
```

---

## Form Submissions with useForm

### Creating and Updating Data

Use Inertia's `useForm` hook for mutations:

```typescript
import { useForm } from '@inertiajs/react';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';

interface PostFormData {
    title: string;
    content: string;
}

export default function CreatePost() {
    const { data, setData, post, processing, errors, reset } = useForm<PostFormData>({
        title: '',
        content: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();

        post('/posts', {
            onSuccess: () => {
                reset();
                // Optionally redirect or show success message
            },
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <label className="block text-sm font-medium">Title</label>
                <Input
                    type="text"
                    value={data.title}
                    onChange={(e) => setData('title', e.target.value)}
                    className="mt-1"
                />
                {errors.title && (
                    <p className="mt-1 text-sm text-red-600">{errors.title}</p>
                )}
            </div>

            <div>
                <label className="block text-sm font-medium">Content</label>
                <textarea
                    value={data.content}
                    onChange={(e) => setData('content', e.target.value)}
                    className="mt-1 w-full rounded-md border p-2"
                    rows={4}
                />
                {errors.content && (
                    <p className="mt-1 text-sm text-red-600">{errors.content}</p>
                )}
            </div>

            <Button type="submit" disabled={processing}>
                {processing ? 'Creating...' : 'Create Post'}
            </Button>
        </form>
    );
}
```

**useForm Methods:**
- `data`: Form data state
- `setData(key, value)`: Update single field
- `setData(newData)`: Update entire form
- `post(url)`, `put(url)`, `patch(url)`, `delete(url)`: HTTP methods
- `processing`: Boolean indicating submission in progress
- `errors`: Validation errors from Laravel
- `reset()`: Reset form to initial values

---

## Partial Reloads (Optimistic Updates)

### Reload Only What Changed

When updating data, reload only specific props:

```typescript
import { router } from '@inertiajs/react';

function handleMarkAsRead(postId: number) {
    router.post(`/posts/${postId}/mark-read`, {}, {
        preserveScroll: true,
        preserveState: true,
        only: ['posts'], // Only reload 'posts' prop
        onSuccess: () => {
            // Handle success
        },
    });
}
```

**Options:**
- `preserveScroll`: Keep scroll position
- `preserveState`: Keep component state
- `only`: Array of prop names to reload
- `except`: Array of prop names to exclude
- `onSuccess`, `onError`: Callbacks

---

## Pagination

### Laravel Pagination with Inertia

**Controller:**
```php
public function index(Request $request)
{
    return Inertia::render('Posts/Index', [
        'posts' => Post::query()
            ->when($request->search, fn($q) =>
                $q->where('title', 'like', "%{$request->search}%")
            )
            ->latest()
            ->paginate(15)
            ->withQueryString(),
    ]);
}
```

**Component:**
```typescript
import { Link } from '@inertiajs/react';
import type { PaginatedData } from '@/types';

interface Post {
    id: number;
    title: string;
}

interface Props extends PageProps {
    posts: PaginatedData<Post>;
}

export default function Index({ posts }: Props) {
    return (
        <div>
            <div className="space-y-4">
                {posts.data.map((post) => (
                    <div key={post.id} className="rounded border p-4">
                        <h2>{post.title}</h2>
                    </div>
                ))}
            </div>

            {/* Pagination Links */}
            <div className="mt-6 flex gap-2">
                {posts.links.map((link, index) => (
                    <Link
                        key={index}
                        href={link.url || '#'}
                        className={cn(
                            "rounded px-3 py-2",
                            link.active
                                ? "bg-blue-600 text-white"
                                : "bg-gray-200 text-gray-700 hover:bg-gray-300"
                        )}
                        dangerouslySetInnerHTML={{ __html: link.label }}
                    />
                ))}
            </div>
        </div>
    );
}
```

**PaginatedData Type:**
```typescript
export interface PaginatedData<T> {
    data: T[];
    links: Array<{
        url: string | null;
        label: string;
        active: boolean;
    }>;
    current_page: number;
    last_page: number;
    per_page: number;
    total: number;
}
```

---

## Filtering and Search

### Preserving State with Query Strings

```typescript
import { useForm } from '@inertiajs/react';
import { useEffect } from 'react';

interface Filters {
    search: string;
    status: string;
}

interface Props extends PageProps {
    posts: PaginatedData<Post>;
    filters: Filters;
}

export default function Index({ posts, filters }: Props) {
    const { data, setData, get } = useForm<Filters>({
        search: filters.search || '',
        status: filters.status || '',
    });

    // Auto-submit on filter change
    useEffect(() => {
        const timer = setTimeout(() => {
            get(route('posts.index'), {
                preserveState: true,
                preserveScroll: true,
            });
        }, 300); // Debounce

        return () => clearTimeout(timer);
    }, [data.search, data.status]);

    return (
        <div>
            <div className="mb-6 flex gap-4">
                <input
                    type="text"
                    value={data.search}
                    onChange={(e) => setData('search', e.target.value)}
                    placeholder="Search posts..."
                    className="rounded border px-3 py-2"
                />

                <select
                    value={data.status}
                    onChange={(e) => setData('status', e.target.value)}
                    className="rounded border px-3 py-2"
                >
                    <option value="">All Status</option>
                    <option value="published">Published</option>
                    <option value="draft">Draft</option>
                </select>
            </div>

            {/* Posts list */}
        </div>
    );
}
```

---

## File Uploads

### Handling File Uploads

```typescript
import { useForm } from '@inertiajs/react';

export default function UploadForm() {
    const { data, setData, post, processing, progress, errors } = useForm({
        avatar: null as File | null,
        name: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post('/profile/update');
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                type="file"
                onChange={(e) => setData('avatar', e.target.files?.[0] || null)}
            />
            {errors.avatar && <p className="text-red-600">{errors.avatar}</p>}

            <input
                type="text"
                value={data.name}
                onChange={(e) => setData('name', e.target.value)}
            />

            {progress && (
                <div className="mt-2">
                    <div className="h-2 rounded bg-gray-200">
                        <div
                            className="h-2 rounded bg-blue-600"
                            style={{ width: `${progress.percentage}%` }}
                        />
                    </div>
                    <p className="text-sm text-gray-600">
                        {progress.percentage}% uploaded
                    </p>
                </div>
            )}

            <button type="submit" disabled={processing}>
                Upload
            </button>
        </form>
    );
}
```

---

## Client-Side Data Fetching (Rare)

### When to Use Client-Side Fetching

Use client-side fetching **only when necessary**:
- Real-time updates (polling, websockets)
- Infinite scroll
- Data that changes frequently
- Optional/supplementary data

**Example with fetch:**
```typescript
import { useState, useEffect } from 'react';

interface Stats {
    views: number;
    likes: number;
}

export function PostStats({ postId }: { postId: number }) {
    const [stats, setStats] = useState<Stats | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch(`/api/posts/${postId}/stats`)
            .then(res => res.json())
            .then(data => {
                setStats(data);
                setLoading(false);
            });
    }, [postId]);

    if (loading) {
        return <div className="animate-pulse">Loading stats...</div>;
    }

    return (
        <div className="flex gap-4">
            <span>{stats?.views} views</span>
            <span>{stats?.likes} likes</span>
        </div>
    );
}
```

**Note:** Prefer server-side props whenever possible.

---

## Summary

**Inertia Data Fetching Patterns:**
1. **Server-Side Props**: Primary pattern for initial data
2. **useForm**: For creating/updating data
3. **Partial Reloads**: Optimize updates with `only` option
4. **Shared Data**: Global props via middleware
5. **Pagination**: Use Laravel's built-in pagination
6. **Filters**: Preserve state with query strings
7. **File Uploads**: Built-in support with progress
8. **Client-Side**: Only when server-side isn't feasible

**See Also:**
- [loading-and-error-states.md](loading-and-error-states.md) - Handling loading and validation errors
- [common-patterns.md](common-patterns.md) - More Inertia patterns
- [complete-examples.md](complete-examples.md) - Full CRUD examples
