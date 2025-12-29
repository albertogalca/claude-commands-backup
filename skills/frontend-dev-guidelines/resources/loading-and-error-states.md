# Loading & Error States - Inertia.js

Handling loading states and validation errors in Inertia.js applications.

---

## Inertia Progress Indicator

### Global Progress Bar

Inertia automatically shows a progress bar during navigation:

```typescript
// resources/js/app.tsx
import { router } from '@inertiajs/react';
import NProgress from 'nprogress';
import 'nprogress/nprogress.css';

// Configure NProgress
NProgress.configure({ showSpinner: false });

router.on('start', () => NProgress.start());
router.on('finish', () => NProgress.done());
```

**Style the progress bar:**

```css
/* app.css */
#nprogress .bar {
    background: #3b82f6 !important;
    height: 3px !important;
}

#nprogress .peg {
    box-shadow: 0 0 10px #3b82f6, 0 0 5px #3b82f6 !important;
}
```

---

## Form Processing States

### useForm Hook

The `useForm` hook provides a `processing` state:

```typescript
import { useForm } from '@inertiajs/react';
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';

export default function CreatePost() {
    const { data, setData, post, processing, errors, reset } = useForm({
        title: '',
        content: '',
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post('/posts', {
            onSuccess: () => reset(),
        });
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <div>
                <Input
                    value={data.title}
                    onChange={(e) => setData('title', e.target.value)}
                    disabled={processing}
                />
            </div>

            <Button type="submit" disabled={processing}>
                {processing ? 'Creating...' : 'Create Post'}
            </Button>
        </form>
    );
}
```

**Key Points:**
- `processing`: Boolean indicating form submission in progress
- Disable inputs during processing
- Show loading text/spinner in button

---

## Validation Errors

### Displaying Laravel Validation Errors

```typescript
import { useForm } from '@inertiajs/react';

interface PostFormData {
    title: string;
    content: string;
    category: string;
}

export default function PostForm() {
    const { data, setData, post, processing, errors } = useForm<PostFormData>({
        title: '',
        content: '',
        category: '',
    });

    return (
        <form onSubmit={handleSubmit} className="space-y-6">
            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Title
                </label>
                <input
                    type="text"
                    value={data.title}
                    onChange={(e) => setData('title', e.target.value)}
                    className={cn(
                        "mt-1 w-full rounded-md border px-3 py-2",
                        errors.title
                            ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                            : "border-gray-300 focus:border-blue-500 focus:ring-blue-500"
                    )}
                />
                {errors.title && (
                    <p className="mt-1 text-sm text-red-600">{errors.title}</p>
                )}
            </div>

            <div>
                <label className="block text-sm font-medium text-gray-700">
                    Content
                </label>
                <textarea
                    value={data.content}
                    onChange={(e) => setData('content', e.target.value)}
                    rows={4}
                    className={cn(
                        "mt-1 w-full rounded-md border px-3 py-2",
                        errors.content && "border-red-500"
                    )}
                />
                {errors.content && (
                    <p className="mt-1 text-sm text-red-600">{errors.content}</p>
                )}
            </div>

            <Button type="submit" disabled={processing}>
                {processing ? 'Saving...' : 'Save Post'}
            </Button>
        </form>
    );
}
```

### Error Summary Component

```typescript
import { usePage } from '@inertiajs/react';

export function ValidationErrors() {
    const { errors } = usePage().props;
    const errorMessages = Object.values(errors);

    if (errorMessages.length === 0) return null;

    return (
        <div className="rounded-md bg-red-50 p-4">
            <div className="flex">
                <div className="flex-shrink-0">
                    <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" />
                    </svg>
                </div>
                <div className="ml-3">
                    <h3 className="text-sm font-medium text-red-800">
                        There {errorMessages.length === 1 ? 'was' : 'were'} {errorMessages.length} error{errorMessages.length === 1 ? '' : 's'} with your submission
                    </h3>
                    <ul className="mt-2 list-disc space-y-1 pl-5 text-sm text-red-700">
                        {errorMessages.map((error, index) => (
                            <li key={index}>{error}</li>
                        ))}
                    </ul>
                </div>
            </div>
        </div>
    );
}
```

---

## Flash Messages

### Success/Error Notifications

```typescript
import { usePage } from '@inertiajs/react';
import { useEffect, useState } from 'react';

export function FlashMessages() {
    const { flash } = usePage<PageProps>().props;
    const [visible, setVisible] = useState(false);

    useEffect(() => {
        if (flash.success || flash.error) {
            setVisible(true);
            const timer = setTimeout(() => setVisible(false), 5000);
            return () => clearTimeout(timer);
        }
    }, [flash]);

    if (!visible || (!flash.success && !flash.error)) return null;

    return (
        <div className="fixed right-4 top-4 z-50">
            {flash.success && (
                <div className="rounded-lg bg-green-50 p-4 shadow-lg">
                    <div className="flex items-center">
                        <svg className="h-5 w-5 text-green-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" />
                        </svg>
                        <p className="ml-3 text-sm font-medium text-green-800">
                            {flash.success}
                        </p>
                        <button
                            onClick={() => setVisible(false)}
                            className="ml-4 text-green-500 hover:text-green-600"
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}

            {flash.error && (
                <div className="rounded-lg bg-red-50 p-4 shadow-lg">
                    <div className="flex items-center">
                        <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" />
                        </svg>
                        <p className="ml-3 text-sm font-medium text-red-800">
                            {flash.error}
                        </p>
                        <button
                            onClick={() => setVisible(false)}
                            className="ml-4 text-red-500 hover:text-red-600"
                        >
                            ×
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
```

