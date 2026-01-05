# Sentry Integration and Monitoring

Complete guide to error tracking and performance monitoring with Sentry in Laravel.

## Table of Contents

- [Core Principles](#core-principles)
- [Sentry Initialization](#sentry-initialization)
- [Error Capture Patterns](#error-capture-patterns)
- [Performance Monitoring](#performance-monitoring)
- [Scheduled Job Monitoring](#scheduled-job-monitoring)
- [Error Context Best Practices](#error-context-best-practices)
- [Common Mistakes](#common-mistakes)

---

## Core Principles

**MANDATORY**: All errors MUST be captured to Sentry. No exceptions.

**ALL ERRORS MUST BE CAPTURED** - Use Sentry Laravel SDK with comprehensive error tracking across all services.

---

## Sentry Initialization

### Laravel Configuration

**Installation:**

```bash
composer require sentry/sentry-laravel
php artisan sentry:publish --dsn=your-dsn-here
```

**Configuration:** `config/sentry.php`

```php
return [
    'dsn' => env('SENTRY_LARAVEL_DSN'),

    'environment' => env('APP_ENV', 'production'),

    // Performance Monitoring
    'traces_sample_rate' => (float) env('SENTRY_TRACES_SAMPLE_RATE', 0.1),
    'profiles_sample_rate' => (float) env('SENTRY_PROFILES_SAMPLE_RATE', 0.1),

    // Error Filtering
    'before_send' => function (\Sentry\Event $event): ?\Sentry\Event {
        // Filter health checks
        if (str_contains($event->getRequest()?->getUrl() ?? '', '/healthcheck')) {
            return null;
        }

        // Scrub sensitive data
        if ($event->getRequest()) {
            $request = $event->getRequest();
            $headers = $request->getHeaders();

            unset($headers['authorization']);
            unset($headers['cookie']);

            $event->setRequest($request->setHeaders($headers));
        }

        // Mask emails for PII
        if ($user = $event->getUser()) {
            if (isset($user['email'])) {
                $user['email'] = preg_replace(
                    '/^(.{2}).*(@.*)$/',
                    '$1***$2',
                    $user['email']
                );
                $event->setUser($user);
            }
        }

        return $event;
    },

    'ignore_exceptions' => [
        Illuminate\Auth\AuthenticationException::class,
        Illuminate\Validation\ValidationException::class,
    ],

    'integrations' => [
        new \Sentry\Integration\RequestIntegration(),
        new \Sentry\Integration\TransactionIntegration(),
        new \Sentry\Integration\FrameContextifierIntegration(),
        new \Sentry\Integration\EnvironmentIntegration(),
    ],
];
```

**Set Service Context in AppServiceProvider:**

```php
namespace App\Providers;

use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function boot(): void
    {
        if (app()->bound('sentry')) {
            \Sentry\configureScope(function (\Sentry\State\Scope $scope): void {
                $scope->setTag('service', 'your-service-name');
                $scope->setTag('version', config('app.version', '1.0.0'));

                $scope->setContext('runtime', [
                    'php_version' => PHP_VERSION,
                    'laravel_version' => app()->version(),
                ]);
            });
        }
    }
}
```

**Critical Points:**
- PII protection built-in (before_send)
- Filter non-critical errors
- Comprehensive integrations
- Database query instrumentation
- Service-specific tagging

---

## Error Capture Patterns

### 1. Base Controller Pattern

```php
namespace App\Http\Controllers;

use Illuminate\Foundation\Auth\Access\AuthorizesRequests;
use Illuminate\Foundation\Validation\ValidatesRequests;
use Illuminate\Http\JsonResponse;
use Illuminate\Routing\Controller;

abstract class BaseController extends Controller
{
    use AuthorizesRequests, ValidatesRequests;

    protected function handleError(
        \Throwable $error,
        string $context,
        int $statusCode = 500
    ): JsonResponse {
        \Sentry\withScope(function (\Sentry\State\Scope $scope) use ($error, $context): void {
            $scope->setTag('controller', static::class);
            $scope->setTag('operation', $context);

            if ($user = auth()->user()) {
                $scope->setUser([
                    'id' => $user->id,
                    'email' => $user->email,
                ]);
            }

            \Sentry\captureException($error);
        });

        return response()->json([
            'success' => false,
            'error' => [
                'message' => $error->getMessage(),
            ],
        ], $statusCode);
    }

    protected function handleSuccess(
        mixed $data,
        string $message = 'Success',
        int $statusCode = 200
    ): JsonResponse {
        return response()->json([
            'success' => true,
            'message' => $message,
            'data' => $data,
        ], $statusCode);
    }
}
```

### 2. Service Layer Error Handling

```php
namespace App\Services;

use Sentry\Laravel\Facade as Sentry;

class PostService
{
    public function createPost(array $data): Post
    {
        try {
            return $this->postRepository->create($data);
        } catch (\Throwable $e) {
            Sentry::withScope(function ($scope) use ($e, $data): void {
                $scope->setTag('service', 'PostService');
                $scope->setTag('operation', 'createPost');

                $scope->setContext('post_data', [
                    'title' => $data['title'] ?? null,
                    'author_id' => $data['author_id'] ?? null,
                ]);

                Sentry::captureException($e);
            });

            throw $e;
        }
    }
}
```

### 3. Exception Handler Integration

```php
namespace App\Exceptions;

use Illuminate\Foundation\Exceptions\Handler as ExceptionHandler;
use Throwable;

class Handler extends ExceptionHandler
{
    public function register(): void
    {
        $this->reportable(function (Throwable $e) {
            if (app()->bound('sentry')) {
                \Sentry\Laravel\Integration::captureUnhandledException($e);
            }
        });
    }
}
```

---

## Performance Monitoring

### Database Query Tracking

**Automatic with Sentry Laravel Integration:**

Laravel's Sentry SDK automatically tracks database queries. No manual instrumentation needed.

**Manual Tracking for Specific Operations:**

```php
use Sentry\Laravel\Facade as Sentry;

$result = Sentry::traceFunction(
    'database.query.users',
    function () {
        return User::with('profile')->take(5)->get();
    }
);
```

### Controller Endpoint Spans

```php
use Sentry\Laravel\Facade as Sentry;

public function store(Request $request): JsonResponse
{
    return Sentry::traceFunction(
        'operation.execute',
        function () use ($request) {
            $result = $this->service->performOperation($request->validated());

            return response()->json($result);
        }
    );
}
```

---

## Scheduled Job Monitoring

### Mandatory Pattern

**Artisan Command:**

```php
namespace App\Console\Commands;

use Illuminate\Console\Command;
use Sentry\Laravel\Facade as Sentry;

class ProcessData extends Command
{
    protected $signature = 'data:process';
    protected $description = 'Process data job';

    public function handle(): int
    {
        return Sentry::traceFunction(
            'cron.process-data',
            function () {
                try {
                    Sentry::configureScope(function ($scope): void {
                        $scope->setTag('cron.job', 'process-data');
                        $scope->setTag('cron.startTime', now()->toISOString());
                    });

                    // Job logic here
                    $this->info('Processing data...');

                    return Command::SUCCESS;
                } catch (\Throwable $e) {
                    Sentry::withScope(function ($scope) use ($e): void {
                        $scope->setTag('cron.job', 'process-data');
                        $scope->setTag('error.type', 'execution_error');

                        Sentry::captureException($e);
                    });

                    $this->error('Error: ' . $e->getMessage());

                    return Command::FAILURE;
                }
            }
        );
    }
}
```

**Queued Jobs:**

```php
namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Sentry\Laravel\Facade as Sentry;

class ProcessDataJob implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable;

    public function handle(): void
    {
        Sentry::traceFunction('job.process-data', function () {
            try {
                // Job logic here
            } catch (\Throwable $e) {
                Sentry::captureException($e);
                throw $e;
            }
        });
    }
}
```

---

## Error Context Best Practices

### Rich Context Example

```php
use Sentry\Laravel\Facade as Sentry;

Sentry::withScope(function ($scope) use ($user, $request, $workflowId, $stepId): void {
    // User context
    $scope->setUser([
        'id' => $user->id,
        'email' => $user->email,
        'username' => $user->name,
    ]);

    // Tags for filtering
    $scope->setTag('service', 'form');
    $scope->setTag('endpoint', $request->path());
    $scope->setTag('method', $request->method());

    // Structured context
    $scope->setContext('operation', [
        'type' => 'workflow.complete',
        'workflow_id' => $workflowId,
        'step_id' => $stepId,
    ]);

    // Breadcrumbs for timeline
    $scope->addBreadcrumb([
        'category' => 'workflow',
        'message' => 'Starting step completion',
        'level' => 'info',
        'data' => ['step_id' => $stepId],
    ]);

    Sentry::captureException($error);
});
```

---

## Common Mistakes

```php
// ❌ Swallowing errors
try {
    $this->riskyOperation();
} catch (\Throwable $e) {
    // Silent failure - NEVER DO THIS
}

// ❌ Generic error messages
throw new \Exception('Error occurred');

// ❌ Exposing sensitive data
Sentry::withScope(function ($scope) use ($user) {
    $scope->setContext('user', [
        'password' => $user->password, // NEVER
    ]);
});

// ❌ Not re-throwing in services
public function serviceMethod()
{
    try {
        return $this->repository->getData();
    } catch (\Throwable $e) {
        Sentry::captureException($e);
        // Should re-throw to let controller handle response
    }
}

// ✅ Proper error handling
public function serviceMethod()
{
    try {
        return $this->repository->getData();
    } catch (\Throwable $e) {
        Sentry::captureException($e);
        throw $e; // Re-throw for proper error propagation
    }
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [routing-and-controllers.md](routing-and-controllers.md)
- [async-and-errors.md](async-and-errors.md)
