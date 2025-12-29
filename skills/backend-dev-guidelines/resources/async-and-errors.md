# Error Handling and Async Patterns in Laravel

Complete guide to error handling and asynchronous operations in Laravel.

## Table of Contents

- [Error Handling Best Practices](#error-handling-best-practices)
- [Custom Error Types](#custom-error-types)
- [Exception Handler](#exception-handler)
- [Async Operations (Queues)](#async-operations-queues)
- [Error Propagation](#error-propagation)
- [Common Pitfalls](#common-pitfalls)

---

## Error Handling Best Practices

### Always Use Try-Catch in Services

```php
// ❌ NEVER: Unhandled exceptions
public function fetchData()
{
    $data = $this->repository->query(); // If throws, unhandled!
    return $data;
}

// ✅ ALWAYS: Wrap in try-catch
public function fetchData()
{
    try {
        $data = $this->repository->query();
        return $data;
    } catch (\Throwable $e) {
        \Sentry\captureException($e);
        throw $e;
    }
}
```

### Controller Error Handling

```php
namespace App\Http\Controllers;

use Illuminate\Http\JsonResponse;

class UserController extends BaseController
{
    public function store(Request $request): JsonResponse
    {
        try {
            $user = $this->userService->create($request->validated());

            return $this->handleSuccess($user, 'User created', 201);
        } catch (\App\Exceptions\ValidationException $e) {
            return $this->handleError($e, 'store', 400);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store', 500);
        }
    }
}
```

---

## Custom Error Types

### Define Custom Exceptions

```php
namespace App\Exceptions;

use Exception;

// Base exception class
class AppException extends Exception
{
    protected int $statusCode = 500;
    protected bool $isOperational = true;

    public function __construct(
        string $message,
        string $code = '',
        int $statusCode = 500,
        bool $isOperational = true
    ) {
        parent::__construct($message, 0);
        $this->code = $code;
        $this->statusCode = $statusCode;
        $this->isOperational = $isOperational;
    }

    public function getStatusCode(): int
    {
        return $this->statusCode;
    }

    public function isOperational(): bool
    {
        return $this->isOperational;
    }
}

// Specific error types
class ValidationException extends AppException
{
    public function __construct(string $message)
    {
        parent::__construct($message, 'VALIDATION_ERROR', 400);
    }
}

class NotFoundException extends AppException
{
    public function __construct(string $message)
    {
        parent::__construct($message, 'NOT_FOUND', 404);
    }
}

class ForbiddenException extends AppException
{
    public function __construct(string $message)
    {
        parent::__construct($message, 'FORBIDDEN', 403);
    }
}

class ConflictException extends AppException
{
    public function __construct(string $message)
    {
        parent::__construct($message, 'CONFLICT', 409);
    }
}
```

### Usage

```php
use App\Exceptions\{NotFoundException, ValidationException};

// Throw specific errors
if (!$user) {
    throw new NotFoundException('User not found');
}

if ($user->age < 18) {
    throw new ValidationException('User must be 18+');
}
```

---

## Exception Handler

### Centralized Error Handling

**File:** `app/Exceptions/Handler.php`

```php
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Illuminate\Http\JsonResponse;
use Illuminate\Support\Facades\Context;
use Throwable;

class Handler extends ExceptionHandler
{
    protected $dontReport = [
        \Illuminate\Auth\AuthenticationException::class,
        \Illuminate\Validation\ValidationException::class,
    ];

    public function register(): void
    {
        $this->reportable(function (Throwable $e) {
            if (app()->bound('sentry')) {
                \Sentry\Laravel\Integration::captureUnhandledException($e);
            }
        });
    }

    public function render($request, Throwable $e): mixed
    {
        // Handle custom app exceptions
        if ($e instanceof AppException) {
            return response()->json([
                'success' => false,
                'error' => [
                    'message' => $e->getMessage(),
                    'code' => $e->getCode(),
                ],
                'request_id' => Context::get('audit.request_id'),
            ], $e->getStatusCode());
        }

        // Handle Laravel validation exceptions
        if ($e instanceof \Illuminate\Validation\ValidationException) {
            return response()->json([
                'success' => false,
                'error' => [
                    'message' => 'Validation failed',
                    'errors' => $e->errors(),
                ],
            ], 422);
        }

        // Handle model not found
        if ($e instanceof \Illuminate\Database\Eloquent\ModelNotFoundException) {
            return response()->json([
                'success' => false,
                'error' => [
                    'message' => 'Resource not found',
                ],
            ], 404);
        }

        // Default Laravel handling
        return parent::render($request, $e);
    }
}
```

---

## Async Operations (Queues)

### Laravel Queues (Not JavaScript async/await)

PHP doesn't have async/await like JavaScript. Instead, Laravel uses queues for background processing.

### Dispatching Jobs

```php
use App\Jobs\SendEmailJob;

// Dispatch job to queue
SendEmailJob::dispatch($user->email, $message);

// Dispatch with delay
SendEmailJob::dispatch($user->email, $message)
    ->delay(now()->addMinutes(5));

// Dispatch to specific queue
SendEmailJob::dispatch($user->email, $message)
    ->onQueue('emails');
```

### Job Class

```php
namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Sentry\Laravel\Facade as Sentry;

class SendEmailJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public $tries = 3;
    public $timeout = 120;

    public function __construct(
        public string $email,
        public string $message
    ) {}

    public function handle(): void
    {
        try {
            // Send email logic
            Mail::to($this->email)->send(new CustomMail($this->message));
        } catch (\Throwable $e) {
            Sentry::captureException($e);
            throw $e; // Will retry based on $tries
        }
    }

    public function failed(\Throwable $exception): void
    {
        // Called when job fails after all retries
        Sentry::captureException($exception);
    }
}
```

### Handling Concurrent Operations

```php
// ❌ JavaScript-style async (doesn't exist in PHP)
// This won't work in PHP!

// ✅ Laravel parallel operations using concurrent()
use Illuminate\Support\Facades\Http;

[$users, $profiles, $settings] = Http::concurrent([
    fn () => Http::get('https://api.example.com/users'),
    fn () => Http::get('https://api.example.com/profiles'),
    fn () => Http::get('https://api.example.com/settings'),
]);

// ✅ Or dispatch multiple jobs
SendEmailJob::dispatch($user1->email, $message);
SendNotificationJob::dispatch($user1->id);
ProcessDataJob::dispatch($data);
```

---

## Error Propagation

### Proper Error Chains

```php
// ✅ Propagate errors up the stack
class UserRepository
{
    public function findAll(): Collection
    {
        try {
            return User::all();
        } catch (\Throwable $e) {
            Sentry::withScope(function ($scope) use ($e): void {
                $scope->setTag('layer', 'repository');
                Sentry::captureException($e);
            });
            throw $e; // Propagate to service
        }
    }
}

class UserService
{
    public function getAllUsers(): Collection
    {
        try {
            return $this->userRepository->findAll();
        } catch (\Throwable $e) {
            Sentry::withScope(function ($scope) use ($e): void {
                $scope->setTag('layer', 'service');
                Sentry::captureException($e);
            });
            throw $e; // Propagate to controller
        }
    }
}

class UserController extends BaseController
{
    public function index(): JsonResponse
    {
        try {
            $users = $this->userService->getAllUsers();
            return $this->handleSuccess($users);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'index'); // Final handler
        }
    }
}
```

---

## Common Pitfalls

### Silent Failures (Bad)

```php
// ❌ NEVER: Silent failure
public function processRequest(Request $request): JsonResponse
{
    try {
        $this->sendEmail($user->email);
    } catch (\Throwable $e) {
        // Silently ignoring error - BAD!
    }

    return response()->json(['success' => true]);
}

// ✅ ALWAYS: Handle or propagate
public function processRequest(Request $request): JsonResponse
{
    try {
        $this->sendEmail($user->email);
        return response()->json(['success' => true]);
    } catch (\Throwable $e) {
        Sentry::captureException($e);
        return response()->json(['error' => 'Failed to send email'], 500);
    }
}

// ✅ OR: Use queue for non-critical operations
public function processRequest(Request $request): JsonResponse
{
    SendEmailJob::dispatch($user->email)
        ->catch(function (\Throwable $e) {
            Sentry::captureException($e);
        });

    return response()->json(['success' => true]);
}
```

### Global Exception Handling

```php
// Laravel automatically handles uncaught exceptions
// Configure in app/Exceptions/Handler.php

// For CLI commands, handle in the command itself
class ProcessData extends Command
{
    public function handle(): int
    {
        try {
            // Command logic
            return Command::SUCCESS;
        } catch (\Throwable $e) {
            Sentry::captureException($e);
            $this->error($e->getMessage());
            return Command::FAILURE;
        }
    }
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [sentry-and-monitoring.md](sentry-and-monitoring.md)
- [complete-examples.md](complete-examples.md)
