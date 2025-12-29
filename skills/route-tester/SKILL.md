---
name: route-tester
description: Test routes in your Laravel application using authentication. Use this skill when testing API endpoints, validating route functionality, or debugging authentication issues. Includes patterns for testing with Sanctum, session auth, and Pest/PHPUnit.
---

# Laravel Route Tester Skill

## Purpose
This skill provides patterns for testing authenticated routes in Laravel applications.

## When to Use This Skill
- Testing new API endpoints
- Validating route functionality after changes
- Debugging authentication issues
- Testing POST/PUT/DELETE operations
- Verifying request/response data

## Laravel Authentication Overview

Laravel supports multiple authentication methods:
- **Session-based** - Traditional web authentication (default for web routes)
- **Laravel Sanctum** - SPA and API token authentication
- **Laravel Passport** - OAuth2 authentication (for complex API requirements)

## Testing Methods

### Method 1: Feature Tests with Pest/PHPUnit (RECOMMENDED)

Laravel's built-in testing framework is the best way to test routes.

**Location**: `tests/Feature/`

#### Basic GET Request Test

```php
<?php

use App\Models\User;

test('user can view dashboard', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->get('/dashboard');

    $response->assertOk();
    $response->assertInertia(fn ($page) =>
        $page->component('Dashboard/Index')
    );
});
```

#### POST Request Test with Validation

```php
test('user can create post', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->post('/posts', [
            'title' => 'Test Post',
            'content' => 'Test content',
        ]);

    $response->assertRedirect('/posts');
    $this->assertDatabaseHas('posts', [
        'title' => 'Test Post',
        'user_id' => $user->id,
    ]);
});
```

#### API Request Test with Sanctum

```php
use Laravel\Sanctum\Sanctum;

test('authenticated user can access API endpoint', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user);

    $response = $this->getJson('/api/user');

    $response->assertOk()
        ->assertJson([
            'id' => $user->id,
            'email' => $user->email,
        ]);
});
```

### Method 2: Manual Testing with artisan tinker

```bash
# Start tinker
php artisan tinker

# Create a test user
$user = User::factory()->create(['email' => 'test@example.com']);

# Generate Sanctum token
$token = $user->createToken('test-token')->plainTextToken;

# Exit tinker and use the token
exit

# Test with curl
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/endpoint
```

### Method 3: Manual Testing with API Client

**Using Postman/Insomnia:**

1. **Session Auth (web routes)**:
   - Make login POST request: `POST /login`
   - Body: `{email, password}`
   - Cookie will be set automatically
   - Subsequent requests include cookie

2. **Sanctum Token Auth (API routes)**:
   - Make login/token request: `POST /api/login`
   - Copy token from response
   - Add header: `Authorization: Bearer {token}`

**Using curl:**

```bash
# Session auth - Login and save cookie
curl -c cookies.txt -X POST http://localhost:8000/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password"}'

# Use saved cookie for subsequent requests
curl -b cookies.txt http://localhost:8000/dashboard

# Sanctum token auth
TOKEN="your-token-here"
curl -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/json" \
     http://localhost:8000/api/user
```

## Common Testing Patterns

### Test with Form Request Validation

```php
test('post creation validates required fields', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->post('/posts', [
            'title' => '', // Invalid: empty title
        ]);

    $response->assertSessionHasErrors(['title', 'content']);
});
```

### Test Inertia Response

```php
use Inertia\Testing\AssertableInertia as Assert;

test('dashboard shows correct data', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->get('/dashboard');

    $response->assertInertia(fn (Assert $page) => $page
        ->component('Dashboard/Index')
        ->has('posts', 10)
        ->has('posts.0', fn (Assert $page) => $page
            ->where('id', 1)
            ->where('title', 'First Post')
            ->etc()
        )
    );
});
```

### Test API Resource Response

```php
test('API returns correct user data', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->getJson('/api/user');

    $response->assertOk()
        ->assertJsonStructure([
            'data' => [
                'id',
                'name',
                'email',
                'created_at',
            ],
        ])
        ->assertJsonMissing(['password']); // Ensure password not exposed
});
```

### Test Authorization (Gates/Policies)

