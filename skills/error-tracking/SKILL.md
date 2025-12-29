---
name: error-tracking
description: Add Sentry v8 error tracking and performance monitoring to your project services. Use this skill when adding error handling, creating new controllers, instrumenting cron jobs, or tracking database performance. ALL ERRORS MUST BE CAPTURED TO SENTRY - no exceptions.
---

# Laravel Sentry Integration Skill

## Purpose
This skill enforces comprehensive Sentry error tracking and performance monitoring across all Laravel applications following Sentry Laravel SDK patterns.

## When to Use This Skill
- Adding error handling to any code
- Creating new controllers or routes
- Instrumenting Artisan commands and Jobs
- Tracking database performance
- Adding performance spans
- Handling workflow errors

## 🚨 CRITICAL RULE

**ALL ERRORS MUST BE CAPTURED TO SENTRY** - No exceptions. Never use Log::error alone without Sentry.

## Current Status

### Form Service ✅ Complete
- Sentry v8 fully integrated
- All workflow errors tracked
- SystemActionQueueProcessor instrumented
- Test endpoints available

### Email Service 🟡 In Progress
- Phase 1-2 complete (6/22 tasks)
- 189 ErrorLogger.log() calls remaining

## Sentry Integration Patterns

### 1. Controller Error Handling

```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use Sentry\Laravel\Integration;

class MyController extends Controller
{
    public function myMethod(Request $request)
    {
        try {
            // ... your code
            return response()->json(['success' => true]);
        } catch (\Exception $e) {
            // Automatically sends to Sentry with context
            \Sentry\captureException($e);

            return response()->json([
                'error' => 'Internal server error'
            ], 500);
        }
    }
}
```

### 2. Route Error Handling with Middleware

```php
<?php

namespace App\Http\Middleware;

use Closure;
use Illuminate\Http\Request;

class SentryContext
{
    public function handle(Request $request, Closure $next)
    {
        \Sentry\configureScope(function (\Sentry\State\Scope $scope) use ($request) {
            $scope->setTag('route', $request->route()?->getName());
            $scope->setTag('method', $request->method());

            if ($user = $request->user()) {
                $scope->setUser([
                    'id' => $user->id,
                    'email' => $user->email,
                ]);
            }
        });

        return $next($request);
    }
}
```

### 3. Workflow Error Handling

```php
<?php

namespace App\Services;

use Sentry\State\Scope;

class WorkflowSentryHelper
{
    public static function captureWorkflowError(
        \Throwable $error,
        array $context = []
    ): void {
        \Sentry\withScope(function (Scope $scope) use ($error, $context) {
            $scope->setContext('workflow', [
                'workflowCode' => $context['workflowCode'] ?? null,
                'instanceId' => $context['instanceId'] ?? null,
                'stepId' => $context['stepId'] ?? null,
                'operation' => $context['operation'] ?? null,
                'metadata' => $context['metadata'] ?? [],
            ]);

            if (isset($context['userId'])) {
                $scope->setUser(['id' => $context['userId']]);
            }

            $scope->setTag('workflow.code', $context['workflowCode'] ?? 'unknown');
            $scope->setTag('workflow.operation', $context['operation'] ?? 'unknown');

            \Sentry\captureException($error);
        });
    }
}
```

### 4. Artisan Commands (MANDATORY Pattern)

```php
<?php

namespace App\Console\Commands;

use Illuminate\Console\Command;
use Sentry\Tracing\SpanContext;
use Sentry\Tracing\TransactionContext;

class ProcessDataCommand extends Command
{
    protected $signature = 'data:process';
    protected $description = 'Process data with Sentry tracking';

    public function handle()
    {
        $transaction = \Sentry\startTransaction(
            new TransactionContext('cron.data-process', 'cron')
        );

        \Sentry\SentrySdk::getCurrentHub()->setSpan($transaction);

        try {
            $this->info('Starting data processing...');

            // Your command logic here

            $transaction->setStatus(\Sentry\Tracing\SpanStatus::ok());
            $this->info('Completed successfully');

            return Command::SUCCESS;
        } catch (\Exception $e) {
            \Sentry\withScope(function (Scope $scope) use ($e) {
                $scope->setTag('cron.job', 'data:process');
                $scope->setTag('error.type', 'execution_error');
                \Sentry\captureException($e);
            });

            $transaction->setStatus(\Sentry\Tracing\SpanStatus::internalError());
            $this->error('Error: ' . $e->getMessage());

            return Command::FAILURE;
        } finally {
            $transaction->finish();
        }
    }
}
```

### 5. Queued Jobs (MANDATORY Pattern)

