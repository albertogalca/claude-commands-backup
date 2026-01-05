# Inertia.js React Patterns

Complete guide for using Inertia.js with React on the client-side with Rails backend.

## Installation & Setup

### 1. Install Dependencies

```bash
npm install @inertiajs/react react react-dom
# or
yarn add @inertiajs/react react react-dom
```

### 2. Initialize Inertia App

```typescript
// app/frontend/entrypoints/application.tsx
import { createRoot } from 'react-dom/client'
import { createInertiaApp } from '@inertiajs/react'

createInertiaApp({
  resolve: (name) => {
    const pages = import.meta.glob('../Pages/**/*.tsx', { eager: true })
    return pages[`../Pages/${name}.tsx`]
  },
  setup({ el, App, props }) {
    createRoot(el).render(<App {...props} />)
  },
})
```

### 3. Progress Indicator (Optional)

```typescript
import { router } from '@inertiajs/react'
import NProgress from 'nprogress'

router.on('start', () => NProgress.start())
router.on('finish', () => NProgress.done())
```

---

## Page Components

### Basic Page Component

```typescript
// app/frontend/Pages/Posts/Index.tsx
import React from 'react'
import { Head } from '@inertiajs/react'

interface Post {
  id: number
  title: string
  content: string
}

interface Props {
  posts: Post[]
}

export default function Index({ posts }: Props) {
  return (
    <>
      <Head title="Posts" />

      <div className="container">
        <h1>Posts</h1>

        {posts.map((post) => (
          <div key={post.id}>
            <h2>{post.title}</h2>
            <p>{post.content}</p>
          </div>
        ))}
      </div>
    </>
  )
}
```

### With Layout

```typescript
// app/frontend/Layouts/AppLayout.tsx
import React, { ReactNode } from 'react'
import { Link } from '@inertiajs/react'

interface Props {
  children: ReactNode
}

export default function AppLayout({ children }: Props) {
  return (
    <div>
      <nav>
        <Link href="/dashboard">Dashboard</Link>
        <Link href="/posts">Posts</Link>
      </nav>

      <main>{children}</main>
    </div>
  )
}

// app/frontend/Pages/Posts/Index.tsx
import AppLayout from '@/Layouts/AppLayout'

function Index({ posts }: Props) {
  return (
    <div>
      {/* Your content */}
    </div>
  )
}

Index.layout = (page: ReactNode) => <AppLayout>{page}</AppLayout>

export default Index
```

---

## Accessing Props

### Page Props

```typescript
interface Props {
  user: {
    id: number
    name: string
    email: string
  }
  posts: Post[]
}

export default function Dashboard({ user, posts }: Props) {
  return (
    <div>
      <h1>Welcome, {user.name}</h1>
      {/* ... */}
    </div>
  )
}
```

### Shared Props (Global Data)

```typescript
import { usePage } from '@inertiajs/react'

interface SharedProps {
  auth: {
    user: {
      id: number
      name: string
      email: string
    }
  }
  flash: {
    notice?: string
    alert?: string
  }
}

export default function SomeComponent() {
  const { auth, flash } = usePage<SharedProps>().props

  return (
    <div>
      {flash.notice && <div className="alert">{flash.notice}</div>}
      <p>Logged in as: {auth.user.name}</p>
    </div>
  )
}
```

---

## Navigation

### Link Component

```typescript
import { Link } from '@inertiajs/react'

export default function Navigation() {
  return (
    <nav>
      {/* Basic link */}
      <Link href="/posts">Posts</Link>

      {/* With CSS classes */}
      <Link href="/posts" className="nav-link">
        Posts
      </Link>

      {/* Active state */}
      <Link
        href="/posts"
        className={route().current('posts.index') ? 'active' : ''}
      >
        Posts
      </Link>

      {/* Preserve scroll position */}
      <Link href="/posts" preserveScroll>
        Posts
      </Link>

      {/* Preserve state */}
      <Link href="/posts" preserveState>
        Posts
      </Link>

      {/* Open in new tab */}
      <Link href="/posts" target="_blank">
        Posts
      </Link>
    </nav>
  )
}
```

