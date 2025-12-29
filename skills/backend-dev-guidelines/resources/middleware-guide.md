# Middleware Guide - Laravel Middleware Patterns

Complete guide to creating and using middleware in Laravel applications.

## Table of Contents

- [Authentication Middleware](#authentication-middleware)
- [Audit Middleware with Context](#audit-middleware-with-context)
- [Error Handling Middleware](#error-handling-middleware)
- [Validation Middleware](#validation-middleware)
- [Composable Middleware](#composable-middleware)
- [Middleware Ordering](#middleware-ordering)

---

## Authentication Middleware

### Custom Authentication Middleware Pattern

**File:** `app/Http/Middleware/VerifyAuthentication.php`

```php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Auth;
use Symfony\Component\HttpFoundation\Response;

class VerifyAuthentication
{
    public function handle(Request $request, Closure $next): Response
    {
        if (!Auth::check()) {
            return response()->json(['error' => 'Not authenticated'], 401);
        }

        // Add user info to request for downstream use
        $request->merge([
            'effective_user_id' => Auth::id(),
            'user_claims' => [
                'sub' => Auth::id(),
                'email' => Auth::user()->email,
                'preferred_username' => Auth::user()->name,
            ],
        ]);

        return $next($request);
    }
}
```

### Using Built-in Auth Middleware

```php
// In routes/web.php or routes/api.php
use Illuminate\Support\Facades\Route;

Route::middleware('auth:sanctum')->group(function () {
    Route::get('/users', [UserController::class, 'index']);
});
```

---

## Audit Middleware with Context

### Excellent Pattern with Request Context

**File:** `app/Http/Middleware/AuditContext.php`

```php
namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;
use Illuminate\Support\Facades\Context;
use Illuminate\Support\Str;
use Symfony\Component\HttpFoundation\Response;

class AuditContext
{
    public function handle(Request $request, Closure $next): Response
    {
        $userId = $request->user()?->id ?? 'anonymous';
        $userName = $request->user()?->name;

        // Set context using Laravel's Context facade
        Context::add('audit', [
            'user_id' => $userId,
            'user_name' => $userName,
            'impersonated_by' => $request->get('impersonated_by'),
            'timestamp' => now(),
            'request_id' => (string) Str::uuid(),
        ]);

        return $next($request);
    }
}
```

**Benefits:**
- Context propagates through entire request
- Automatically available in services, repositories
- Type-safe context access via Laravel's Context facade
- Works with logs, Sentry, and monitoring

**Usage in Services:**

```php
namespace App\Services;

use Illuminate\Support\Facades\Context;

class SomeService
{
    public function performOperation(): void
    {
        $auditContext = Context::get('audit');

        logger()->info('Operation performed', [
            'user_id' => $auditContext['user_id'],
            'request_id' => $auditContext['request_id'],
        ]);
    }
}
```

---

## Error Handling Middleware

### Comprehensive Error Handler

**Note:** Laravel's exception handler in `app/Exceptions/Handler.php` handles this:

```php
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Throwable;
use Sentry\Laravel\Integration;

class Handler extends ExceptionHandler
{
    protected $dontReport = [
        // Exceptions that shouldn't be reported to Sentry
    ];

    public function register(): void
    {
        $this->reportable(function (Throwable $e) {
            if (app()->bound('sentry')) {
                Integration::captureUnhandledException($e);
            }
        });
    }

    public function render($request, Throwable $e)
    {
        $statusCode = $this->getStatusCode($e);

        return response()->json([
            'success' => false,
            'error' => [
                'message' => $e->getMessage(),
                'code' => class_basename($e),
            ],
            'request_id' => Context::get('audit.request_id'),
        ], $statusCode);
    }

    private function getStatusCode(Throwable $e): int
    {
        return method_exists($e, 'getStatusCode')
            ? $e->getStatusCode()
            : 500;
    }
}
```

---

## Validation Middleware

### Using Form Requests (Preferred)

```php
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // or custom authorization logic
    }

    public function rules(): array
    {
        return [
            'email' => 'required|email|unique:users',
            'name' => 'required|string|max:255',
            'age' => 'required|integer|min:18',
        ];
    }

    public function messages(): array
    {
        return [
            'age.min' => 'User must be at least 18 years old',
        ];
    }
}
```

**Usage in Controller:**

```php
public function store(CreateUserRequest $request)
{
    // Validation happens automatically
    $validated = $request->validated();

    $user = User::create($validated);

    return response()->json($user, 201);
}
```

---

## Composable Middleware

### Middleware Groups

**File:** `app/Http/Kernel.php` or `bootstrap/app.php` (Laravel 11+)

```php
// Laravel 11+ bootstrap/app.php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->group('api_with_audit', [
            'auth:sanctum',
            \App\Http\Middleware\AuditContext::class,
        ]);
    })
    ->create();
```

**Usage:**

```php
// In routes/api.php
Route::middleware('api_with_audit')->group(function () {
    Route::post('/forms/{id}/submit', [FormController::class, 'submit']);
});
```

---

## Middleware Ordering

### Critical Order (Must Follow)

**Laravel 11+ (`bootstrap/app.php`):**

```php
use Illuminate\Foundation\Application;
use Illuminate\Foundation\Configuration\Middleware;

return Application::configure(basePath: dirname(__DIR__))
    ->withMiddleware(function (Middleware $middleware) {
        $middleware->priority([
            // 1. Sentry tracking (FIRST)
            \Sentry\Laravel\Http\Middleware\TracingMiddleware::class,

            // 2. Session handling
            \Illuminate\Session\Middleware\StartSession::class,

            // 3. Cookie handling
            \Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse::class,

            // 4. CSRF protection
            \Illuminate\Foundation\Http\Middleware\ValidateCsrfToken::class,

            // 5. Authentication
            \Illuminate\Auth\Middleware\Authenticate::class,

            // 6. Your custom middleware
            \App\Http\Middleware\AuditContext::class,
        ]);
    })
    ->create();
```

**Laravel 10 and earlier (`app/Http/Kernel.php`):**

```php
protected $middlewarePriority = [
    // 1. Sentry tracking (FIRST)
    \Sentry\Laravel\Http\Middleware\TracingMiddleware::class,

    // 2. Session handling
    \Illuminate\Session\Middleware\StartSession::class,

    // 3. Authentication
    \Illuminate\Auth\Middleware\Authenticate::class,

    // 4. Your custom middleware
    \App\Http\Middleware\AuditContext::class,
];
```

**Rule:** Middleware runs in the order defined in the priority array!

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [routing-and-controllers.md](routing-and-controllers.md)
- [async-and-errors.md](async-and-errors.md)
