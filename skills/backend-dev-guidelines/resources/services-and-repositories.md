# Services and Repositories - Business Logic Layer

Complete guide to organizing business logic with services and data access with repositories in Laravel.

## Table of Contents

- [Service Layer Overview](#service-layer-overview)
- [Dependency Injection Pattern](#dependency-injection-pattern)
- [Singleton Pattern](#singleton-pattern)
- [Repository Pattern](#repository-pattern)
- [Service Design Principles](#service-design-principles)
- [Caching Strategies](#caching-strategies)
- [Testing Services](#testing-services)

---

## Service Layer Overview

### Purpose of Services

**Services contain business logic** - the 'what' and 'why' of your application:

```
Controller asks: "Should I do this?"
Service answers: "Yes/No, here's why, and here's what happens"
Repository executes: "Here's the data you requested"
```

**Services are responsible for:**
- ✅ Business rules enforcement
- ✅ Orchestrating multiple repositories
- ✅ Transaction management
- ✅ Complex calculations
- ✅ External service integration
- ✅ Business validations

**Services should NOT:**
- ❌ Know about HTTP (Request/Response)
- ❌ Direct Eloquent access (use repositories)
- ❌ Handle route-specific logic
- ❌ Format HTTP responses

---

## Dependency Injection Pattern

### Why Dependency Injection?

**Benefits:**
- Easy to test (inject mocks)
- Clear dependencies
- Flexible configuration
- Promotes loose coupling

### Excellent Example: NotificationService

**File:** `app/Services/NotificationService.php`

```php
<?php

namespace App\Services;

use App\Models\UserPreference;
use Illuminate\Support\Facades\Cache;

class NotificationService
{
    private const CACHE_TTL = 300; // 5 minutes

    public function __construct(
        private BatchingService $batchingService,
        private EmailComposer $emailComposer
    ) {}

    /**
     * Create a notification and route it appropriately
     */
    public function createNotification(array $params): array
    {
        $recipientID = $params['recipientID'];
        $type = $params['type'];
        $context = $params['context'] ?? [];
        $channel = $params['channel'] ?? 'both';
        $priority = $params['priority'] ?? NotificationPriority::NORMAL;

        try {
            // Get template and render content
            $template = $this->getNotificationTemplate($type);
            $rendered = $this->renderNotificationContent($template, $context);

            // Create in-app notification record
            $notification = \App\Models\Notification::create([
                'instance_id' => $context['instanceId'] ?? 0,
                'template' => $type,
                'recipient_user_id' => $recipientID,
                'channel' => $channel === 'email' ? 'email' : 'inApp',
                'context_data' => $context,
                'title' => $rendered['title'],
                'message' => $rendered['message'],
                'link' => $rendered['link'] ?? null,
            ]);

            // Route notification based on channel
            if ($channel === 'email' || $channel === 'both') {
                $this->routeNotification([
                    'notificationId' => $notification->id,
                    'userId' => $recipientID,
                    'type' => $type,
                    'priority' => $priority,
                    'title' => $rendered['title'],
                    'message' => $rendered['message'],
                    'link' => $rendered['link'] ?? null,
                    'context' => $context,
                ]);
            }

            return $notification->toArray();
        } catch (\Throwable $e) {
            \Log::error('[NotificationService] createNotification', [
                'type' => $type,
                'recipientID' => $recipientID,
                'error' => $e->getMessage(),
            ]);
            throw $e;
        }
    }

    /**
     * Route notification based on user preferences
     */
    private function routeNotification(array $params): void
    {
        // Get user preferences with caching
        $preferences = $this->getUserPreferences($params['userId']);

        // Check if we should batch or send immediately
        if ($this->shouldBatchEmail($preferences, $params['type'], $params['priority'])) {
            $this->batchingService->queueNotificationForBatch([
                'notificationId' => $params['notificationId'],
                'userId' => $params['userId'],
                'userPreference' => $preferences,
                'priority' => $params['priority'],
            ]);
        } else {
            // Send immediately via EmailComposer
            $this->sendImmediateEmail([
                'userId' => $params['userId'],
                'title' => $params['title'],
                'message' => $params['message'],
                'link' => $params['link'],
                'context' => $params['context'],
                'type' => $params['type'],
            ]);
        }
    }

    /**
     * Determine if email should be batched
     */
    public function shouldBatchEmail(
        UserPreference $preferences,
        string $notificationType,
        string $priority
    ): bool {
        // HIGH priority always immediate
        if ($priority === NotificationPriority::HIGH) {
            return false;
        }

        // Check batch mode
        $batchMode = $preferences->email_batch_mode ?? BatchMode::IMMEDIATE;
        return $batchMode !== BatchMode::IMMEDIATE;
    }

    /**
     * Get user preferences with caching
     */
    public function getUserPreferences(string $userId): UserPreference
    {
        return Cache::remember(
            "user_preferences:{$userId}",
            self::CACHE_TTL,
            fn() => UserPreference::where('user_id', $userId)->first()
                ?? $this->getDefaultPreferences()
        );
    }

    private function getDefaultPreferences(): UserPreference
    {
        return new UserPreference([
            'email_batch_mode' => BatchMode::IMMEDIATE,
        ]);
    }
}
```

**Usage in Controller:**

```php
<?php

namespace App\Http\Controllers;

use App\Services\NotificationService;
use Illuminate\Http\JsonResponse;
use Illuminate\Http\Request;

class NotificationController extends Controller
{
    public function __construct(
        private NotificationService $notificationService
    ) {}

    public function store(Request $request): JsonResponse
    {
        try {
            $notification = $this->notificationService->createNotification([
                'recipientID' => $request->input('recipientID'),
                'type' => 'AFRLWorkflowNotification',
                'context' => ['workflowName' => 'AFRL Monthly Report'],
            ]);

            return $this->handleSuccess($notification, 'Notification created', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }
}
```

**Key Takeaways:**
- Dependencies injected via constructor
- Laravel's service container handles injection automatically
- Easy to test (inject mocks)
- Encapsulated caching logic
- Business rules isolated from HTTP

---

## Singleton Pattern

### When to Use Singletons

**Use for:**
- Services with expensive initialization
- Services with shared state (caching)
- Services accessed from many places
- Permission services
- Configuration services

### Example: PermissionService (Singleton)

**File:** `app/Services/PermissionService.php`

```php
<?php

namespace App\Services;

use App\Models\Post;
use Illuminate\Support\Facades\Cache;

class PermissionService
{
    private const CACHE_TTL = 300; // 5 minutes

    /**
     * Check if user can complete a workflow step
     */
    public function canCompleteStep(string $userId, int $stepInstanceId): bool
    {
        $cacheKey = "permission:{$userId}:{$stepInstanceId}";

        return Cache::remember($cacheKey, self::CACHE_TTL, function () use ($userId, $stepInstanceId) {
            try {
                $post = Post::with(['author', 'comments.user'])
                    ->find($stepInstanceId);

                if (!$post) {
                    return false;
                }

                // Check if user has permission
                $canEdit = $post->author_id === $userId
                    || $this->isUserAdmin($userId);

                return $canEdit;
            } catch (\Throwable $e) {
                \Log::error('[PermissionService] Error checking step permission', [
                    'userId' => $userId,
                    'stepInstanceId' => $stepInstanceId,
                    'error' => $e->getMessage(),
                ]);
                return false;
            }
        });
    }

    /**
     * Check if user is admin
     */
    private function isUserAdmin(string $userId): bool
    {
        return Cache::remember(
            "user_admin:{$userId}",
            self::CACHE_TTL,
            fn() => \App\Models\User::find($userId)?->hasRole('admin') ?? false
        );
    }

    /**
     * Clear cache for user
     */
    public function clearUserCache(string $userId): void
    {
        $pattern = "permission:{$userId}:*";
        // Note: Pattern deletion requires Redis
        Cache::tags(["user:{$userId}"])->flush();
    }

    /**
     * Clear all cache
     */
    public function clearCache(): void
    {
        Cache::flush();
    }
}
```

**Usage:**

```php
<?php

namespace App\Services;

use App\Exceptions\ForbiddenException;

class WorkflowService
{
    public function __construct(
        private PermissionService $permissionService
    ) {}

    public function completeStep(array $data, string $userId): array
    {
        $canComplete = $this->permissionService->canCompleteStep(
            $userId,
            $data['stepInstanceId']
        );

        if (!$canComplete) {
            throw new ForbiddenException('You do not have permission to complete this step');
        }

        // Continue with workflow logic...
    }
}
```

---

## Repository Pattern

### Purpose of Repositories

**Repositories abstract data access** - the 'how' of data operations:

```
Service: "Get me all active users sorted by name"
Repository: "Here's the Eloquent query that does that"
```

**Repositories are responsible for:**
- ✅ All Eloquent operations
- ✅ Query construction
- ✅ Query optimization (select, with)
- ✅ Database error handling
- ✅ Caching database results

**Repositories should NOT:**
- ❌ Contain business logic
- ❌ Know about HTTP
- ❌ Make decisions (that's service layer)

### Repository Template

```php
<?php

namespace App\Repositories;

use App\Models\User;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\Cache;

class UserRepository
{
    /**
     * Find user by ID with optimized query
     */
    public function findById(string $userId): ?User
    {
        try {
            return User::select([
                    'id',
                    'email',
                    'name',
                    'is_active',
                    'created_at',
                    'updated_at',
                ])
                ->with('roles')
                ->find($userId);
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error finding user by ID', [
                'userId' => $userId,
                'error' => $e->getMessage(),
            ]);
            throw new \Exception("Failed to find user: {$userId}");
        }
    }

    /**
     * Find all active users
     */
    public function findActive(array $orderBy = ['name' => 'asc']): Collection
    {
        try {
            return User::where('is_active', true)
                ->select(['id', 'email', 'name'])
                ->with('roles')
                ->orderBy(array_key_first($orderBy), array_values($orderBy)[0])
                ->get();
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error finding active users', [
                'error' => $e->getMessage(),
            ]);
            throw new \Exception('Failed to find active users');
        }
    }

    /**
     * Find user by email
     */
    public function findByEmail(string $email): ?User
    {
        try {
            return User::where('email', $email)->first();
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error finding user by email', [
                'email' => $email,
                'error' => $e->getMessage(),
            ]);
            throw new \Exception("Failed to find user with email: {$email}");
        }
    }

    /**
     * Create new user
     */
    public function create(array $data): User
    {
        try {
            return User::create($data);
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error creating user', [
                'error' => $e->getMessage(),
            ]);
            throw new \Exception('Failed to create user');
        }
    }

    /**
     * Update user
     */
    public function update(string $userId, array $data): User
    {
        try {
            $user = User::findOrFail($userId);
            $user->update($data);
            return $user->fresh();
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error updating user', [
                'userId' => $userId,
                'error' => $e->getMessage(),
            ]);
            throw new \Exception("Failed to update user: {$userId}");
        }
    }

    /**
     * Delete user (soft delete by setting is_active = false)
     */
    public function delete(string $userId): User
    {
        try {
            $user = User::findOrFail($userId);
            $user->update(['is_active' => false]);
            return $user;
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error deleting user', [
                'userId' => $userId,
                'error' => $e->getMessage(),
            ]);
            throw new \Exception("Failed to delete user: {$userId}");
        }
    }

    /**
     * Check if email exists
     */
    public function emailExists(string $email): bool
    {
        try {
            return User::where('email', $email)->exists();
        } catch (\Throwable $e) {
            \Log::error('[UserRepository] Error checking email exists', [
                'error' => $e->getMessage(),
            ]);
            throw new \Exception('Failed to check if email exists');
        }
    }
}
```

**Using Repository in Service:**

```php
<?php

namespace App\Services;

use App\Exceptions\ConflictException;
use App\Exceptions\NotFoundException;
use App\Exceptions\ValidationException;
use App\Models\User;
use App\Repositories\UserRepository;

class UserService
{
    public function __construct(
        private UserRepository $userRepository
    ) {}

    /**
     * Create new user with business rules
     */
    public function create(array $data): User
    {
        // Business rule: Check if email already exists
        if ($this->userRepository->emailExists($data['email'])) {
            throw new ConflictException('Email already exists');
        }

        // Business rule: Validate roles
        $validRoles = ['admin', 'operations', 'user'];
        $invalidRoles = array_diff($data['roles'] ?? [], $validRoles);

        if (!empty($invalidRoles)) {
            throw new ValidationException('Invalid roles: ' . implode(', ', $invalidRoles));
        }

        // Create user via repository
        return $this->userRepository->create([
            'email' => $data['email'],
            'name' => $data['name'],
            'is_active' => true,
        ]);
    }

    /**
     * Get user by ID
     */
    public function findById(string $userId): User
    {
        $user = $this->userRepository->findById($userId);

        if (!$user) {
            throw new NotFoundException("User not found: {$userId}");
        }

        return $user;
    }
}
```

---

## Service Design Principles

### 1. Single Responsibility

Each service should have ONE clear purpose:

```php
// ✅ GOOD - Single responsibility
class UserService
{
    public function create(array $data): User {}
    public function update(string $id, array $data): User {}
    public function delete(string $id): void {}
}

class EmailService
{
    public function sendEmail(array $data): void {}
    public function sendBulkEmails(array $recipients): void {}
}

// ❌ BAD - Too many responsibilities
class UserService
{
    public function create(array $data): User {}
    public function sendWelcomeEmail(User $user): void {}  // Should be EmailService
    public function logUserActivity(User $user): void {}   // Should be AuditService
    public function processPayment(User $user): void {}    // Should be PaymentService
}
```

### 2. Clear Method Names

Method names should describe WHAT they do:

```php
// ✅ GOOD - Clear intent
public function createNotification(array $data): array
public function getUserPreferences(string $userId): UserPreference
public function shouldBatchEmail(UserPreference $prefs): bool
public function routeNotification(array $params): void

// ❌ BAD - Vague or misleading
public function process(): void
public function handle(): void
public function doIt(): void
public function execute(): void
```

### 3. Type Hints

Always use type hints:

```php
// ✅ GOOD - Explicit types
public function create(array $data): User {}
public function findAll(): Collection {}
public function delete(string $id): void {}

// ❌ BAD - No types
public function create($data) {}  // No types!
```

### 4. Error Handling

Services should throw meaningful exceptions:

```php
// ✅ GOOD - Meaningful exceptions
if (!$user) {
    throw new NotFoundException("User not found: {$userId}");
}

if ($this->userRepository->emailExists($email)) {
    throw new ConflictException('Email already exists');
}

// ❌ BAD - Generic errors
if (!$user) {
    throw new \Exception('Error');  // What error?
}
```

### 5. Avoid God Services

Don't create services that do everything:

```php
// ❌ BAD - God service
class WorkflowService
{
    public function startWorkflow(): void {}
    public function completeStep(): void {}
    public function assignRoles(): void {}
    public function sendNotifications(): void {}  // Should be NotificationService
    public function validatePermissions(): bool {}  // Should be PermissionService
    public function logAuditTrail(): void {}  // Should be AuditService
    // ... 50 more methods
}

// ✅ GOOD - Focused services
class WorkflowService
{
    public function __construct(
        private NotificationService $notificationService,
        private PermissionService $permissionService,
        private AuditService $auditService
    ) {}

    public function startWorkflow(array $data): void
    {
        // Orchestrate other services
        $this->permissionService->checkPermission($data['userId']);
        // Create workflow...
        $this->notificationService->notify($data);
        $this->auditService->log($data);
    }
}
```

---

## Caching Strategies

### 1. Cache Facade

```php
<?php

namespace App\Services;

use Illuminate\Support\Facades\Cache;

class UserService
{
    private const CACHE_TTL = 300; // 5 minutes

    public function getUser(string $userId): ?User
    {
        return Cache::remember(
            "user:{$userId}",
            self::CACHE_TTL,
            fn() => $this->userRepository->findById($userId)
        );
    }

    public function clearUserCache(string $userId): void
    {
        Cache::forget("user:{$userId}");
    }
}
```

### 2. Cache Invalidation

```php
<?php

namespace App\Services;

class UserService
{
    public function update(string $userId, array $data): User
    {
        // Update in database
        $user = $this->userRepository->update($userId, $data);

        // Invalidate cache
        $this->clearUserCache($userId);

        return $user;
    }
}
```

---

## Testing Services

### Unit Tests

```php
<?php

namespace Tests\Unit\Services;

use App\Exceptions\ConflictException;
use App\Repositories\UserRepository;
use App\Services\UserService;
use Tests\TestCase;

class UserServiceTest extends TestCase
{
    private UserService $userService;
    private UserRepository $userRepository;

    protected function setUp(): void
    {
        parent::setUp();

        $this->userRepository = $this->createMock(UserRepository::class);
        $this->userService = new UserService($this->userRepository);
    }

    public function test_create_throws_exception_when_email_exists(): void
    {
        // Arrange
        $userData = [
            'email' => 'test@example.com',
            'name' => 'Test User',
            'roles' => ['user'],
        ];

        $this->userRepository
            ->expects($this->once())
            ->method('emailExists')
            ->with($userData['email'])
            ->willReturn(true);

        // Act & Assert
        $this->expectException(ConflictException::class);
        $this->userService->create($userData);
    }

    public function test_create_user_when_email_is_unique(): void
    {
        // Arrange
        $userData = [
            'email' => 'test@example.com',
            'name' => 'Test User',
            'roles' => ['user'],
        ];

        $this->userRepository
            ->expects($this->once())
            ->method('emailExists')
            ->willReturn(false);

        $this->userRepository
            ->expects($this->once())
            ->method('create')
            ->willReturn(new \App\Models\User(['id' => '123']));

        // Act
        $user = $this->userService->create($userData);

        // Assert
        $this->assertNotNull($user);
    }
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main guide
- [routing-and-controllers.md](routing-and-controllers.md) - Controllers that use services
- [database-patterns.md](database-patterns.md) - Eloquent and repository patterns
- [complete-examples.md](complete-examples.md) - Full service/repository examples