```php
<?php

namespace App\Jobs;

use Illuminate\Bus\Queueable;
use Illuminate\Contracts\Queue\ShouldQueue;
use Illuminate\Foundation\Bus\Dispatchable;
use Illuminate\Queue\InteractsWithQueue;
use Illuminate\Queue\SerializesModels;
use Sentry\Tracing\TransactionContext;

class ProcessWorkflow implements ShouldQueue
{
    use Dispatchable, InteractsWithQueue, Queueable, SerializesModels;

    public function handle()
    {
        $transaction = \Sentry\startTransaction(
            new TransactionContext('job.process-workflow', 'queue.job')
        );

        \Sentry\SentrySdk::getCurrentHub()->setSpan($transaction);

        try {
            // Your job logic here

            $transaction->setStatus(\Sentry\Tracing\SpanStatus::ok());
        } catch (\Exception $e) {
            \Sentry\withScope(function (Scope $scope) use ($e) {
                $scope->setTag('job.name', 'ProcessWorkflow');
                $scope->setTag('job.queue', $this->queue);
                \Sentry\captureException($e);
            });

            $transaction->setStatus(\Sentry\Tracing\SpanStatus::internalError());
            throw $e;
        } finally {
            $transaction->finish();
        }
    }

    public function failed(\Throwable $exception)
    {
        \Sentry\captureException($exception);
    }
}
```

### 6. Database Performance Monitoring

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\DB;
use Sentry\Tracing\SpanContext;

class DatabasePerformanceMonitor
{
    public static function withPerformanceTracking(
        string $operation,
        string $model,
        callable $callback
    ) {
        $span = \Sentry\SentrySdk::getCurrentHub()
            ->getSpan()
            ?->startChild(new SpanContext());

        $span?->setOp('db.query.' . $operation);
        $span?->setDescription($model);

        try {
            $result = $callback();
            $span?->setStatus(\Sentry\Tracing\SpanStatus::ok());
            return $result;
        } catch (\Exception $e) {
            $span?->setStatus(\Sentry\Tracing\SpanStatus::internalError());
            throw $e;
        } finally {
            $span?->finish();
        }
    }
}

// Usage example:
$users = DatabasePerformanceMonitor::withPerformanceTracking(
    'select',
    'User',
    fn() => User::where('active', true)->limit(5)->get()
);
```

### 7. Laravel Query Logging with Sentry

```php
<?php

// In AppServiceProvider.php
namespace App\Providers;

use Illuminate\Support\Facades\DB;
use Illuminate\Support\ServiceProvider;

class AppServiceProvider extends ServiceProvider
{
    public function boot()
    {
        // Track slow queries
        DB::listen(function ($query) {
            $threshold = config('sentry.slow_query_threshold', 100);

            if ($query->time > $threshold) {
                \Sentry\withScope(function (Scope $scope) use ($query) {
                    $scope->setContext('database', [
                        'query' => $query->sql,
                        'bindings' => $query->bindings,
                        'time' => $query->time,
                        'connection' => $query->connectionName,
                    ]);

                    $scope->setTag('db.slow_query', 'true');
                    $scope->setTag('db.time', (string) $query->time);

                    \Sentry\captureMessage(
                        'Slow query detected',
                        \Sentry\Severity::warning()
                    );
                });
            }
        });
    }
}
```

### 8. Laravel Telescope Integration

```php
<?php

// config/telescope.php
'watchers' => [
    Watchers\ExceptionWatcher::class => [
        'enabled' => env('TELESCOPE_EXCEPTION_WATCHER', true),
    ],

    Watchers\QueryWatcher::class => [
        'enabled' => env('TELESCOPE_QUERY_WATCHER', true),
        'slow' => 100, // milliseconds
    ],
],
```

### 9. Async Operations with Spans

```php
<?php

use Sentry\Tracing\SpanContext;

$span = \Sentry\SentrySdk::getCurrentHub()
    ->getSpan()
    ?->startChild(new SpanContext());

$span?->setOp('operation.type');
$span?->setDescription('Operation Name');
$span?->setData(['custom.attribute' => 'value']);

try {
    // Your async operation
    $result = someAsyncOperation();
    $span?->setStatus(\Sentry\Tracing\SpanStatus::ok());
    return $result;
} catch (\Exception $e) {
    $span?->setStatus(\Sentry\Tracing\SpanStatus::internalError());
    throw $e;
} finally {
    $span?->finish();
}
```

## Error Levels

Use appropriate severity levels:

- **fatal**: System is unusable (database down, critical service failure)
- **error**: Operation failed, needs immediate attention
- **warning**: Recoverable issues, degraded performance
- **info**: Informational messages, successful operations
- **debug**: Detailed debugging information (dev only)

## Required Context

```php
<?php

use Sentry\State\Scope;

\Sentry\withScope(function (Scope $scope) {
    // ALWAYS include these if available
    $scope->setUser([
        'id' => $userId,
        'email' => $userEmail,
    ]);

    $scope->setTag('service', 'form'); // or 'email', 'users', etc.
    $scope->setTag('environment', config('app.env'));

    // Add operation-specific context
    $scope->setContext('operation', [
        'type' => 'workflow.start',
        'workflowCode' => 'DHS_CLOSEOUT',
        'entityId' => 123,
    ]);

    \Sentry\captureException($error);
});
```

## Service-Specific Integration

### Laravel Configuration

**Location**: `config/sentry.php`

```php
<?php

