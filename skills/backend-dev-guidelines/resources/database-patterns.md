# Database Patterns - Eloquent ORM Best Practices

Complete guide to database access patterns using Eloquent ORM in Laravel applications.

## Table of Contents

- [Eloquent Model Usage](#eloquent-model-usage)
- [Repository Pattern](#repository-pattern)
- [Transaction Patterns](#transaction-patterns)
- [Query Optimization](#query-optimization)
- [N+1 Query Prevention](#n1-query-prevention)
- [Error Handling](#error-handling)

---

## Eloquent Model Usage

### Basic Pattern

```php
use App\Models\User;

// Always use Eloquent models directly or through repositories
$users = User::all();
$user = User::find($id);
```

### Model Definition

```php
namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasOne;

class User extends Model
{
    protected $fillable = ['email', 'name', 'is_active'];

    protected $casts = [
        'is_active' => 'boolean',
        'created_at' => 'datetime',
    ];

    public function profile(): HasOne
    {
        return $this->hasOne(UserProfile::class);
    }
}
```

---

## Repository Pattern

### Why Use Repositories

✅ **Use repositories when:**
- Complex queries with joins/eager loading
- Query used in multiple places
- Need caching layer
- Want to mock for testing

❌ **Skip repositories for:**
- Simple one-off queries
- Prototyping (can refactor later)

### Repository Template

```php
namespace App\Repositories;

use App\Models\User;
use Illuminate\Database\Eloquent\Collection;

class UserRepository
{
    public function findById(int $id): ?User
    {
        return User::with('profile')->find($id);
    }

    public function findActive(): Collection
    {
        return User::where('is_active', true)
            ->orderBy('created_at', 'desc')
            ->get();
    }

    public function create(array $data): User
    {
        return User::create($data);
    }
}
```

---

## Transaction Patterns

### Simple Transaction

```php
use Illuminate\Support\Facades\DB;

$result = DB::transaction(function () use ($userData) {
    $user = User::create($userData);

    $profile = $user->profile()->create([
        'first_name' => $userData['first_name'],
        'last_name' => $userData['last_name'],
    ]);

    return ['user' => $user, 'profile' => $profile];
});
```

### Manual Transaction Control

```php
use Illuminate\Support\Facades\DB;

DB::beginTransaction();

try {
    $user = User::find($id);

    if (!$user) {
        throw new \Exception('User not found');
    }

    $user->update(['last_login' => now()]);

    DB::commit();
} catch (\Exception $e) {
    DB::rollBack();
    throw $e;
}
```

---

## Query Optimization

### Use select to Limit Fields

```php
// ❌ Fetches all fields
$users = User::all();

// ✅ Only fetch needed fields
$users = User::select(['id', 'email'])
    ->with('profile:id,user_id,first_name,last_name')
    ->get();
```

### Use Eager Loading Carefully

```php
// ❌ Excessive eager loading
$user = User::with([
    'profile',
    'posts.comments',
    'workflows.steps.actions',
])->find($id);

// ✅ Only eager load what you need
$user = User::with('profile')->find($id);
```

---

## N+1 Query Prevention

### Problem: N+1 Queries

```php
// ❌ N+1 Query Problem
$users = User::all(); // 1 query

foreach ($users as $user) {
    // N queries (one per user)
    $profile = $user->profile;
}
```

### Solution: Use Eager Loading

```php
// ✅ Single query with eager loading
$users = User::with('profile')->get();

// ✅ Conditional eager loading
$users = User::when($includeProfile, function ($query) {
    $query->with('profile');
})->get();

// ✅ Or batch query
$userIds = $users->pluck('id');
$profiles = UserProfile::whereIn('user_id', $userIds)->get();
```

### Laravel Debugbar for Detection

```php
// Install Laravel Debugbar to detect N+1 queries
// composer require barryvdh/laravel-debugbar --dev

// Will show all queries executed in the request
```

---

## Error Handling

### Eloquent Exception Types

```php
use Illuminate\Database\QueryException;
use Illuminate\Database\Eloquent\ModelNotFoundException;

try {
    $user = User::create($data);
} catch (QueryException $e) {
    // Unique constraint violation
    if ($e->getCode() === '23000') {
        throw new \App\Exceptions\ConflictException('Email already exists');
    }

    // Foreign key constraint
    if (str_contains($e->getMessage(), 'foreign key constraint')) {
        throw new \App\Exceptions\ValidationException('Invalid reference');
    }

    // Log and rethrow
    \Sentry\captureException($e);
    throw $e;
} catch (ModelNotFoundException $e) {
    throw new \App\Exceptions\NotFoundException('Record not found');
}
```

### Using findOrFail

```php
// Automatically throws ModelNotFoundException if not found
$user = User::findOrFail($id);

// firstOrFail for query chains
$user = User::where('email', $email)->firstOrFail();
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [services-and-repositories.md](services-and-repositories.md)
- [async-and-errors.md](async-and-errors.md)