**Set flash messages in controller:**

```php
return redirect()->route('posts.index')
    ->with('success', 'Post created successfully');

return redirect()->back()
    ->with('error', 'Something went wrong');
```

---

## Loading Skeletons

### Skeleton for Lazy Components

```typescript
import { Suspense } from 'react';

const HeavyDataGrid = React.lazy(() => import('./HeavyDataGrid'));

function PostsSkeleton() {
    return (
        <div className="space-y-4">
            {[...Array(5)].map((_, i) => (
                <div key={i} className="animate-pulse rounded-lg border bg-white p-6">
                    <div className="h-4 w-3/4 rounded bg-gray-200"></div>
                    <div className="mt-3 h-3 w-full rounded bg-gray-200"></div>
                    <div className="mt-2 h-3 w-5/6 rounded bg-gray-200"></div>
                </div>
            ))}
        </div>
    );
}

export default function Posts() {
    return (
        <div>
            <h1>Posts</h1>
            <Suspense fallback={<PostsSkeleton />}>
                <HeavyDataGrid />
            </Suspense>
        </div>
    );
}
```

---

## File Upload Progress

### Track Upload Progress

```typescript
import { useForm } from '@inertiajs/react';

export default function UploadForm() {
    const { data, setData, post, processing, progress } = useForm({
        file: null as File | null,
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post('/upload');
    };

    return (
        <form onSubmit={handleSubmit} className="space-y-4">
            <input
                type="file"
                onChange={(e) => setData('file', e.target.files?.[0] || null)}
                className="block w-full"
            />

            {progress && (
                <div className="space-y-2">
                    <div className="h-2 w-full rounded-full bg-gray-200">
                        <div
                            className="h-2 rounded-full bg-blue-600 transition-all"
                            style={{ width: `${progress.percentage}%` }}
                        />
                    </div>
                    <p className="text-sm text-gray-600">
                        Uploading: {progress.percentage}%
                    </p>
                </div>
            )}

            <button
                type="submit"
                disabled={processing}
                className="rounded bg-blue-600 px-4 py-2 text-white disabled:opacity-50"
            >
                {processing ? 'Uploading...' : 'Upload'}
            </button>
        </form>
    );
}
```

---

## Optimistic UI Updates

### Update UI Before Server Response

```typescript
import { router } from '@inertiajs/react';
import { useState } from 'react';

export default function LikeButton({ post }: { post: Post }) {
    const [optimisticLikes, setOptimisticLikes] = useState(post.likes_count);
    const [isLiked, setIsLiked] = useState(post.is_liked);

    const handleLike = () => {
        // Optimistic update
        setOptimisticLikes(isLiked ? optimisticLikes - 1 : optimisticLikes + 1);
        setIsLiked(!isLiked);

        // Send to server
        router.post(`/posts/${post.id}/like`, {}, {
            preserveScroll: true,
            onError: () => {
                // Revert on error
                setOptimisticLikes(post.likes_count);
                setIsLiked(post.is_liked);
            },
        });
    };

    return (
        <button
            onClick={handleLike}
            className={cn(
                "flex items-center gap-2 rounded px-3 py-2",
                isLiked ? "bg-blue-600 text-white" : "bg-gray-200 text-gray-700"
            )}
        >
            <HeartIcon className="h-5 w-5" />
            <span>{optimisticLikes}</span>
        </button>
    );
}
```

---

## Empty States

### No Data Available

```typescript
export function EmptyState({
    icon: Icon,
    title,
    description,
    action,
}: EmptyStateProps) {
    return (
        <div className="flex flex-col items-center justify-center py-12 text-center">
            {Icon && <Icon className="h-12 w-12 text-gray-400" />}
            <h3 className="mt-4 text-lg font-semibold text-gray-900">{title}</h3>
            {description && (
                <p className="mt-2 text-sm text-gray-600">{description}</p>
            )}
            {action && <div className="mt-6">{action}</div>}
        </div>
    );
}

// Usage
{posts.length === 0 ? (
    <EmptyState
        icon={DocumentIcon}
        title="No posts yet"
        description="Get started by creating your first post."
        action={
            <Link href="/posts/create">
                <Button>Create Post</Button>
            </Link>
        }
    />
) : (
    <PostList posts={posts} />
)}
```

---

## Summary

**Inertia Loading & Error Patterns:**
1. **Progress Bar**: NProgress for navigation
2. **Form Processing**: Use `processing` state from `useForm`
3. **Validation Errors**: Display Laravel validation errors
4. **Flash Messages**: Success/error notifications
5. **Skeletons**: Loading placeholders for lazy components
6. **Upload Progress**: Track file upload progress
7. **Optimistic UI**: Update UI before server response
8. **Empty States**: Handle no data scenarios

**See Also:**
- [data-fetching.md](data-fetching.md) - useForm and mutations
- [component-patterns.md](component-patterns.md) - Lazy loading
- [common-patterns.md](common-patterns.md) - Form patterns
