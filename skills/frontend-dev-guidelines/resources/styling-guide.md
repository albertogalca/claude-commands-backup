# Styling Guide - Tailwind CSS v4

Modern styling patterns using Tailwind CSS v4 with utility-first approach and component extraction strategies.

---

## Utility-First Approach

### Core Philosophy

Tailwind CSS encourages utility classes directly in JSX:

**Benefits:**
- No context switching between files
- No naming things
- Faster development
- Responsive design built-in
- Automatic purging of unused styles

### Basic Example

```typescript
export default function Card({ title, content }: CardProps) {
    return (
        <div className="rounded-lg border border-gray-200 bg-white p-6 shadow-sm">
            <h2 className="text-2xl font-bold text-gray-900">{title}</h2>
            <p className="mt-2 text-gray-600">{content}</p>
        </div>
    );
}
```

---

## Responsive Design

### Mobile-First Breakpoints

Tailwind uses mobile-first breakpoints:

```typescript
<div className="
    w-full           // Full width on mobile
    md:w-1/2         // Half width on medium screens
    lg:w-1/3         // Third width on large screens
    xl:w-1/4         // Quarter width on extra large
">
    Content
</div>
```

**Breakpoints:**
- `sm`: 640px
- `md`: 768px
- `lg`: 1024px
- `xl`: 1280px
- `2xl`: 1536px

### Responsive Patterns

```typescript
export default function ResponsiveGrid({ items }: Props) {
    return (
        <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
            {items.map((item) => (
                <div key={item.id} className="rounded-lg bg-white p-4">
                    {item.name}
                </div>
            ))}
        </div>
    );
}
```

---

## The cn() Utility

### Conditional Classes

Use the `cn()` utility for conditional and merged classes:

```typescript
import { cn } from '@/lib/utils';

interface ButtonProps {
    variant?: 'primary' | 'secondary' | 'danger';
    size?: 'sm' | 'md' | 'lg';
    disabled?: boolean;
    className?: string;
    children: React.ReactNode;
}

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    disabled,
    className,
    children,
}) => {
    return (
        <button
            className={cn(
                // Base classes (always applied)
                "rounded font-medium transition-colors focus:outline-none focus:ring-2",

                // Variant classes
                variant === 'primary' && "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500",
                variant === 'secondary' && "bg-gray-200 text-gray-900 hover:bg-gray-300 focus:ring-gray-500",
                variant === 'danger' && "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500",

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

### cn() Implementation

```typescript
// lib/utils.ts
import { type ClassValue, clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
    return twMerge(clsx(inputs));
}
```

**Install dependencies:**
```bash
npm install clsx tailwind-merge
```

---

## Component Extraction

### When to Extract Components

**Extract to a component when:**
- Pattern is used 3+ times
- Significant complexity
- Needs props/state
- Domain-specific styling

### Reusable Component Example

```typescript
// Components/ui/card.tsx
import { cn } from '@/lib/utils';