### Manual Visits

```typescript
import { router } from '@inertiajs/react'

// GET request
router.get('/posts')

// POST request
router.post('/posts', {
  title: 'New Post',
  content: 'Content here',
})

// PUT request
router.put(`/posts/${id}`, data)

// PATCH request
router.patch(`/posts/${id}`, data)

// DELETE request
router.delete(`/posts/${id}`)

// Generic visit
router.visit('/posts', {
  method: 'get',
  data: { filter: 'active' },
  preserveScroll: true,
  preserveState: true,
  only: ['posts'], // Partial reload
  onSuccess: (page) => {
    console.log('Success')
  },
  onError: (errors) => {
    console.log('Errors:', errors)
  },
})
```

---

## Forms

### Basic Form with useForm

```typescript
import { useForm } from '@inertiajs/react'

interface Props {
  errors?: Record<string, string>
}

export default function Create({ errors }: Props) {
  const { data, setData, post, processing } = useForm({
    title: '',
    content: '',
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()
    post('/posts')
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label htmlFor="title">Title</label>
        <input
          id="title"
          type="text"
          value={data.title}
          onChange={(e) => setData('title', e.target.value)}
        />
        {errors?.title && <div className="error">{errors.title}</div>}
      </div>

      <div>
        <label htmlFor="content">Content</label>
        <textarea
          id="content"
          value={data.content}
          onChange={(e) => setData('content', e.target.value)}
        />
        {errors?.content && <div className="error">{errors.content}</div>}
      </div>

      <button type="submit" disabled={processing}>
        {processing ? 'Creating...' : 'Create Post'}
      </button>
    </form>
  )
}
```

### Form with All Features

```typescript
import { useForm } from '@inertiajs/react'

interface Post {
  id: number
  title: string
  content: string
}

interface Props {
  post: Post
}

export default function Edit({ post }: Props) {
  const {
    data,
    setData,
    put,
    processing,
    errors,
    reset,
    clearErrors,
    setError,
  } = useForm({
    title: post.title,
    content: post.content,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    put(`/posts/${post.id}`, {
      preserveScroll: true,
      onSuccess: () => {
        reset()
      },
      onError: (errors) => {
        console.log('Validation errors:', errors)
      },
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <div>
        <label>Title</label>
        <input
          type="text"
          value={data.title}
          onChange={(e) => setData('title', e.target.value)}
        />
        {errors.title && <span className="error">{errors.title}</span>}
      </div>

      <div>
        <label>Content</label>
        <textarea
          value={data.content}
          onChange={(e) => setData('content', e.target.value)}
        />
        {errors.content && <span className="error">{errors.content}</span>}
      </div>

      <div className="actions">
        <button type="submit" disabled={processing}>
          Update Post
        </button>
        <button type="button" onClick={() => reset()}>
          Reset
        </button>
      </div>
    </form>
  )
}
```

### File Uploads

```typescript
import { useForm } from '@inertiajs/react'

export default function UploadForm() {
  const { data, setData, post, progress } = useForm({
    title: '',
    file: null as File | null,
  })

  function handleSubmit(e: React.FormEvent) {
    e.preventDefault()

    // Automatically sends as multipart/form-data
    post('/uploads', {
      forceFormData: true,
      onSuccess: () => {
        console.log('Uploaded!')
      },
    })
  }

  return (
    <form onSubmit={handleSubmit}>
      <input
        type="text"
        value={data.title}
        onChange={(e) => setData('title', e.target.value)}
      />

      <input
        type="file"
        onChange={(e) => setData('file', e.target.files?.[0] || null)}
      />

      {progress && (
        <progress value={progress.percentage} max="100">
          {progress.percentage}%
        </progress>
      )}

      <button type="submit">Upload</button>
    </form>
  )
}
```

---

## Error Handling

### Display Validation Errors