```php
test('user cannot delete others posts', function () {
    $user = User::factory()->create();
    $otherUser = User::factory()->create();
    $post = Post::factory()->create(['user_id' => $otherUser->id]);

    $response = $this->actingAs($user)
        ->delete("/posts/{$post->id}");

    $response->assertForbidden();
    $this->assertDatabaseHas('posts', ['id' => $post->id]);
});
```

### Test File Upload

```php
use Illuminate\Http\UploadedFile;
use Illuminate\Support\Facades\Storage;

test('user can upload file', function () {
    Storage::fake('public');
    $user = User::factory()->create();

    $file = UploadedFile::fake()->image('test.jpg');

    $response = $this->actingAs($user)
        ->post('/upload', [
            'file' => $file,
        ]);

    $response->assertOk();
    Storage::disk('public')->assertExists('uploads/' . $file->hashName());
});
```

### Test with Database Transactions

```php
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

test('user registration creates user', function () {
    $response = $this->post('/register', [
        'name' => 'Test User',
        'email' => 'test@example.com',
        'password' => 'password',
        'password_confirmation' => 'password',
    ]);

    $response->assertRedirect('/dashboard');
    $this->assertDatabaseHas('users', [
        'email' => 'test@example.com',
    ]);
    $this->assertAuthenticated();
});
```

## Laravel Route Testing Best Practices

### 1. Use Factories for Test Data

```php
// database/factories/UserFactory.php
class UserFactory extends Factory
{
    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'password' => bcrypt('password'),
        ];
    }

    public function admin(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_admin' => true,
        ]);
    }
}

// Usage
$admin = User::factory()->admin()->create();
```

### 2. Test Middleware Application

```php
test('admin middleware protects route', function () {
    $user = User::factory()->create(); // Regular user

    $response = $this->actingAs($user)
        ->get('/admin/dashboard');

    $response->assertForbidden();
});

test('admin can access admin dashboard', function () {
    $admin = User::factory()->admin()->create();

    $response = $this->actingAs($admin)
        ->get('/admin/dashboard');

    $response->assertOk();
});
```

### 3. Test JSON API Endpoints

```php
test('API validates request data', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->postJson('/api/posts', [
            'title' => '', // Invalid
        ]);

    $response->assertStatus(422)
        ->assertJsonValidationErrors(['title']);
});
```

### 4. Test Route Model Binding

```php
test('route returns 404 for non-existent resource', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->get('/posts/999999');

    $response->assertNotFound();
});
```

## Authentication Testing Patterns

### Session-Based (Web Routes)

```php
test('guest cannot access protected route', function () {
    $response = $this->get('/dashboard');
    $response->assertRedirect('/login');
});

test('authenticated user can access dashboard', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->get('/dashboard');

    $response->assertOk();
});
```

### Sanctum Token (API Routes)

```php
use Laravel\Sanctum\Sanctum;

test('unauthenticated request returns 401', function () {
    $response = $this->getJson('/api/user');
    $response->assertUnauthorized();
});

test('authenticated API request succeeds', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user, ['*']);

    $response = $this->getJson('/api/user');
    $response->assertOk();
});

test('token with limited scope cannot access route', function () {
    $user = User::factory()->create();
    Sanctum::actingAs($user, ['view-posts']); // Limited scope

    $response = $this->deleteJson('/api/posts/1');
    $response->assertForbidden();
});
```

## Testing Checklist

Before testing a route:

- [ ] Identify route type (web/api)
- [ ] Determine authentication method (session/sanctum)
- [ ] Check middleware requirements
- [ ] Prepare test data using factories
- [ ] Write test for authenticated access
- [ ] Write test for unauthenticated access
- [ ] Test validation rules
- [ ] Test authorization (gates/policies)
- [ ] Verify database changes
- [ ] Test different user roles/permissions

## Verifying Database Changes

