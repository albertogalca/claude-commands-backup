---
name: backend-dev-guidelines
description: Comprehensive backend development guide for Laravel + Inertia.js applications. Use when creating routes, controllers, services, repositories, middleware, models, or working with Laravel APIs, Eloquent ORM, Inertia.js responses, validation, dependency injection, or async patterns. Covers layered architecture (routes → controllers → services → repositories), controller patterns, error handling, performance monitoring, testing strategies, and Laravel best practices.
---

# Backend Development Guidelines

## Purpose

Establish consistency and best practices for Laravel + Inertia.js applications using modern PHP/Laravel patterns.

## When to Use This Skill

Automatically activates when working on:
- Creating or modifying routes, endpoints, APIs
- Building controllers, services, repositories
- Implementing middleware (auth, validation, error handling)
- Database operations with Eloquent ORM
- Error tracking and logging
- Input validation with Form Requests
- Configuration management
- Inertia.js responses and shared data
- Backend testing and refactoring

---

## Quick Start

### New Backend Feature Checklist

- [ ] **Route**: Clean definition in routes/web.php or routes/api.php
- [ ] **Controller**: Invokable or resource controller
- [ ] **Service**: Business logic with DI (if needed)
- [ ] **Repository**: Database access (if complex queries)
- [ ] **Form Request**: Validation rules
- [ ] **Model**: Eloquent model with relationships
- [ ] **Resource**: API resource for transformations (if API)
- [ ] **Tests**: Feature + unit tests
- [ ] **Config**: Use .env and config files

### New Laravel Module Checklist

- [ ] Directory structure (see [architecture-overview.md](architecture-overview.md))
- [ ] Service provider registration (if needed)
- [ ] Middleware registration
- [ ] Model factories and seeders
- [ ] Database migrations
- [ ] Exception handling
- [ ] Testing setup (Feature + Unit)

---

## Architecture Overview

### Layered Architecture

```
HTTP Request
    ↓
Routes (routing only)
    ↓
Middleware (auth, validation, etc.)
    ↓
Controllers (request handling)
    ↓
Form Requests (validation)
    ↓
Services (business logic)
    ↓
Repositories (data access)
    ↓
Models (Eloquent ORM)
    ↓
Database
```

**Key Principle:** Each layer has ONE responsibility.

See [architecture-overview.md](architecture-overview.md) for complete details.

---

## Directory Structure

```
app/
├── Http/
│   ├── Controllers/       # Request handlers
│   ├── Requests/          # Form validation
│   ├── Middleware/        # Middleware
│   └── Resources/         # API resources
├── Services/              # Business logic
├── Repositories/          # Data access
├── Models/                # Eloquent models
├── Exceptions/            # Custom exceptions
└── Providers/             # Service providers
bootstrap/
config/                    # Configuration files
database/
├── migrations/            # Database migrations
├── factories/             # Model factories
└── seeders/              # Database seeders
routes/
├── web.php               # Web routes (Inertia)
├── api.php               # API routes
└── console.php           # Artisan commands
resources/
├── js/                   # Inertia.js frontend
│   ├── Pages/            # Inertia pages
│   └── Components/       # React components
└── views/                # Blade templates (if needed)
tests/
├── Feature/              # Feature tests
└── Unit/                 # Unit tests
```

**Naming Conventions:**
- Controllers: `PascalCase` - `UserController.php`
- Services: `PascalCase` - `UserService.php`
- Models: `PascalCase` - `User.php`
- Repositories: `PascalCase` - `UserRepository.php`
- Requests: `PascalCase` - `StoreUserRequest.php`

---

## Core Principles (7 Key Rules)

### 1. Routes Only Route, Controllers Control

```php
// ❌ NEVER: Business logic in routes
Route::post('/submit', function (Request $request) {
    // 200 lines of logic
});

// ✅ ALWAYS: Delegate to controller
Route::post('/submit', [SubmitController::class, 'store']);
// Or use invokable controller
Route::post('/submit', SubmitController::class);
```

### 2. Use Form Requests for Validation

```php
// ✅ ALWAYS: Dedicated Form Request class
class StoreUserRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'email' => ['required', 'email', 'unique:users'],
            'name' => ['required', 'string', 'max:255'],
        ];
    }
}

// Controller
public function store(StoreUserRequest $request)
{
    // $request->validated() is already validated
}
```

### 3. Return Inertia Responses for Pages

```php
use Inertia\Inertia;

public function index()
{
    return Inertia::render('Users/Index', [
        'users' => User::paginate(10),
    ]);
}
```