interface CardProps {
    className?: string;
    children: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({ className, children }) => {
    return (
        <div className={cn(
            "rounded-lg border border-gray-200 bg-white shadow-sm",
            className
        )}>
            {children}
        </div>
    );
};

export const CardHeader: React.FC<CardProps> = ({ className, children }) => {
    return (
        <div className={cn("border-b border-gray-200 px-6 py-4", className)}>
            {children}
        </div>
    );
};

export const CardContent: React.FC<CardProps> = ({ className, children }) => {
    return (
        <div className={cn("px-6 py-4", className)}>
            {children}
        </div>
    );
};

export const CardFooter: React.FC<CardProps> = ({ className, children }) => {
    return (
        <div className={cn("border-t border-gray-200 px-6 py-4", className)}>
            {children}
        </div>
    );
};

// Usage
import { Card, CardHeader, CardContent, CardFooter } from '@/Components/ui/card';

<Card>
    <CardHeader>
        <h2 className="text-xl font-semibold">Title</h2>
    </CardHeader>
    <CardContent>
        <p>Content goes here</p>
    </CardContent>
    <CardFooter>
        <button className="rounded bg-blue-600 px-4 py-2 text-white">
            Action
        </button>
    </CardFooter>
</Card>
```

---

## Tailwind v4 Features

### CSS-First Configuration

Tailwind v4 uses CSS for configuration instead of JavaScript:

```css
/* app.css */
@import "tailwindcss";

@theme {
    --color-primary: #3b82f6;
    --color-secondary: #64748b;
    --font-sans: 'Inter', system-ui, sans-serif;
    --breakpoint-3xl: 1920px;
}
```

### Custom Utilities

```css
@layer utilities {
    .text-balance {
        text-wrap: balance;
    }

    .scrollbar-hide {
        scrollbar-width: none;
        -ms-overflow-style: none;
    }

    .scrollbar-hide::-webkit-scrollbar {
        display: none;
    }
}
```

### Container Queries

```typescript
<div className="@container">
    <div className="
        @sm:flex
        @md:grid @md:grid-cols-2
        @lg:grid-cols-3
    ">
        {/* Content */}
    </div>
</div>
```

---

## Dark Mode

### Class-Based Dark Mode

```typescript
export default function ThemedCard() {
    return (
        <div className="
            rounded-lg bg-white p-6 text-gray-900
            dark:bg-gray-800 dark:text-gray-100
        ">
            <h2 className="text-2xl font-bold">Card Title</h2>
            <p className="mt-2 text-gray-600 dark:text-gray-400">
                Content that adapts to dark mode
            </p>
        </div>
    );
}
```

### Toggle Dark Mode

```typescript
import { useState, useEffect } from 'react';

export function useDarkMode() {
    const [isDark, setIsDark] = useState(false);

    useEffect(() => {
        const saved = localStorage.getItem('darkMode');
        const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
        setIsDark(saved ? saved === 'true' : prefersDark);
    }, []);

    const toggleDarkMode = () => {
        const newValue = !isDark;
        setIsDark(newValue);
        localStorage.setItem('darkMode', String(newValue));
        document.documentElement.classList.toggle('dark', newValue);
    };

    return { isDark, toggleDarkMode };
}
```

---

## Common Patterns

### Flexbox Layouts

```typescript
// Centered content
<div className="flex items-center justify-center">
    <Content />
</div>

// Space between items
<div className="flex items-center justify-between">
    <Left />
    <Right />
</div>

// Vertical stack with gap
<div className="flex flex-col gap-4">
    <Item1 />
    <Item2 />
    <Item3 />
</div>

// Responsive flex direction
<div className="flex flex-col md:flex-row gap-4">
    <Sidebar />
    <Main />
</div>
```

### Grid Layouts

```typescript
// Auto-fit grid
<div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
    {items.map(item => <Card key={item.id} {...item} />)}
</div>

// Fixed columns with responsive
<div className="grid grid-cols-12 gap-4">
    <div className="col-span-12 md:col-span-8">
        <Main />
    </div>
    <div className="col-span-12 md:col-span-4">
        <Sidebar />
    </div>
</div>
```

### Hover and Focus States

```typescript
<button className="
    rounded bg-blue-600 px-4 py-2 text-white
    transition-colors
    hover:bg-blue-700
    focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2
    active:bg-blue-800
    disabled:cursor-not-allowed disabled:opacity-50
">
    Click me
</button>
```

### Animations

```typescript
// Spin animation
<div className="h-8 w-8 animate-spin rounded-full border-4 border-gray-200 border-t-blue-600" />

// Pulse animation
<div className="animate-pulse rounded bg-gray-200 p-4" />

// Custom animation
<div className="animate-bounce">
    <Icon />
</div>

// Transition
<div className="transform transition-all duration-300 hover:scale-105">
    <Card />
</div>
```

---

## Form Styling

### Input Components

```typescript
export const Input: React.FC<InputProps> = ({
    type = 'text',
    error,
    className,
    ...props
}) => {
    return (
        <input
            type={type}
            className={cn(
                "w-full rounded-md border px-3 py-2 transition-colors",
                "focus:outline-none focus:ring-2",
                error
                    ? "border-red-500 focus:border-red-500 focus:ring-red-500"
                    : "border-gray-300 focus:border-blue-500 focus:ring-blue-500",
                className
            )}
            {...props}
        />
    );
};

// Usage with validation
<div>
    <label className="block text-sm font-medium text-gray-700">
        Email
    </label>
    <Input
        type="email"
        value={data.email}
        onChange={(e) => setData('email', e.target.value)}
        error={!!errors.email}
        className="mt-1"
    />
    {errors.email && (
        <p className="mt-1 text-sm text-red-600">{errors.email}</p>
    )}
</div>
```

---

## Best Practices

### DO's

✅ Use utility classes directly in JSX
✅ Extract components for reused patterns
✅ Use `cn()` for conditional classes
✅ Follow mobile-first responsive design
✅ Use Tailwind's color palette
✅ Leverage hover, focus, and active states
✅ Use spacing scale consistently (4, 8, 12, 16, etc.)

### DON'Ts

❌ Don't create custom CSS unless absolutely necessary
❌ Don't use arbitrary values extensively (`w-[137px]`)
❌ Don't duplicate complex class combinations
❌ Don't fight Tailwind's conventions
❌ Don't use `@apply` for one-off components
❌ Don't mix Tailwind with traditional CSS modules

---

## Typography

### Text Sizes

```typescript
<h1 className="text-4xl font-bold">Heading 1</h1>
<h2 className="text-3xl font-bold">Heading 2</h2>
<h3 className="text-2xl font-semibold">Heading 3</h3>
<h4 className="text-xl font-semibold">Heading 4</h4>
<p className="text-base">Body text</p>
<p className="text-sm text-gray-600">Small text</p>
<p className="text-xs text-gray-500">Tiny text</p>
```

### Text Utilities

```typescript
<p className="
    truncate              // Truncate with ellipsis
    line-clamp-3          // Clamp to 3 lines
    text-balance          // Balance text wrapping (v4)
    leading-relaxed       // Line height
    tracking-wide         // Letter spacing
">
    Long text content...
</p>
```

---

## Summary

**Tailwind CSS Patterns:**
1. **Utility-First**: Use utility classes directly
2. **cn() Utility**: Merge conditional classes
3. **Component Extraction**: Extract at 3+ uses
4. **Responsive**: Mobile-first breakpoints
5. **Tailwind v4**: CSS-first configuration
6. **Dark Mode**: Class-based theming
7. **Consistency**: Use Tailwind's design tokens

**See Also:**
- [component-patterns.md](component-patterns.md) - Component structure
- [complete-examples.md](complete-examples.md) - Full styled examples