```typescript
import { useForm, usePage } from '@inertiajs/react'

interface PageProps {
  errors: Record<string, string>
}

export default function CreatePost() {
  const { errors } = usePage<PageProps>().props
  const { data, setData, post } = useForm({
    title: '',
    content: '',
  })

  return (
    <form onSubmit={(e) => { e.preventDefault(); post('/posts') }}>
      <div>
        <input
          type="text"
          value={data.title}
          onChange={(e) => setData('title', e.target.value)}
        />
        {errors.title && <p className="error">{errors.title}</p>}
      </div>

      <div>
        <textarea
          value={data.content}
          onChange={(e) => setData('content', e.target.value)}
        />
        {errors.content && <p className="error">{errors.content}</p>}
      </div>

      <button type="submit">Create</button>
    </form>
  )
}
```

### Error Bags (Multiple Forms)

```typescript
import { useForm, usePage } from '@inertiajs/react'

interface PageProps {
  errors: {
    createCompany?: Record<string, string>
    createUser?: Record<string, string>
  }
}

export default function MultiFormPage() {
  const { errors } = usePage<PageProps>().props

  const companyForm = useForm({ name: '' })
  const userForm = useForm({ name: '', email: '' })

  function handleCompanySubmit(e: React.FormEvent) {
    e.preventDefault()
    companyForm.post('/companies', {
      errorBag: 'createCompany',
    })
  }

  function handleUserSubmit(e: React.FormEvent) {
    e.preventDefault()
    userForm.post('/users', {
      errorBag: 'createUser',
    })
  }

  return (
    <div>
      <form onSubmit={handleCompanySubmit}>
        <input
          value={companyForm.data.name}
          onChange={(e) => companyForm.setData('name', e.target.value)}
        />
        {errors.createCompany?.name && <p>{errors.createCompany.name}</p>}
        <button type="submit">Create Company</button>
      </form>

      <form onSubmit={handleUserSubmit}>
        <input
          value={userForm.data.name}
          onChange={(e) => userForm.setData('name', e.target.value)}
        />
        {errors.createUser?.name && <p>{errors.createUser.name}</p>}
        <button type="submit">Create User</button>
      </form>
    </div>
  )
}
```

---

## Flash Messages

```typescript
import { usePage } from '@inertiajs/react'
import { useEffect, useState } from 'react'

interface SharedProps {
  flash: {
    notice?: string
    alert?: string
  }
}

export default function FlashMessages() {
  const { flash } = usePage<SharedProps>().props
  const [visible, setVisible] = useState(true)

  useEffect(() => {
    if (flash.notice || flash.alert) {
      setVisible(true)
      const timer = setTimeout(() => setVisible(false), 3000)
      return () => clearTimeout(timer)
    }
  }, [flash])

  if (!visible) return null

  return (
    <div>
      {flash.notice && (
        <div className="alert alert-success">
          {flash.notice}
          <button onClick={() => setVisible(false)}>×</button>
        </div>
      )}

      {flash.alert && (
        <div className="alert alert-danger">
          {flash.alert}
          <button onClick={() => setVisible(false)}>×</button>
        </div>
      )}
    </div>
  )
}
```

---

## Advanced Patterns

### Lazy Loading / Partial Reloads

```typescript
import { router } from '@inertiajs/react'
import { useState } from 'react'

interface Props {
  users: User[]
  stats?: {
    total: number
    active: number
  }
}

export default function Dashboard({ users, stats }: Props) {
  const [loadedStats, setLoadedStats] = useState(false)

  function loadStats() {
    router.reload({
      only: ['stats'],
      onSuccess: () => setLoadedStats(true),
    })
  }

  return (
    <div>
      <h1>Users</h1>
      {users.map(user => <div key={user.id}>{user.name}</div>)}

      {!loadedStats && (
        <button onClick={loadStats}>Load Stats</button>
      )}

      {stats && (
        <div>
          <p>Total: {stats.total}</p>
          <p>Active: {stats.active}</p>
        </div>
      )}
    </div>
  )
}
```

### Prefetching

