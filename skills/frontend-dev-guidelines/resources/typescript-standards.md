# TypeScript Standards - Inertia.js

TypeScript best practices for Inertia.js + Laravel applications.

---

## Strict Mode

### Configuration

TypeScript strict mode is **enabled**:

```json
// tsconfig.json
{
    "compilerOptions": {
        "strict": true,
        "noImplicitAny": true,
        "strictNullChecks": true,
        "paths": {
            "@/*": ["./resources/js/*"]
        }
    }
}
```

**This means:**
- No implicit `any` types
- Null/undefined must be handled explicitly
- Type safety enforced

---

## No `any` Type

### The Rule

```typescript
// ❌ NEVER use any
function handleData(data: any) {
    return data.something;
}

// ✅ Use specific types
interface Post {
    id: number;
    title: string;
    content: string;
}

function handleData(data: Post) {
    return data.title;
}

// ✅ Or use unknown for truly unknown data
function handleUnknown(data: unknown) {
    if (typeof data === 'object' && data !== null && 'title' in data) {
        return (data as Post).title;
    }
}
```

---

## Inertia Page Props

### PageProps Interface

Define global props available on all pages:

```typescript
// types/index.d.ts
export interface User {
    id: number;
    name: string;
    email: string;
    email_verified_at?: string;
}

export interface PageProps {
    auth: {
        user: User;
    };
    flash: {
        success?: string;
        error?: string;
        warning?: string;
    };
    errors: Record<string, string>;
}
```

### Page-Specific Props

Extend `PageProps` for page-specific data:

```typescript
import type { PageProps } from '@/types';

interface Post {
    id: number;
    title: string;
    content: string;
    author: User;
    created_at: string;
}

interface Props extends PageProps {
    posts: Post[];
    filters: {
        search?: string;
        status?: string;
    };
}

export default function Index({ auth, posts, filters }: Props) {
    // All props are typed
    return <div>{/* ... */}</div>;
}
```

---

## Laravel Model Types

### Define Model Interfaces

```typescript
// types/models.d.ts
export interface User {
    id: number;
    name: string;
    email: string;
    email_verified_at?: string;
    created_at: string;
    updated_at: string;
}

export interface Post {
    id: number;
    title: string;
    content: string;
    published_at?: string;
    author: User;
    created_at: string;
    updated_at: string;
}

export interface Comment {
    id: number;
    content: string;
    post_id: number;
    user_id: number;
    user: User;
    created_at: string;
}
```

### Relationships

```typescript
// With relationships loaded
interface PostWithComments extends Post {
    comments: Comment[];
}

// Partial relationships
interface PostWithAuthor extends Post {
    author: User;
}
```

---

## Pagination Types

### PaginatedData Generic

```typescript
// types/index.d.ts
export interface PaginationLink {
    url: string | null;
    label: string;
    active: boolean;
}

export interface PaginatedData<T> {
    data: T[];
    links: PaginationLink[];
    current_page: number;
    last_page: number;
    per_page: number;
    total: number;
    from: number;
    to: number;
}

// Usage
interface Props extends PageProps {
    posts: PaginatedData<Post>;
}
```

---

## Form Data Types

### useForm with TypeScript

```typescript
import { useForm } from '@inertiajs/react';

interface PostFormData {
    title: string;
    content: string;
    published: boolean;
    category_id?: number;
}

export default function CreatePost() {
    const { data, setData, post, processing, errors } = useForm<PostFormData>({
        title: '',
        content: '',
        published: false,
        category_id: undefined,
    });

    // TypeScript knows about all fields
    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        post('/posts');
    };

    return (
        <form onSubmit={handleSubmit}>
            <input
                value={data.title}
                onChange={(e) => setData('title', e.target.value)}
            />
            {/* TypeScript autocomplete works */}
        </form>
    );
}
```

---

## Component Props

### React.FC Pattern

```typescript
import type { PropsWithChildren } from 'react';

interface ButtonProps {
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    onClick?: () => void;
    className?: string;
}

export const Button: React.FC<PropsWithChildren<ButtonProps>> = ({
    variant = 'primary',
    size = 'md',
    disabled = false,
    onClick,
    className,
    children,
}) => {
    return (
        <button
            onClick={onClick}
            disabled={disabled}
            className={cn(/* ... */, className)}
        >
            {children}
        </button>
    );
};
```

### JSDoc Comments