```php
test('route creates database record', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/posts', [
            'title' => 'Test Post',
            'content' => 'Test content',
        ]);

    $this->assertDatabaseHas('posts', [
        'title' => 'Test Post',
        'user_id' => $user->id,
    ]);
});

test('route deletes database record', function () {
    $user = User::factory()->create();
    $post = Post::factory()->create(['user_id' => $user->id]);

    $this->actingAs($user)
        ->delete("/posts/{$post->id}");

    $this->assertDatabaseMissing('posts', [
        'id' => $post->id,
    ]);
    // Or assertSoftDeleted if using soft deletes
    $this->assertSoftDeleted('posts', [
        'id' => $post->id,
    ]);
});
```

## Running Tests

```bash
# Run all tests
php artisan test

# Run specific test file
php artisan test tests/Feature/PostTest.php

# Run tests in parallel (faster)
php artisan test --parallel

# Run with coverage
php artisan test --coverage

# Run specific test
php artisan test --filter test_user_can_create_post

# Run tests for specific group
php artisan test --group=api
```

## Debugging Failed Tests

### 401 Unauthorized

**Possible causes**:
1. Missing `actingAs()` call
2. Token expired (Sanctum)
3. Session not started
4. Middleware not applied correctly

**Solutions**:
```php
// Ensure actingAs is called
$this->actingAs($user)->get('/protected');

// For API, use Sanctum
Sanctum::actingAs($user);
$this->getJson('/api/protected');
```

### 403 Forbidden

**Possible causes**:
1. User lacks required permissions
2. Policy/gate denies access
3. CSRF token mismatch

**Solutions**:
```php
// Check policies
test('authorized user can access route', function () {
    $user = User::factory()->admin()->create();
    $this->actingAs($user)->get('/admin');
});

// Disable CSRF for testing (already disabled in TestCase)
```

### 404 Not Found

**Possible causes**:
1. Route not defined
2. Incorrect route path
3. Route model binding failed

**Solutions**:
```bash
# Check registered routes
php artisan route:list

# Check specific route
php artisan route:list --name=posts.store
```

### 422 Validation Error

**Expected behavior** - test it:
```php
test('validation fails for invalid data', function () {
    $user = User::factory()->create();

    $response = $this->actingAs($user)
        ->post('/posts', [
            'title' => '', // Invalid
        ]);

    $response->assertSessionHasErrors(['title']);
});
```

## Advanced Testing Patterns

### Test Events

```php
use Illuminate\Support\Facades\Event;

test('post creation dispatches event', function () {
    Event::fake();
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/posts', [
            'title' => 'Test',
            'content' => 'Content',
        ]);

    Event::assertDispatched(PostCreated::class);
});
```

### Test Queued Jobs

```php
use Illuminate\Support\Facades\Queue;

test('route dispatches job', function () {
    Queue::fake();
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/posts', ['title' => 'Test', 'content' => 'Content']);

    Queue::assertPushed(ProcessPost::class);
});
```

### Test Email Notifications

```php
use Illuminate\Support\Facades\Mail;

test('route sends email', function () {
    Mail::fake();
    $user = User::factory()->create();

    $this->actingAs($user)
        ->post('/posts', ['title' => 'Test', 'content' => 'Content']);

    Mail::assertSent(PostCreatedMail::class);
});
```

## Configuration

### phpunit.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<phpunit>
    <testsuites>
        <testsuite name="Feature">
            <directory>tests/Feature</directory>
        </testsuite>
        <testsuite name="Unit">
            <directory>tests/Unit</directory>
        </testsuite>
    </testsuites>
    <php>
        <env name="APP_ENV" value="testing"/>
        <env name="DB_CONNECTION" value="sqlite"/>
        <env name="DB_DATABASE" value=":memory:"/>
    </php>
</phpunit>
```

### .env.testing

```bash
APP_ENV=testing
DB_CONNECTION=sqlite
DB_DATABASE=:memory:
CACHE_DRIVER=array
QUEUE_CONNECTION=sync
SESSION_DRIVER=array
MAIL_MAILER=array
```

## Related Skills

- Use **backend-dev-guidelines** for controller/route patterns
- Use **error-tracking** for testing error handling
- Use **frontend-dev-guidelines** for Inertia.js testing

## Key Files

- `tests/Feature/` - Feature tests
- `tests/Unit/` - Unit tests
- `tests/TestCase.php` - Base test class
- `phpunit.xml` - PHPUnit configuration
- `.env.testing` - Testing environment variables