return [
    'dsn' => env('SENTRY_LARAVEL_DSN'),

    'environment' => env('APP_ENV', 'production'),

    'breadcrumbs' => [
        'logs' => true,
        'cache' => true,
        'livewire' => true,
        'sql_queries' => true,
        'sql_bindings' => true,
        'sql_transaction' => true,
        'queue_info' => true,
        'command_info' => true,
    ],

    'traces_sample_rate' => (float) env('SENTRY_TRACES_SAMPLE_RATE', 0.1),

    'profiles_sample_rate' => (float) env('SENTRY_PROFILES_SAMPLE_RATE', 0.1),

    'send_default_pii' => env('SENTRY_SEND_DEFAULT_PII', false),

    'slow_query_threshold' => 100, // milliseconds
];
```

**Key Helpers**:
- `WorkflowSentryHelper` - Workflow-specific errors
- `DatabasePerformanceMonitor` - DB query tracking
- Laravel's built-in exception handler integration

### Environment Configuration (.env)

```ini
SENTRY_LARAVEL_DSN=your-sentry-dsn
SENTRY_TRACES_SAMPLE_RATE=0.1
SENTRY_PROFILES_SAMPLE_RATE=0.1
```

## Installation

```bash
# Install Sentry Laravel SDK
composer require sentry/sentry-laravel

# Publish configuration
php artisan vendor:publish --provider="Sentry\Laravel\ServiceProvider"

# Add to .env
echo "SENTRY_LARAVEL_DSN=your-dsn-here" >> .env
```

## Testing Sentry Integration

### Test Routes

```php
<?php

// routes/web.php or routes/api.php
use Illuminate\Support\Facades\Route;

Route::get('/sentry/test-error', function () {
    throw new \Exception('Test error for Sentry');
});

Route::get('/sentry/test-workflow-error', function () {
    \App\Services\WorkflowSentryHelper::captureWorkflowError(
        new \Exception('Test workflow error'),
        [
            'workflowCode' => 'TEST_WORKFLOW',
            'instanceId' => 123,
            'operation' => 'test',
        ]
    );

    return response()->json(['message' => 'Workflow error sent to Sentry']);
});

Route::get('/sentry/test-database-performance', function () {
    $users = \App\Services\DatabasePerformanceMonitor::withPerformanceTracking(
        'select',
        'User',
        fn() => \App\Models\User::limit(5)->get()
    );

    return response()->json(['users' => $users]);
});
```

### Test Commands

```bash
# Test basic error capture
curl http://localhost:8000/sentry/test-error

# Test workflow error
curl http://localhost:8000/sentry/test-workflow-error

# Test database performance
curl http://localhost:8000/sentry/test-database-performance

# Test Artisan command
php artisan data:process
```

## Performance Monitoring

### Requirements

1. **All API endpoints** must have transaction tracking (automatic with Sentry Laravel)
2. **Database queries > 100ms** are automatically flagged
3. **N+1 queries** are detected via Telescope
4. **Artisan commands and Jobs** must track execution time

### Transaction Tracking

```php
<?php

// Automatic transaction tracking via middleware
// In app/Http/Kernel.php
protected $middleware = [
    // ...
    \Sentry\Laravel\Http\SetRequestMiddleware::class,
];

// Manual transaction for custom operations
use Sentry\Tracing\TransactionContext;

$transaction = \Sentry\startTransaction(
    new TransactionContext('operation.type', 'Operation Name')
);

\Sentry\SentrySdk::getCurrentHub()->setSpan($transaction);

try {
    // Your operation
} finally {
    $transaction->finish();
}
```

## Common Mistakes to Avoid

❌ **NEVER** use Log::error without Sentry
❌ **NEVER** swallow errors silently
❌ **NEVER** expose sensitive data in error context
❌ **NEVER** use generic error messages without context
❌ **NEVER** skip error handling in async operations
❌ **NEVER** forget to call failed() method in queued jobs

## Implementation Checklist

When adding Sentry to new code:

- [ ] Installed sentry/sentry-laravel package
- [ ] Published and configured config/sentry.php
- [ ] All try/catch blocks capture to Sentry
- [ ] Added meaningful context to errors
- [ ] Used appropriate error level
- [ ] No sensitive data in error messages
- [ ] Added performance tracking for slow operations
- [ ] Tested error handling paths
- [ ] For Jobs: implemented failed() method
- [ ] For Commands: wrapped in transaction

## Key Files

### Laravel Application
- `config/sentry.php` - Sentry configuration
- `app/Services/WorkflowSentryHelper.php` - Workflow errors
- `app/Services/DatabasePerformanceMonitor.php` - DB monitoring
- `app/Http/Middleware/SentryContext.php` - Request context
- `app/Providers/AppServiceProvider.php` - Query logging setup

### Configuration
- `.env` - Environment-specific configuration
- `config/telescope.php` - Laravel Telescope configuration

## Documentation

- Official Sentry Laravel: https://docs.sentry.io/platforms/php/guides/laravel/
- Laravel Telescope: https://laravel.com/docs/telescope
- Performance monitoring: https://docs.sentry.io/platforms/php/guides/laravel/performance/

## Related Skills

- Use **database-verification** before database operations
- Use **workflow-builder** for workflow error context
- Use **database-scripts** for database error handling