### 4. Use config(), NEVER env()

```php
// ❌ NEVER (except in config files)
$timeout = env('TIMEOUT_MS');

// ✅ ALWAYS
$timeout = config('app.timeout');
```

### 5. Use Eloquent Relationships

```php
// ✅ Define relationships in models
class User extends Model
{
    public function posts()
    {
        return $this->hasMany(Post::class);
    }
}

// Use eager loading to avoid N+1
$users = User::with('posts')->get();
```

### 6. Use Repository Pattern for Complex Queries

```php
// Service → Repository → Model
$users = $this->userRepository->findActive();
```

### 7. Comprehensive Testing Required

```php
// Feature test
test('user can create post', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->post('/posts', ['title' => 'Test']);

    $response->assertRedirect();
    expect(Post::count())->toBe(1);
});
```

---

## Common Imports

```php
// Laravel Core
use Illuminate\Http\Request;
use Illuminate\Http\RedirectResponse;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Route;

// Validation
use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

// Database
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasMany;
use Illuminate\Support\Facades\DB;

// Inertia
use Inertia\Inertia;
use Inertia\Response as InertiaResponse;

// Resources
use Illuminate\Http\Resources\Json\JsonResource;
use Illuminate\Http\Resources\Json\ResourceCollection;

// Middleware
use Illuminate\Auth\Middleware\Authenticate;
use App\Http\Middleware\HandleInertiaRequests;

// Exceptions
use Illuminate\Validation\ValidationException;
```

---

## Quick Reference

### HTTP Status Codes

| Code | Use Case |
|------|----------|
| 200 | Success |
| 201 | Created |
| 400 | Bad Request |
| 401 | Unauthorized |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Server Error |

### Laravel Patterns

**Invokable Controllers** - Single action controllers
**Resource Controllers** - RESTful resource operations
**Form Requests** - Validation logic extraction
**API Resources** - Data transformation layer

---

## Anti-Patterns to Avoid

❌ Business logic in routes
❌ Direct env() usage (use config())
❌ Missing error handling
❌ No input validation
❌ N+1 query problems (use eager loading)
❌ Mass assignment vulnerabilities (use $fillable)
❌ Raw queries without parameter binding

---

## Navigation Guide

| Need to... | Read this |
|------------|-----------|
| Understand architecture | [architecture-overview.md](architecture-overview.md) |
| Create routes/controllers | [routing-and-controllers.md](routing-and-controllers.md) |
| Organize business logic | [services-and-repositories.md](services-and-repositories.md) |
| Validate input | [validation-patterns.md](validation-patterns.md) |
| Add error tracking | [sentry-and-monitoring.md](sentry-and-monitoring.md) |
| Create middleware | [middleware-guide.md](middleware-guide.md) |
| Database access | [database-patterns.md](database-patterns.md) |
| Manage config | [configuration.md](configuration.md) |
| Handle async/errors | [async-and-errors.md](async-and-errors.md) |
| Write tests | [testing-guide.md](testing-guide.md) |
| See examples | [complete-examples.md](complete-examples.md) |

---

## Resource Files

### [architecture-overview.md](architecture-overview.md)
Layered architecture, request lifecycle, separation of concerns

### [routing-and-controllers.md](routing-and-controllers.md)
Route definitions, BaseController, error handling, examples

### [services-and-repositories.md](services-and-repositories.md)
Service patterns, DI, repository pattern, caching

### [validation-patterns.md](validation-patterns.md)
Zod schemas, validation, DTO pattern

### [sentry-and-monitoring.md](sentry-and-monitoring.md)
Sentry init, error capture, performance monitoring

### [middleware-guide.md](middleware-guide.md)
Auth, audit, error boundaries, AsyncLocalStorage

### [database-patterns.md](database-patterns.md)
PrismaService, repositories, transactions, optimization

### [configuration.md](configuration.md)
UnifiedConfig, environment configs, secrets

### [async-and-errors.md](async-and-errors.md)
Async patterns, custom errors, asyncErrorWrapper

### [testing-guide.md](testing-guide.md)
Unit/integration tests, mocking, coverage

### [complete-examples.md](complete-examples.md)
Full examples, refactoring guide

---

## Related Skills

- **frontend-dev-guidelines** - Inertia.js + React/TypeScript patterns
- **error-tracking** - Error tracking and logging patterns
- **skill-developer** - Meta-skill for creating and managing skills

---

**Skill Status**: COMPLETE ✅
**Line Count**: < 500 ✅
**Progressive Disclosure**: 11 resource files ✅
