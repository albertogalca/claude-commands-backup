# Testing Guide - Laravel Testing Strategies

Complete guide to testing Laravel applications with Pest and PHPUnit.

## Table of Contents

- [Unit Testing](#unit-testing)
- [Feature Testing](#feature-testing)
- [Mocking Strategies](#mocking-strategies)
- [Test Data Management](#test-data-management)
- [Testing Authenticated Routes](#testing-authenticated-routes)
- [Coverage Targets](#coverage-targets)

---

## Unit Testing

### Test Structure with Pest

**Installation:**

```bash
composer require pestphp/pest --dev --with-all-dependencies
php artisan pest:install
```

**Example Test:**

```php
// tests/Unit/Services/UserServiceTest.php
use App\Services\UserService;
use App\Repositories\UserRepository;
use App\Exceptions\ConflictException;

beforeEach(function () {
    $this->repository = Mockery::mock(UserRepository::class);
    $this->service = new UserService($this->repository);
});

test('it throws error if email exists', function () {
    $this->repository
        ->shouldReceive('findByEmail')
        ->with('test@test.com')
        ->once()
        ->andReturn((object) ['id' => 123]);

    expect(fn () => $this->service->create([
        'email' => 'test@test.com',
        'name' => 'Test User',
    ]))->toThrow(ConflictException::class, 'Email already in use');
});

test('it creates user if email is unique', function () {
    $this->repository
        ->shouldReceive('findByEmail')
        ->with('test@test.com')
        ->once()
        ->andReturn(null);

    $this->repository
        ->shouldReceive('create')
        ->once()
        ->andReturn((object) [
            'id' => 123,
            'email' => 'test@test.com',
            'name' => 'Test User',
        ]);

    $user = $this->service->create([
        'email' => 'test@test.com',
        'name' => 'Test User',
    ]);

    expect($user)->toBeDefined()
        ->and($user->email)->toBe('test@test.com');
});
```

### PHPUnit Style (Alternative)

```php
// tests/Unit/Services/UserServiceTest.php
namespace Tests\Unit\Services;

use App\Services\UserService;
use App\Repositories\UserRepository;
use Tests\TestCase;

class UserServiceTest extends TestCase
{
    private UserService $service;
    private UserRepository $repository;

    protected function setUp(): void
    {
        parent::setUp();

        $this->repository = Mockery::mock(UserRepository::class);
        $this->service = new UserService($this->repository);
    }

    protected function tearDown(): void
    {
        Mockery::close();
        parent::tearDown();
    }

    public function test_it_throws_error_if_email_exists(): void
    {
        $this->repository
            ->shouldReceive('findByEmail')
            ->with('test@test.com')
            ->once()
            ->andReturn((object) ['id' => 123]);

        $this->expectException(ConflictException::class);

        $this->service->create([
            'email' => 'test@test.com',
            'name' => 'Test User',
        ]);
    }
}
```

---

## Feature Testing

### Test with Real Database

**Pest Style:**

```php
// tests/Feature/UserControllerTest.php
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

beforeEach(function () {
    $this->user = User::factory()->create([
        'email' => 'test@test.com',
    ]);
});

test('it can list users', function () {
    $this->actingAs($this->user)
        ->getJson('/api/users')
        ->assertOk()
        ->assertJsonStructure([
            'success',
            'data' => [
                '*' => ['id', 'email', 'name'],
            ],
        ]);
});

test('it can create a user', function () {
    $this->actingAs($this->user)
        ->postJson('/api/users', [
            'email' => 'new@test.com',
            'name' => 'New User',
            'age' => 25,
        ])
        ->assertCreated()
        ->assertJson([
            'success' => true,
            'data' => [
                'email' => 'new@test.com',
            ],
        ]);

    expect(User::where('email', 'new@test.com')->exists())->toBeTrue();
});
```

**PHPUnit Style:**

```php
// tests/Feature/UserControllerTest.php
namespace Tests\Feature;

use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;
use Tests\TestCase;

class UserControllerTest extends TestCase
{
    use RefreshDatabase;

    private User $user;

    protected function setUp(): void
    {
        parent::setUp();

        $this->user = User::factory()->create([
            'email' => 'test@test.com',
        ]);
    }

    public function test_it_can_create_a_user(): void
    {
        $response = $this->actingAs($this->user)
            ->postJson('/api/users', [
                'email' => 'new@test.com',
                'name' => 'New User',
                'age' => 25,
            ]);

        $response->assertCreated()
            ->assertJson([
                'success' => true,
                'data' => [
                    'email' => 'new@test.com',
                ],
            ]);

        $this->assertDatabaseHas('users', [
            'email' => 'new@test.com',
        ]);
    }
}
```

---

## Mocking Strategies

### Mock Eloquent Models

```php
use App\Models\User;
use Mockery;

test('it mocks user model', function () {
    $mockUser = Mockery::mock(User::class);

    $mockUser->shouldReceive('where')
        ->with('email', 'test@test.com')
        ->once()
        ->andReturnSelf();

    $mockUser->shouldReceive('first')
        ->once()
        ->andReturn((object) ['id' => 1, 'email' => 'test@test.com']);
});
```

### Mock Services

```php
use App\Services\UserService;

test('it mocks user service', function () {
    $mockService = Mockery::mock(UserService::class);

    $mockService->shouldReceive('findById')
        ->with(1)
        ->once()
        ->andReturn((object) ['id' => 1, 'email' => 'test@test.com']);

    $this->app->instance(UserService::class, $mockService);
});
```

### Bind Mock in Container

```php
test('it uses mocked service from container', function () {
    $mockService = Mockery::mock(UserService::class);
    $mockService->shouldReceive('getAllUsers')
        ->once()
        ->andReturn(collect([
            (object) ['id' => 1, 'name' => 'User 1'],
            (object) ['id' => 2, 'name' => 'User 2'],
        ]));

    $this->app->instance(UserService::class, $mockService);

    $response = $this->getJson('/api/users');

    $response->assertOk()
        ->assertJsonCount(2, 'data');
});
```

---

## Test Data Management

### Using Factories

**Define Factory:**

```php
// database/factories/UserFactory.php
namespace Database\Factories;

use Illuminate\Database\Eloquent\Factories\Factory;

class UserFactory extends Factory
{
    public function definition(): array
    {
        return [
            'name' => fake()->name(),
            'email' => fake()->unique()->safeEmail(),
            'age' => fake()->numberBetween(18, 80),
            'is_active' => true,
        ];
    }

    public function inactive(): static
    {
        return $this->state(fn (array $attributes) => [
            'is_active' => false,
        ]);
    }
}
```

**Use in Tests:**

```php
test('it uses factories', function () {
    // Create single user
    $user = User::factory()->create();

    // Create multiple users
    $users = User::factory()->count(5)->create();

    // Create with custom attributes
    $admin = User::factory()->create(['role' => 'admin']);

    // Create inactive users
    $inactive = User::factory()->inactive()->create();
});
```

### Setup and Teardown

```php
use Illuminate\Foundation\Testing\RefreshDatabase;

uses(RefreshDatabase::class);

beforeEach(function () {
    // Runs before each test
    $this->user = User::factory()->create();
});

afterEach(function () {
    // Runs after each test (usually not needed with RefreshDatabase)
});
```

---

## Testing Authenticated Routes

### Using actingAs()

```php
use App\Models\User;

test('it requires authentication', function () {
    $this->getJson('/api/users')
        ->assertUnauthorized();
});

test('it allows authenticated users', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->getJson('/api/users')
        ->assertOk();
});
```

### Using Sanctum

```php
use Laravel\Sanctum\Sanctum;
use App\Models\User;

test('it authenticates with sanctum', function () {
    $user = User::factory()->create();

    Sanctum::actingAs($user, ['*']);

    $this->getJson('/api/users')
        ->assertOk();
});
```

### Testing Different User Roles

```php
test('admin can access users', function () {
    $admin = User::factory()->create(['role' => 'admin']);

    $this->actingAs($admin)
        ->getJson('/api/users')
        ->assertOk();
});

test('regular user cannot access users', function () {
    $user = User::factory()->create(['role' => 'user']);

    $this->actingAs($user)
        ->getJson('/api/users')
        ->assertForbidden();
});
```

---

## Coverage Targets

### Recommended Coverage

- **Unit Tests**: 70%+ coverage
- **Feature Tests**: Critical paths covered
- **E2E Tests**: Happy paths covered

### Run Tests

```bash
# Run all tests
php artisan test

# Run with Pest
./vendor/bin/pest

# Run specific test file
php artisan test tests/Feature/UserControllerTest.php

# Run with coverage (requires Xdebug or PCOV)
php artisan test --coverage

# Pest with coverage
./vendor/bin/pest --coverage

# Minimum coverage threshold
./vendor/bin/pest --coverage --min=70
```

### Parallel Testing

```bash
# Run tests in parallel
php artisan test --parallel

# Pest parallel
./vendor/bin/pest --parallel
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [services-and-repositories.md](services-and-repositories.md)
- [complete-examples.md](complete-examples.md)
