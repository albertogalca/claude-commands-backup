---
description: Map edited routes & launch tests
argument-hint: "[/extra/path …]"
allowed-tools: Bash(cat:*), Bash(awk:*), Bash(grep:*), Bash(sort:*), Bash(xargs:*), Bash(sed:*), Bash(php:*)
model: sonnet
---

## Context

Changed route files this session (auto-generated):

!cat "$CLAUDE_PROJECT_DIR/.claude/tsc-cache"/\*/edited-files.log \
 | awk -F: '{print $2}' \
 | grep 'routes/' \
 | sort -u

User-specified additional routes: `$ARGUMENTS`

## Your task

Follow the numbered steps **exactly**:

1. Combine the auto list with `$ARGUMENTS`, dedupe, and identify which route files were modified:
   - `routes/web.php` - Web routes
   - `routes/api.php` - API routes
   - `routes/console.php` - Artisan command routes
   - `routes/channels.php` - Broadcasting routes

2. Use `php artisan route:list --json` to get all registered routes and filter to only modified ones:

```bash
php artisan route:list --json | jq -r '.[] | select(.uri | contains("your-route-pattern"))'
```

3. For each modified route, extract:
   - HTTP method (GET, POST, PUT, DELETE, etc.)
   - URI pattern (e.g., `/api/users/{id}`)
   - Controller@method or closure
   - Middleware applied
   - Route name (if defined)

4. For each route, create a JSON record with:
   - `path`: The route URI
   - `method`: HTTP method
   - `controller`: Controller class and method
   - `middleware`: Array of middleware
   - `requestShape`: Expected request structure (from FormRequest or controller)
   - `responseShape`: Expected response structure
   - `validPayload`: Example valid request
   - `invalidPayload`: Example invalid request (for validation testing)

5. **Now call the `Task` tool** using:

```json
{
    "tool": "Task",
    "parameters": {
        "description": "route smoke tests",
        "prompt": "Run Laravel feature tests for the routes listed above. Use php artisan test to execute tests for these routes."
    }
}
```

## Laravel Route Testing Pattern

### Example Route Discovery

```bash
# List all routes in JSON format
php artisan route:list --json

# Filter routes by URI pattern
php artisan route:list --json | jq '.[] | select(.uri | contains("api/users"))'

# Filter routes by controller
php artisan route:list --json | jq '.[] | select(.action | contains("UserController"))'

# Get routes by method
php artisan route:list --json | jq '.[] | select(.method | contains("POST"))'

# Get routes by middleware
php artisan route:list --json | jq '.[] | select(.middleware | contains("auth"))'
```

### Example Feature Test Structure

```php
<?php

namespace Tests\Feature;

use Tests\TestCase;
use App\Models\User;
use Illuminate\Foundation\Testing\RefreshDatabase;

class UserRoutesTest extends TestCase
{
    use RefreshDatabase;

    /** @test */
    public function it_can_get_user_list()
    {
        $user = User::factory()->create();

        $response = $this->actingAs($user)
            ->getJson('/api/users');

        $response->assertStatus(200)
            ->assertJsonStructure([
                'data' => [
                    '*' => ['id', 'name', 'email', 'created_at']
                ]
            ]);
    }

    /** @test */
    public function it_can_create_user_with_valid_data()
    {
        $admin = User::factory()->admin()->create();

        $payload = [
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'password' => 'password123',
        ];

        $response = $this->actingAs($admin)
            ->postJson('/api/users', $payload);

        $response->assertStatus(201)
            ->assertJsonStructure([
                'data' => ['id', 'name', 'email']
            ]);

        $this->assertDatabaseHas('users', [
            'email' => 'john@example.com'
        ]);
    }

    /** @test */
    public function it_fails_to_create_user_with_invalid_data()
    {
        $admin = User::factory()->admin()->create();

        $invalidPayload = [
            'name' => '',
            'email' => 'not-an-email',
            'password' => '123', // too short
        ];

        $response = $this->actingAs($admin)
            ->postJson('/api/users', $invalidPayload);

        $response->assertStatus(422)
            ->assertJsonValidationErrors(['name', 'email', 'password']);
    }

    /** @test */
    public function it_requires_authentication()
    {
        $response = $this->getJson('/api/users');

        $response->assertStatus(401);
    }
}
```

### Example JSON Record Format

```json
{
  "routes": [
    {
      "path": "/api/users",
      "method": "GET",
      "controller": "App\\Http\\Controllers\\UserController@index",
      "middleware": ["api", "auth:sanctum"],
      "routeName": "users.index",
      "requestShape": null,
      "responseShape": {
        "data": [
          {
            "id": "integer",
            "name": "string",
            "email": "string",
            "created_at": "datetime"
          }
        ]
      },
      "validPayload": null,
      "invalidPayload": null
    },
    {
      "path": "/api/users",
      "method": "POST",
      "controller": "App\\Http\\Controllers\\UserController@store",
      "middleware": ["api", "auth:sanctum", "can:create,User"],
      "routeName": "users.store",
      "requestShape": {
        "name": "required|string|max:255",
        "email": "required|email|unique:users",
        "password": "required|min:8"
      },
      "responseShape": {
        "data": {
          "id": "integer",
          "name": "string",
          "email": "string",
          "created_at": "datetime"
        }
      },
      "validPayload": {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "password123"
      },
      "invalidPayload": {
        "name": "",
        "email": "not-an-email",
        "password": "123"
      }
    }
  ]
}
```

## Testing Commands

```bash
# Run all tests
php artisan test

# Run specific test file
php artisan test tests/Feature/UserRoutesTest.php

# Run with coverage
php artisan test --coverage

# Run tests for specific route pattern
php artisan test --filter=UserRoutes

# Run tests in parallel
php artisan test --parallel
```

## Additional Laravel Testing Tools

### Pest PHP Alternative

```php
<?php

use App\Models\User;

test('users can be listed', function () {
    $user = User::factory()->create();

    $this->actingAs($user)
        ->getJson('/api/users')
        ->assertStatus(200);
});

test('users can be created with valid data', function () {
    $admin = User::factory()->admin()->create();

    $this->actingAs($admin)
        ->postJson('/api/users', [
            'name' => 'John Doe',
            'email' => 'john@example.com',
            'password' => 'password123',
        ])
        ->assertStatus(201);
});
```

### Route Testing Helpers

```bash
# Test route exists
php artisan route:list | grep "api/users"

# Verify middleware on route
php artisan route:list --path=api/users --json | jq '.[].middleware'

# Check route parameters
php artisan route:list --path=api/users/{id} --json | jq '.[].parameters'
```
