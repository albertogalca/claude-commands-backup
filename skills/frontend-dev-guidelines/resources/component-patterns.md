# Component Patterns

Modern React component architecture for Inertia.js applications emphasizing type safety, lazy loading, and Tailwind CSS styling.

---

## React.FC Pattern (PREFERRED)

### Why React.FC

All components use the `React.FC<Props>` pattern for:
- Explicit type safety for props
- Consistent component signatures
- Clear prop interface documentation
- Better IDE autocomplete

### Basic Pattern

```typescript
import React from 'react';

interface MyComponentProps {
    /** User ID to display */
    userId: number;
    /** Optional callback when action occurs */
    onAction?: () => void;
}

export const MyComponent: React.FC<MyComponentProps> = ({ userId, onAction }) => {
    return (
        <div className="rounded-lg bg-white p-4 shadow-sm">
            <p className="text-gray-700">User: {userId}</p>
        </div>
    );
};

export default MyComponent;
```

**Key Points:**
- Props interface defined separately with JSDoc comments
- `React.FC<Props>` provides type safety
- Destructure props in parameters
- Default export at bottom
- Tailwind classes for styling

---

## Lazy Loading Pattern

### When to Lazy Load

Lazy load components that are:
- Heavy (DataGrid, charts, rich text editors)
- Modal/dialog content (not shown initially)
- Below-the-fold content
- Complex data visualizations

### How to Lazy Load

```typescript
import React, { Suspense } from 'react';

// Lazy load heavy component
const PostDataGrid = React.lazy(() =>
    import('./grids/PostDataGrid')
);

// For named exports
const MyComponent = React.lazy(() =>
    import('./MyComponent').then(module => ({
        default: module.MyComponent
    }))
);
```

**Example Usage:**

```typescript
import React, { Suspense } from 'react';

const PostDataGrid = React.lazy(() => import('./grids/PostDataGrid'));

export const PostTable: React.FC<PostTableProps> = ({ posts }) => {
    return (
        <div className="rounded-lg border bg-white p-6">
            <Suspense fallback={
                <div className="flex items-center justify-center py-8">
                    <div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600"></div>
                </div>
            }>
                <PostDataGrid posts={posts} />
            </Suspense>
        </div>
    );
};

export default PostTable;
```

---

## Inertia Page Components

### Page Component Pattern

Inertia pages receive data via props from Laravel controllers:

```typescript
import React from 'react';
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
                <h1 className="mb-6 text-3xl font-bold">Posts</h1>

                <div className="grid gap-4">
                    {posts.map((post) => (
                        <div
                            key={post.id}
                            className="rounded-lg border bg-white p-6 shadow-sm"
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

**Key Points:**
- Extend `PageProps` for auth and shared data
- Use `<Head>` component for page title
- Wrap in layout component
- Data comes from props (no loading states needed)

---

## Component Structure Template

### Recommended Order

```typescript
/**
 * Component description
 * What it does, when to use it
 */
import React, { useState, useCallback, useMemo, useEffect } from 'react';
import { Link, router } from '@inertiajs/react';
import { cn } from '@/lib/utils';

// Component imports
import { Button } from '@/Components/ui/button';
import { Input } from '@/Components/ui/input';

// Types
import type { User, Post } from '@/types';

// 1. PROPS INTERFACE (with JSDoc)
interface MyComponentProps {
    /** The ID of the entity to display */
    entityId: number;
    /** Optional callback when action completes */
    onComplete?: () => void;
    /** Display mode */
    mode?: 'view' | 'edit';
    /** Additional CSS classes */
    className?: string;
}

// 2. COMPONENT DEFINITION
export const MyComponent: React.FC<MyComponentProps> = ({
    entityId,
    onComplete,
    mode = 'view',
    className,
}) => {
    // 3. HOOKS (in this order)
    // - Local state
    const [selectedItem, setSelectedItem] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(mode === 'edit');

    // - Memoized values
    const filteredData = useMemo(() => {
        // Expensive computation
        return data.filter(item => item.active);
    }, [data]);

    // - Effects
    useEffect(() => {
        // Setup
        return () => {
            // Cleanup
        };
    }, []);

    // 4. EVENT HANDLERS (with useCallback)
    const handleItemSelect = useCallback((itemId: string) => {
        setSelectedItem(itemId);
    }, []);

    const handleSave = useCallback(() => {
        router.post('/api/entities', {
            entityId,
            // data
        }, {
            onSuccess: () => {
                onComplete?.();
            },
        });
    }, [entityId, onComplete]);

    // 5. RENDER
    return (
        <div className={cn("rounded-lg bg-white p-6 shadow-sm", className)}>
            <div className="mb-4 flex items-center justify-between">
                <h2 className="text-2xl font-bold">My Component</h2>
                <Button onClick={handleSave}>Save</Button>
            </div>

            <div className="space-y-4">
                {filteredData.map(item => (
                    <div key={item.id} className="rounded border p-4">
                        {item.name}
                    </div>
                ))}
            </div>
        </div>
    );
};

// 6. EXPORT (default export at bottom)
export default MyComponent;
```

---

## Component Separation

### When to Split Components

**Split into multiple components when:**
- Component exceeds 300 lines
- Multiple distinct responsibilities
- Reusable sections
- Complex nested JSX

**Example:**

```typescript
// ❌ AVOID - Monolithic
function MassiveComponent() {
    // 500+ lines
    // Search logic
    // Filter logic
    // Grid logic
    // Action panel logic
}

