# Routing and Controllers - Best Practices

Complete guide to clean route definitions and controller patterns in Laravel.

## Table of Contents

- [Routes: Routing Only](#routes-routing-only)
- [Controller Pattern](#controller-pattern)
- [Good Examples](#good-examples)
- [Anti-Patterns](#anti-patterns)
- [Refactoring Guide](#refactoring-guide)
- [Error Handling](#error-handling)
- [HTTP Status Codes](#http-status-codes)

---

## Routes: Routing Only

### The Golden Rule

**Routes should ONLY:**
- ✅ Define route paths
- ✅ Register middleware
- ✅ Delegate to controllers

**Routes should NEVER:**
- ❌ Contain business logic
- ❌ Access database directly
- ❌ Implement validation logic (use Form Requests)
- ❌ Format complex responses
- ❌ Handle complex error scenarios

### Clean Route Pattern

```php
// routes/web.php or routes/api.php
use App\Http\Controllers\UserController;
use App\Http\Middleware\AuditMiddleware;

// ✅ CLEAN: Route definition only
Route::middleware(['auth', AuditMiddleware::class])->group(function () {
    Route::get('/users/{id}', [UserController::class, 'show']);
    Route::post('/users', [UserController::class, 'store']);
    Route::put('/users/{id}', [UserController::class, 'update']);
    Route::delete('/users/{id}', [UserController::class, 'destroy']);
});
```

**Key Points:**
- Each route: method, path, middleware chain, controller delegation
- No try-catch needed (controller handles errors)
- Clean, readable, maintainable
- Easy to see all endpoints at a glance

---

## Controller Pattern

### Why Use Controllers?

**Benefits:**
- Consistent error handling across all endpoints
- Automatic exception tracking with Sentry
- Standardized response formats
- Reusable helper methods
- Performance tracking utilities
- Logging and breadcrumb helpers

### Base Controller Pattern (Template)

**File:** `app/Http/Controllers/Controller.php`

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Foundation\Validation\ValidatesRequests;
use Illuminate\Routing\Controller as BaseController;
use Illuminate\Http\JsonResponse;
use Sentry\Laravel\Facade as Sentry;

abstract class Controller extends BaseController
{
    use AuthorizesRequests, ValidatesRequests;

    /**
     * Handle success responses
     */
    protected function handleSuccess(
        mixed $data,
        ?string $message = null,
        int $statusCode = 200
    ): JsonResponse {
        return response()->json([
            'success' => true,
            'message' => $message,
            'data' => $data,
        ], $statusCode);
    }

    /**
     * Handle error responses
     */
    protected function handleError(
        \Throwable $error,
        string $context,
        int $statusCode = 500
    ): JsonResponse {
        Sentry::withScope(function ($scope) use ($error, $context) {
            $scope->setTag('controller', static::class);
            $scope->setTag('operation', $context);
            $scope->setUser(['id' => auth()->id()]);

            $scope->setContext('error_details', [
                'message' => $error->getMessage(),
                'file' => $error->getFile(),
                'line' => $error->getLine(),
            ]);

            Sentry::captureException($error);
        });

        return response()->json([
            'success' => false,
            'error' => [
                'message' => $error->getMessage(),
                'code' => $statusCode,
            ],
        ], $statusCode);
    }

    /**
     * Add Sentry breadcrumb
     */
    protected function addBreadcrumb(
        string $message,
        string $category,
        array $data = []
    ): void {
        Sentry::addBreadcrumb([
            'message' => $message,
            'category' => $category,
            'level' => 'info',
            'data' => $data,
        ]);
    }

    /**
     * Log info message
     */
    protected function logInfo(string $message, array $context = []): void
    {
        Sentry::addBreadcrumb([
            'category' => static::class,
            'message' => $message,
            'level' => 'info',
            'data' => $context,
        ]);
    }

    /**
     * Log warning message
     */
    protected function logWarning(string $message, array $context = []): void
    {
        Sentry::captureMessage($message, [
            'level' => 'warning',
            'tags' => ['controller' => static::class],
            'extra' => $context,
        ]);
    }

    /**
     * Capture custom metric
     */
    protected function captureMetric(string $name, float $value, string $unit): void
    {
        Sentry::metrics()->gauge($name, $value, ['unit' => $unit]);
    }
}
```

### Using Controller Pattern

```php
<?php

namespace App\Http\Controllers;

use App\Http\Requests\CreateUserRequest;
use App\Http\Requests\UpdateUserRequest;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class UserController extends Controller
{
    public function __construct(
        private UserService $userService
    ) {}

    public function show(string $id): JsonResponse
    {
        try {
            $this->addBreadcrumb('Fetching user', 'user_controller', ['userId' => $id]);

            $user = $this->userService->findById($id);

            if (!$user) {
                return $this->handleError(
                    new \Exception('User not found'),
                    'show',
                    404
                );
            }

            return $this->handleSuccess($user);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'show');
        }
    }

    public function store(CreateUserRequest $request): JsonResponse
    {
        try {
            // Validated data from Form Request
            $validated = $request->validated();

            $user = $this->userService->create($validated);

            return $this->handleSuccess($user, 'User created successfully', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }

    public function update(UpdateUserRequest $request, string $id): JsonResponse
    {
        try {
            $validated = $request->validated();

            $user = $this->userService->update($id, $validated);

            return $this->handleSuccess($user, 'User updated');
        } catch (\Throwable $e) {
            return $this->handleError($e, 'update');
        }
    }

    public function destroy(string $id): JsonResponse
    {
        try {
            $this->userService->delete($id);

            return $this->handleSuccess(null, 'User deleted', 204);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'destroy');
        }
    }
}
```

**Benefits:**
- Consistent error handling
- Automatic Sentry integration
- Performance tracking
- Clean, readable code
- Easy to test

---

## Good Examples

### Example 1: Email Notification Routes (Excellent ✅)

**File:** `routes/api.php`

```php
use App\Http\Controllers\NotificationController;

Route::middleware(['auth'])->group(function () {
    // ✅ EXCELLENT: Clean delegation
    Route::get('/notifications', [NotificationController::class, 'index']);
    Route::post('/notifications', [NotificationController::class, 'store']);
    Route::put('/notifications/{id}/read', [NotificationController::class, 'markAsRead']);
});
```

**What Makes This Excellent:**
- Zero business logic in routes
- Clear middleware chain
- Consistent pattern
- Easy to understand

### Example 2: Resource Routes with Validation (Good ✅)

```php
use App\Http\Controllers\ProxyController;
use App\Http\Middleware\AuditMiddleware;

Route::middleware(['auth', AuditMiddleware::class])->group(function () {
    Route::apiResource('proxies', ProxyController::class);
});
```

```php
<?php

namespace App\Http\Controllers;

use App\Http\Requests\CreateProxyRequest;
use App\Services\ProxyService;
use Illuminate\Http\JsonResponse;

class ProxyController extends Controller
{
    public function __construct(
        private ProxyService $proxyService
    ) {}

    public function store(CreateProxyRequest $request): JsonResponse
    {
        try {
            $validated = $request->validated();
            $proxy = $this->proxyService->createProxyRelationship($validated);

            return $this->handleSuccess($proxy, 'Proxy created', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }
}
```

**What Makes This Good:**
- Form Request validation
- Delegates to service
- Proper HTTP status codes
- Error handling

---

## Anti-Patterns

### Anti-Pattern 1: Business Logic in Routes (Bad ❌)

```php
// ❌ ANTI-PATTERN: 200+ lines of business logic in route
Route::post('/forms/{formID}/submit', function (Request $request, $formID) {
    $username = auth()->user()->email;
    $responses = $request->input('responses');
    $stepInstanceId = $request->input('stepInstanceId');

    // ❌ Permission checking in route
    $user = app(UserProfileService::class)->getProfileByEmail($username);
    $canComplete = app(PermissionService::class)->canCompleteStep($user->id, $stepInstanceId);

    if (!$canComplete) {
        return response()->json(['error' => 'No permission'], 403);
    }

    // ❌ Workflow logic in route
    $engine = app(WorkflowEngine::class);
    $command = new CompleteStepCommand(
        $stepInstanceId,
        $user->id,
        $responses
    );
    $events = $engine->executeCommand($command);

    // ❌ Impersonation handling in route
    if (session('isImpersonating')) {
        app(ImpersonationContextStore::class)->storeContext($stepInstanceId, [
            'originalUserId' => session('originalUserId'),
            'effectiveUserId' => $user->id,
        ]);
    }

    // ... 100+ more lines of business logic

    return response()->json(['success' => true, 'data' => $result]);
});
```

**Why This Is Terrible:**
- 200+ lines of business logic
- Hard to test (requires HTTP mocking)
- Hard to reuse (tied to route)
- Mixed responsibilities
- Difficult to debug
- Performance tracking difficult

### How to Refactor (Step-by-Step)

**Step 1: Create Controller**

```php
<?php

namespace App\Http\Controllers;

use App\Http\Requests\CreatePostRequest;
use App\Services\PostService;
use Illuminate\Http\JsonResponse;

class PostController extends Controller
{
    public function __construct(
        private PostService $postService
    ) {}

    public function store(CreatePostRequest $request): JsonResponse
    {
        try {
            $validated = $request->validated();
            $result = $this->postService->createPost($validated, auth()->id());

            return $this->handleSuccess($result, 'Post created successfully');
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }
}
```

**Step 2: Create Service**

```php
<?php

namespace App\Services;

use App\Exceptions\ForbiddenException;
use App\Repositories\PostRepository;

class PostService
{
    public function __construct(
        private PostRepository $postRepository,
        private PermissionService $permissionService,
        private WorkflowEngine $workflowEngine
    ) {}

    public function createPost(array $data, string $userId): array
    {
        // Permission check
        if (!$this->permissionService->canCreatePost($userId)) {
            throw new ForbiddenException('No permission to create post');
        }

        // Execute workflow
        $command = new CompleteStepCommand($data['stepInstanceId'], $userId, $data['responses']);
        $events = $this->workflowEngine->executeCommand($command);

        // Handle impersonation if needed
        if (session('isImpersonating')) {
            $this->handleImpersonation($data['stepInstanceId']);
        }

        return ['events' => $events, 'success' => true];
    }

    private function handleImpersonation(int $stepInstanceId): void
    {
        // Impersonation logic
    }
}
```

**Step 3: Update Route**

```php
use App\Http\Controllers\PostController;

// ✅ CLEAN: Just routing
Route::middleware(['auth', 'audit'])->group(function () {
    Route::post('/posts', [PostController::class, 'store']);
});
```

**Result:**
- Route: 3 lines (was 200+)
- Controller: 25 lines (request handling)
- Service: 50 lines (business logic)
- Testable, reusable, maintainable!

---

## Error Handling

### Controller Error Handling

```php
public function store(CreateUserRequest $request): JsonResponse
{
    try {
        $result = $this->userService->create($request->validated());
        return $this->handleSuccess($result, 'User created', 201);
    } catch (\Throwable $e) {
        // Controller::handleError automatically:
        // - Captures to Sentry with context
        // - Sets appropriate status code
        // - Returns formatted error response
        return $this->handleError($e, 'store');
    }
}
```

### Custom Error Status Codes

```php
public function show(string $id): JsonResponse
{
    try {
        $user = $this->userService->findById($id);

        if (!$user) {
            // Custom 404 status
            return $this->handleError(
                new \Exception('User not found'),
                'show',
                404
            );
        }

        return $this->handleSuccess($user);
    } catch (\Throwable $e) {
        return $this->handleError($e, 'show');
    }
}
```

### Validation Errors

```php
public function store(CreateUserRequest $request): JsonResponse
{
    try {
        // Form Request handles validation automatically
        // ValidationException thrown if validation fails
        $user = $this->userService->create($request->validated());
        return $this->handleSuccess($user, 'User created', 201);
    } catch (\Illuminate\Validation\ValidationException $e) {
        // Validation errors get 422 status
        return response()->json([
            'success' => false,
            'errors' => $e->errors(),
        ], 422);
    } catch (\Throwable $e) {
        return $this->handleError($e, 'store');
    }
}
```

---

## HTTP Status Codes

### Standard Codes

| Code | Use Case | Example |
|------|----------|---------|
| 200 | Success (GET, PUT) | User retrieved, Updated |
| 201 | Created (POST) | User created |
| 204 | No Content (DELETE) | User deleted |
| 400 | Bad Request | Invalid input data |
| 401 | Unauthorized | Not authenticated |
| 403 | Forbidden | No permission |
| 404 | Not Found | Resource doesn't exist |
| 409 | Conflict | Duplicate resource |
| 422 | Unprocessable Entity | Validation failed |
| 500 | Internal Server Error | Unexpected error |

### Usage Examples

```php
// 200 - Success (default)
return $this->handleSuccess($user);

// 201 - Created
return $this->handleSuccess($user, 'Created', 201);

// 400 - Bad Request
return $this->handleError($error, 'operation', 400);

// 404 - Not Found
return $this->handleError(new \Exception('Not found'), 'operation', 404);

// 403 - Forbidden
return $this->handleError(new ForbiddenException('No permission'), 'operation', 403);
```

---

## Refactoring Guide

### Identify Routes Needing Refactoring

**Red Flags:**
- Route file > 100 lines
- Multiple try-catch blocks in closures
- Direct Eloquent access in routes
- Complex business logic (if statements, loops)
- Permission checks in routes

**Check your routes:**
```bash
# Find large route files
wc -l routes/*.php | sort -n

# Find routes with Eloquent usage
grep -r "::create\|::update\|::find" routes/
```

### Refactoring Process

**1. Extract to Controller:**
```php
// Before: Route with logic
Route::post('/action', function (Request $request) {
    // 50 lines of logic
});

// After: Clean route
Route::post('/action', [ActionController::class, 'perform']);

// New controller method
public function perform(Request $request): JsonResponse
{
    try {
        $result = $this->actionService->perform($request->all());
        return $this->handleSuccess($result);
    } catch (\Throwable $e) {
        return $this->handleError($e, 'perform');
    }
}
```

**2. Extract to Service:**
```php
// Controller stays thin
public function perform(PerformActionRequest $request): JsonResponse
{
    try {
        $validated = $request->validated();
        $result = $this->actionService->execute($validated);
        return $this->handleSuccess($result);
    } catch (\Throwable $e) {
        return $this->handleError($e, 'perform');
    }
}

// Service contains business logic
class ActionService
{
    public function execute(array $data): array
    {
        // All business logic here
        // Permission checks
        // Database operations
        // Complex transformations
        return $result;
    }
}
```

**3. Add Repository (if needed):**
```php
// Service calls repository
class ActionService
{
    public function __construct(
        private ActionRepository $actionRepository
    ) {}

    public function execute(array $data): array
    {
        // Business logic
        $entity = $this->actionRepository->findById($data['id']);
        // More logic
        return $this->actionRepository->update($data['id'], $changes);
    }
}

// Repository handles data access
class ActionRepository
{
    public function findById(int $id): ?Entity
    {
        return Entity::find($id);
    }

    public function update(int $id, array $data): Entity
    {
        $entity = Entity::findOrFail($id);
        $entity->update($data);
        return $entity;
    }
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main guide
- [services-and-repositories.md](services-and-repositories.md) - Service layer details
- [complete-examples.md](complete-examples.md) - Full refactoring examples