```typescript
import { Link, router } from '@inertiajs/react'

export default function PostList({ posts }: Props) {
  return (
    <div>
      {posts.map((post) => (
        <Link
          key={post.id}
          href={`/posts/${post.id}`}
          onMouseEnter={() => {
            // Prefetch on hover
            router.prefetch(`/posts/${post.id}`)
          }}
        >
          {post.title}
        </Link>
      ))}
    </div>
  )
}
```

### Infinite Scroll

```typescript
import { router } from '@inertiajs/react'
import { useEffect, useRef, useState } from 'react'

interface Props {
  posts: {
    data: Post[]
    current_page: number
    total_pages: number
  }
}

export default function InfiniteList({ posts: initialPosts }: Props) {
  const [posts, setPosts] = useState(initialPosts.data)
  const [page, setPage] = useState(initialPosts.current_page)
  const [hasMore, setHasMore] = useState(page < initialPosts.total_pages)
  const observerRef = useRef<IntersectionObserver>()
  const lastPostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const observer = new IntersectionObserver((entries) => {
      if (entries[0].isIntersecting && hasMore) {
        loadMore()
      }
    })

    if (lastPostRef.current) {
      observer.observe(lastPostRef.current)
    }

    observerRef.current = observer

    return () => observer.disconnect()
  }, [hasMore, page])

  function loadMore() {
    router.visit(`/posts?page=${page + 1}`, {
      preserveScroll: true,
      preserveState: true,
      only: ['posts'],
      onSuccess: (page) => {
        const newPosts = page.props.posts as typeof initialPosts
        setPosts((prev) => [...prev, ...newPosts.data])
        setPage(newPosts.current_page)
        setHasMore(newPosts.current_page < newPosts.total_pages)
      },
    })
  }

  return (
    <div>
      {posts.map((post, index) => (
        <div
          key={post.id}
          ref={index === posts.length - 1 ? lastPostRef : null}
        >
          {post.title}
        </div>
      ))}
    </div>
  )
}
```

---

## TypeScript Support

### Page Props Interface

```typescript
// app/frontend/types/index.d.ts
export interface User {
  id: number
  name: string
  email: string
  avatar_url?: string
}

export interface PageProps {
  auth: {
    user: User
  }
  flash: {
    notice?: string
    alert?: string
  }
  errors: Record<string, string>
}
```

### Using with Components

```typescript
import { PageProps } from '@/types'
import { usePage } from '@inertiajs/react'

interface Props extends PageProps {
  posts: Post[]
}

export default function Index({ posts }: Props) {
  const { auth } = usePage<PageProps>().props

  return (
    <div>
      <p>Welcome, {auth.user.name}</p>
      {/* ... */}
    </div>
  )
}
```

---

## Best Practices

### 1. Type Your Props

```typescript
// ✅ GOOD
interface Props {
  user: User
  posts: Post[]
}

export default function Dashboard({ user, posts }: Props) {
  // ...
}

// ❌ BAD
export default function Dashboard(props: any) {
  // ...
}
```

### 2. Use Shared Props for Global Data

```typescript
// ✅ GOOD: Access from usePage
const { auth, flash } = usePage<PageProps>().props

// ❌ BAD: Pass on every component
<Dashboard user={user} flash={flash} />
```

### 3. Handle Loading States

```typescript
// ✅ GOOD
const { processing } = useForm({ /*...*/ })

<button disabled={processing}>
  {processing ? 'Saving...' : 'Save'}
</button>

// ❌ BAD: No loading indicator
<button>Save</button>
```

### 4. Clear Errors on Input Change

```typescript
const { data, setData, errors, clearErrors } = useForm({ name: '' })

<input
  value={data.name}
  onChange={(e) => {
    setData('name', e.target.value)
    clearErrors('name') // Clear error when user types
  }}
/>
```

---

## Reference

- Inertia.js Docs: https://inertiajs.com
- React Adapter: https://inertiajs.com/client-side-setup
- Inertia Rails: https://inertia-rails.dev/guide
