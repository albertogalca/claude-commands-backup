# Configuration Management - Laravel Config Pattern

Complete guide to managing configuration in Laravel applications.

## Table of Contents

- [Laravel Config Overview](#laravel-config-overview)
- [NEVER Use env() Directly](#never-use-env-directly)
- [Configuration Structure](#configuration-structure)
- [Environment-Specific Configs](#environment-specific-configs)
- [Secrets Management](#secrets-management)
- [Migration Guide](#migration-guide)

---

## Laravel Config Overview

### Why Laravel Config?

**Problems with env() in code:**
- ❌ No type safety
- ❌ No caching support
- ❌ Hard to test
- ❌ Scattered throughout code
- ❌ Bypasses config cache
- ❌ Runtime errors for typos

**Benefits of config() helper:**
- ✅ Type-safe with IDE support
- ✅ Single source of truth
- ✅ Validated at startup
- ✅ Easy to test with mocks
- ✅ Clear structure
- ✅ Cacheable for performance

---

## NEVER Use env() Directly

### The Rule

```php
// ❌ NEVER DO THIS (outside config files)
$timeout = (int) env('TIMEOUT_MS', 5000);
$dbHost = env('DB_HOST', 'localhost');

// ✅ ALWAYS DO THIS
$timeout = config('app.timeout');
$dbHost = config('database.connections.mysql.host');
```

### Why This Matters

**Example of problems:**
```php
// Typo in environment variable name
$host = env('DB_HSOT'); // null! No error!

// Type safety
$port = env('PORT'); // string! Need (int)
$timeout = (int) env('TIMEOUT'); // 0 if not set!

// Config caching breaks env()
php artisan config:cache
// After caching, env() always returns null!
```

**With config() helper:**
```php
$port = config('app.port'); // int, guaranteed
$timeout = config('app.timeout'); // int, with fallback
$features = config('app.features'); // array, type-safe
```

---

## Configuration Structure

### Laravel Config Files

**Directory:** `/config/`

```
config/
├── app.php           # Application config
├── database.php      # Database connections
├── cache.php         # Cache stores
├── queue.php         # Queue connections
├── mail.php          # Mail configuration
├── services.php      # Third-party services
├── auth.php          # Authentication
├── logging.php       # Logging channels
└── custom.php        # Custom app config
```

### Custom Configuration File

**File:** `config/custom.php`

```php
<?php

return [
    'tokens' => [
        'jwt_secret' => env('JWT_SECRET'),
        'jwt_ttl' => env('JWT_TTL', 3600),
        'refresh_ttl' => env('REFRESH_TTL', 86400),
    ],

    'external_apis' => [
        'stripe' => [
            'key' => env('STRIPE_KEY'),
            'secret' => env('STRIPE_SECRET'),
            'webhook_secret' => env('STRIPE_WEBHOOK_SECRET'),
        ],
        'sendgrid' => [
            'api_key' => env('SENDGRID_API_KEY'),
        ],
    ],

    'features' => [
        'analytics' => env('FEATURE_ANALYTICS', true),
        'notifications' => env('FEATURE_NOTIFICATIONS', true),
        'maintenance_mode' => env('MAINTENANCE_MODE', false),
    ],

    'limits' => [
        'max_upload_size' => env('MAX_UPLOAD_SIZE', 10240), // KB
        'rate_limit_per_minute' => env('RATE_LIMIT', 60),
        'pagination_default' => env('PAGINATION_DEFAULT', 15),
    ],
];
```

### Usage in Code

```php
// Access configuration
$jwtSecret = config('custom.tokens.jwt_secret');
$stripeKey = config('custom.external_apis.stripe.key');
$uploadLimit = config('custom.limits.max_upload_size');

// Check if feature enabled
if (config('custom.features.analytics')) {
    // Track analytics
}

// Get with default fallback
$timeout = config('custom.timeout', 30);

// Set config at runtime (not persisted)
config(['custom.runtime_value' => 'temp']);
```

---

## Environment-Specific Configs

### .env File Structure

```bash
# Application
APP_NAME="My Application"
APP_ENV=local
APP_KEY=base64:your-app-key-here
APP_DEBUG=true
APP_URL=http://localhost

# Database
DB_CONNECTION=mysql
DB_HOST=127.0.0.1
DB_PORT=3306
DB_DATABASE=myapp_dev
DB_USERNAME=root
DB_PASSWORD=password

# Custom Configuration
JWT_SECRET=your-jwt-secret-here
JWT_TTL=3600
REFRESH_TTL=86400

# External Services
STRIPE_KEY=pk_test_xxx
STRIPE_SECRET=sk_test_xxx
SENDGRID_API_KEY=SG.xxx

# Features
FEATURE_ANALYTICS=true
FEATURE_NOTIFICATIONS=true
MAINTENANCE_MODE=false

# Limits
MAX_UPLOAD_SIZE=10240
RATE_LIMIT=60
PAGINATION_DEFAULT=15
```

### Environment Files

Laravel supports multiple environment files:

```
.env                 # Default (local development)
.env.example         # Template for new developers
.env.testing         # Test environment
.env.production      # Production (never committed)
.env.staging         # Staging environment
```

### Accessing Config in Different Environments

```php
// config/database.php
'connections' => [
    'mysql' => [
        'driver' => 'mysql',
        'host' => env('DB_HOST', '127.0.0.1'),
        'port' => env('DB_PORT', '3306'),
        'database' => env('DB_DATABASE', 'forge'),
        'username' => env('DB_USERNAME', 'forge'),
        'password' => env('DB_PASSWORD', ''),
    ],
];

// Usage in code
$dbHost = config('database.connections.mysql.host');
```

### Config Caching

**Production Best Practice:**

```bash
# Cache configuration for performance
php artisan config:cache

# Clear config cache
php artisan config:clear

# After changing .env, always recache
php artisan config:cache
```

**Important:** After caching, env() returns null! Always use config().

---

## Secrets Management

### DO NOT Commit Secrets

```gitignore
# .gitignore
.env
.env.backup
.env.production
.env.staging
*.pem
*.key
storage/oauth-private.key
storage/oauth-public.key
```

### Production Secrets

**Option 1: Environment Variables (Recommended)**
```php
// Set in server environment
// config/services.php
return [
    'stripe' => [
        'key' => env('STRIPE_KEY'),
        'secret' => env('STRIPE_SECRET'),
    ],
];
```

**Option 2: Laravel Secrets (Encrypted)**
```bash
# Encrypt secrets
php artisan env:encrypt --env=production

# Creates .env.production.encrypted

# Decrypt on server
php artisan env:decrypt --env=production
```

**Option 3: External Secret Management**
```php
// AWS Secrets Manager, HashiCorp Vault, etc.
// Use packages like:
// - aws/aws-sdk-php
// - spatie/laravel-vault
```

### Validate Required Secrets

**Service Provider (app/Providers/AppServiceProvider.php):**
```php
public function boot(): void
{
    if (app()->environment('production')) {
        $requiredSecrets = [
            'APP_KEY',
            'DB_PASSWORD',
            'JWT_SECRET',
            'STRIPE_SECRET',
        ];

        foreach ($requiredSecrets as $secret) {
            if (empty(config(str_replace('_', '.', strtolower($secret))))) {
                throw new \RuntimeException("Missing required secret: {$secret}");
            }
        }
    }
}
```

---

## Migration Guide

### Find All env() Usage Outside Config

```bash
# Find env() calls outside config directory
grep -r "env(" app/ --include="*.php" | grep -v "config/"

# Should return minimal results (ideally none)
```

### Migration Example

**Before (Bad):**
```php
// app/Services/PaymentService.php
class PaymentService
{
    public function charge($amount)
    {
        $stripeSecret = env('STRIPE_SECRET'); // ❌ Bad!
        $timeout = (int) env('PAYMENT_TIMEOUT', 30); // ❌ Bad!

        // ...
    }
}
```

**After (Good):**
```php
// config/services.php
return [
    'stripe' => [
        'secret' => env('STRIPE_SECRET'),
        'timeout' => env('PAYMENT_TIMEOUT', 30),
    ],
];

// app/Services/PaymentService.php
class PaymentService
{
    public function charge($amount)
    {
        $stripeSecret = config('services.stripe.secret'); // ✅ Good!
        $timeout = config('services.stripe.timeout'); // ✅ Good!

        // ...
    }
}
```

### Testing with Config

**Feature Test:**
```php
use Illuminate\Support\Facades\Config;

test('payment processes correctly', function () {
    // Override config for test
    Config::set('services.stripe.secret', 'test_secret_key');

    $service = new PaymentService();
    $result = $service->charge(1000);

    expect($result)->toBeTrue();
});
```

**Mocking Config:**
```php
test('feature flag controls behavior', function () {
    // Test when feature enabled
    Config::set('custom.features.analytics', true);
    $this->assertTrue(app(AnalyticsService::class)->isEnabled());

    // Test when feature disabled
    Config::set('custom.features.analytics', false);
    $this->assertFalse(app(AnalyticsService::class)->isEnabled());
});
```

### Config Validation Pattern

**Create a validation service:**
```php
// app/Services/ConfigValidationService.php
class ConfigValidationService
{
    public static function validate(): void
    {
        $required = [
            'app.key' => 'Application key must be set',
            'custom.tokens.jwt_secret' => 'JWT secret is required',
        ];

        foreach ($required as $key => $message) {
            if (empty(config($key))) {
                throw new \RuntimeException($message);
            }
        }
    }
}

// app/Providers/AppServiceProvider.php
public function boot(): void
{
    if (!app()->runningInConsole() || app()->environment('production')) {
        ConfigValidationService::validate();
    }
}
```

---

## Advanced Patterns

### Dynamic Configuration

```php
// Load config from database
// app/Providers/AppServiceProvider.php
public function boot(): void
{
    if (Schema::hasTable('settings')) {
        $settings = DB::table('settings')->pluck('value', 'key');
        Config::set('dynamic', $settings->toArray());
    }
}

// Usage
$siteName = config('dynamic.site_name');
```

### Per-Tenant Configuration

```php
// Multi-tenant app
class TenantConfigMiddleware
{
    public function handle($request, $next)
    {
        $tenant = $request->tenant();

        Config::set('database.connections.tenant', [
            'database' => "tenant_{$tenant->id}",
            // ...
        ]);

        return $next($request);
    }
}
```

### Type-Safe Config Access

```php
// Create helper class for type safety
class AppConfig
{
    public static function jwtSecret(): string
    {
        return config('custom.tokens.jwt_secret');
    }

    public static function jwtTtl(): int
    {
        return (int) config('custom.tokens.jwt_ttl');
    }

    public static function isFeatureEnabled(string $feature): bool
    {
        return (bool) config("custom.features.{$feature}", false);
    }
}

// Usage
$secret = AppConfig::jwtSecret(); // string, type-safe
$ttl = AppConfig::jwtTtl(); // int, type-safe
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [testing-guide.md](testing-guide.md)
- [services-and-repositories.md](services-and-repositories.md)