```typescript
interface CardProps {
    /** The title displayed in the card header */
    title: string;
    /** Optional description text */
    description?: string;
    /** Callback when card is clicked */
    onClick?: () => void;
}
```

---

## Utility Types

### Common Patterns

```typescript
// Make all properties optional
type PartialPost = Partial<Post>;

// Make all properties required
type RequiredPost = Required<Post>;

// Pick specific properties
type PostPreview = Pick<Post, 'id' | 'title' | 'author'>;

// Omit specific properties
type PostWithoutContent = Omit<Post, 'content'>;

// Extract from union
type Status = 'draft' | 'published' | 'archived';
type PublishedStatus = Extract<Status, 'published'>;
```

### Custom Utility Types

```typescript
// For API responses
type ApiResponse<T> = {
    data: T;
    message?: string;
};

// For form state
type FormState<T> = {
    data: T;
    errors: Partial<Record<keyof T, string>>;
    processing: boolean;
};

// Usage
const postResponse: ApiResponse<Post> = await fetch(/* ... */);
```

---

## Shared Props Pattern

### usePage Hook

```typescript
import { usePage } from '@inertiajs/react';
import type { PageProps } from '@/types';

export function MyComponent() {
    const { auth, flash } = usePage<PageProps>().props;

    return (
        <div>
            <p>Welcome, {auth.user.name}</p>
            {flash.success && <div>{flash.success}</div>}
        </div>
    );
}
```

---

## Type Guards

### Runtime Type Checking

```typescript
function isPost(value: unknown): value is Post {
    return (
        typeof value === 'object' &&
        value !== null &&
        'id' in value &&
        'title' in value &&
        'content' in value
    );
}

function handleData(data: unknown) {
    if (isPost(data)) {
        // TypeScript knows data is Post
        console.log(data.title);
    }
}
```

---

## Enum vs Union Types

### Prefer Union Types

```typescript
// ✅ PREFERRED - Union types
type PostStatus = 'draft' | 'published' | 'archived';

interface Post {
    status: PostStatus;
}

// ❌ AVOID - Enums (less flexible)
enum PostStatus {
    Draft = 'draft',
    Published = 'published',
    Archived = 'archived',
}
```

**Why union types?**
- Simpler
- Better autocomplete
- Works with JSON directly
- No runtime overhead

---

## Readonly Types

### Immutable Data

```typescript
interface Config {
    readonly apiUrl: string;
    readonly timeout: number;
}

// Array
const items: readonly Post[] = [...];
// items.push() // Error: readonly

// Deep readonly
type DeepReadonly<T> = {
    readonly [P in keyof T]: DeepReadonly<T[P]>;
};
```

---

## Best Practices

### DO's

✅ Use `interface` for object shapes
✅ Use `type` for unions, intersections, primitives
✅ Extend `PageProps` for page components
✅ Type `useForm` hook data
✅ Use type guards for unknown data
✅ Document complex types with JSDoc
✅ Use `Partial<T>` for optional updates
✅ Define pagination generics

### DON'Ts

❌ Don't use `any`
❌ Don't skip return types
❌ Don't use enums (prefer union types)
❌ Don't make everything optional
❌ Don't duplicate type definitions
❌ Don't cast without type guards
❌ Don't ignore TypeScript errors

---

## Example: Complete Type Setup

```typescript
// types/index.d.ts
export interface User {
    id: number;
    name: string;
    email: string;
}

export interface Post {
    id: number;
    title: string;
    content: string;
    author: User;
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
}

// Page component
import type { PageProps, Post, PaginatedData } from '@/types';

interface Props extends PageProps {
    posts: PaginatedData<Post>;
    filters: {
        search?: string;
    };
}

export default function Index({ auth, posts, filters }: Props) {
    // Fully typed
    return <div>{/* ... */}</div>;
}
```

---

## Summary

**TypeScript Best Practices:**
1. **Strict Mode**: Always enabled
2. **No `any`**: Use specific types or `unknown`
3. **PageProps**: Global props interface
4. **Model Types**: Define Laravel models
5. **Pagination**: Generic `PaginatedData<T>`
6. **useForm**: Type form data
7. **Union Types**: Prefer over enums
8. **Type Guards**: For runtime checks

**See Also:**
- [data-fetching.md](data-fetching.md) - Typing props and forms
- [component-patterns.md](component-patterns.md) - Component typing
- [file-organization.md](file-organization.md) - Where to put types