// ✅ PREFERRED - Modular
function ParentContainer() {
    return (
        <div className="space-y-6">
            <SearchAndFilter onFilter={handleFilter} />
            <DataGrid data={filteredData} />
            <ActionPanel onAction={handleAction} />
        </div>
    );
}
```

### When to Keep Together

**Keep in same file when:**
- Component < 200 lines
- Tightly coupled logic
- Not reusable elsewhere
- Simple presentation component

---

## Export Patterns

### Named Const + Default Export (PREFERRED)

```typescript
export const MyComponent: React.FC<Props> = ({ ... }) => {
    // Component logic
};

export default MyComponent;
```

**Why:**
- Named export for testing/refactoring
- Default export for lazy loading convenience
- Both options available to consumers

### Lazy Loading Named Exports

```typescript
const MyComponent = React.lazy(() =>
    import('./MyComponent').then(module => ({
        default: module.MyComponent
    }))
);
```

---

## Component Communication

### Props Down, Events Up

```typescript
// Parent
function Parent() {
    const [selectedId, setSelectedId] = useState<string | null>(null);

    return (
        <Child
            data={data}                    // Props down
            onSelect={setSelectedId}       // Events up
        />
    );
}

// Child
interface ChildProps {
    data: Data[];
    onSelect: (id: string) => void;
}

export const Child: React.FC<ChildProps> = ({ data, onSelect }) => {
    return (
        <div
            className="cursor-pointer rounded p-4 hover:bg-gray-50"
            onClick={() => onSelect(data[0].id)}
        >
            {/* Content */}
        </div>
    );
};
```

### Avoid Prop Drilling

**Use context for deep nesting:**
```typescript
// ❌ AVOID - Prop drilling 5+ levels
<A prop={x}>
  <B prop={x}>
    <C prop={x}>
      <D prop={x}>
        <E prop={x} />  // Finally uses it here
      </D>
    </C>
  </B>
</A>

// ✅ PREFERRED - Context
const MyContext = createContext<MyData | null>(null);

function Provider({ children, data }) {
    return <MyContext.Provider value={data}>{children}</MyContext.Provider>;
}

function DeepChild() {
    const data = useContext(MyContext);
    // Use data directly
}
```

---

## Conditional Classes with cn()

### The cn() Utility

```typescript
import { cn } from '@/lib/utils';

export const Button: React.FC<ButtonProps> = ({
    variant = 'default',
    size = 'md',
    disabled,
    className,
    children
}) => {
    return (
        <button
            className={cn(
                // Base classes
                "rounded font-medium transition-colors",
                // Variant classes
                variant === 'primary' && "bg-blue-600 text-white hover:bg-blue-700",
                variant === 'secondary' && "bg-gray-200 text-gray-900 hover:bg-gray-300",
                variant === 'danger' && "bg-red-600 text-white hover:bg-red-700",
                // Size classes
                size === 'sm' && "px-3 py-1.5 text-sm",
                size === 'md' && "px-4 py-2 text-base",
                size === 'lg' && "px-6 py-3 text-lg",
                // State classes
                disabled && "cursor-not-allowed opacity-50",
                // Custom classes from props
                className
            )}
            disabled={disabled}
        >
            {children}
        </button>
    );
};
```

---

## Advanced Patterns

### Compound Components

```typescript
// Card.tsx
interface CardComponent extends React.FC<CardProps> {
    Header: typeof CardHeader;
    Body: typeof CardBody;
    Footer: typeof CardFooter;
}

export const Card: CardComponent = ({ children, className }) => {
    return (
        <div className={cn("rounded-lg border bg-white shadow-sm", className)}>
            {children}
        </div>
    );
};

const CardHeader: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return <div className="border-b px-6 py-4">{children}</div>;
};

const CardBody: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return <div className="px-6 py-4">{children}</div>;
};

const CardFooter: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    return <div className="border-t px-6 py-4">{children}</div>;
};

Card.Header = CardHeader;
Card.Body = CardBody;
Card.Footer = CardFooter;

// Usage
<Card>
    <Card.Header>Title</Card.Header>
    <Card.Body>Content</Card.Body>
    <Card.Footer>Actions</Card.Footer>
</Card>
```

### Render Props (Rare, but useful)

```typescript
interface DataProviderProps {
    data: Data[];
    children: (filteredData: Data[]) => React.ReactNode;
}

export const DataProvider: React.FC<DataProviderProps> = ({ data, children }) => {
    const [filter, setFilter] = useState('');

    const filteredData = useMemo(() => {
        return data.filter(item => item.name.includes(filter));
    }, [data, filter]);

    return <>{children(filteredData)}</>;
};

// Usage
<DataProvider data={posts}>
    {(filteredPosts) => <PostList posts={filteredPosts} />}
</DataProvider>
```

---

## Summary

**Modern Component Recipe:**
1. `React.FC<Props>` with TypeScript
2. Lazy load if heavy: `React.lazy(() => import())`
3. Use Tailwind CSS for styling
4. Use `cn()` for conditional classes
5. Import aliases (@/, @/Components, @/Pages)
6. Event handlers with `useCallback`
7. Default export at bottom
8. Props extend `PageProps` for Inertia pages

**See Also:**
- [data-fetching.md](data-fetching.md) - Inertia server-side props
- [styling-guide.md](styling-guide.md) - Tailwind CSS patterns
- [complete-examples.md](complete-examples.md) - Full working examples
