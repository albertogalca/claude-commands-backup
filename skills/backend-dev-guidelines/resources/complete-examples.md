# Complete Examples - Full Working Code

Real-world examples showing complete implementation patterns in Laravel.

## Table of Contents

- [Complete Controller Example](#complete-controller-example)
- [Complete Service with DI](#complete-service-with-di)
- [Complete Route File](#complete-route-file)
- [Complete Repository](#complete-repository)
- [Refactoring Example: Bad to Good](#refactoring-example-bad-to-good)
- [End-to-End Feature Example](#end-to-end-feature-example)

---

## Complete Controller Example

### UserController (Following All Best Practices)

```php
// app/Http/Controllers/UserController.php
namespace App\Http\Controllers;

use App\Http\Requests\CreateUserRequest;
use App\Http\Requests\UpdateUserRequest;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;
use Sentry\Laravel\Facade as Sentry;

class UserController extends BaseController
{
    public function __construct(
        private readonly UserService $userService
    ) {}

    public function show(int $id): JsonResponse
    {
        try {
            Sentry::addBreadcrumb([
                'category' => 'user_controller',
                'message' => 'Fetching user',
                'data' => ['user_id' => $id],
            ]);

            $user = Sentry::traceFunction(
                'user.get',
                fn () => $this->userService->findById($id)
            );

            if (!$user) {
                return $this->handleError(
                    new \App\Exceptions\NotFoundException('User not found'),
                    'show',
                    404
                );
            }

            return $this->handleSuccess($user);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'show');
        }
    }

    public function index(): JsonResponse
    {
        try {
            $users = $this->userService->getAll();
            return $this->handleSuccess($users);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'index');
        }
    }

    public function store(CreateUserRequest $request): JsonResponse
    {
        try {
            // Validation happens automatically via FormRequest
            $validated = $request->validated();

            // Track performance
            $user = Sentry::traceFunction(
                'user.create',
                fn () => $this->userService->create($validated)
            );

            return $this->handleSuccess($user, 'User created successfully', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }

    public function update(UpdateUserRequest $request, int $id): JsonResponse
    {
        try {
            $validated = $request->validated();
            $user = $this->userService->update($id, $validated);

            return $this->handleSuccess($user, 'User updated');
        } catch (\Throwable $e) {
            return $this->handleError($e, 'update');
        }
    }

    public function destroy(int $id): JsonResponse
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

---

## Complete Service with DI

### UserService

```php
// app/Services/UserService.php
namespace App\Services;

use App\Repositories\UserRepository;
use App\Exceptions\{ConflictException, NotFoundException, ValidationException};
use App\Models\User;
use Illuminate\Database\Eloquent\Collection;

class UserService
{
    public function __construct(
        private readonly UserRepository $userRepository
    ) {}

    public function findById(int $id): ?User
    {
        return $this->userRepository->findById($id);
    }

    public function getAll(): Collection
    {
        return $this->userRepository->findActive();
    }

    public function create(array $data): User
    {
        // Business rule: validate age
        if (($data['age'] ?? 0) < 18) {
            throw new ValidationException('User must be 18 or older');
        }

        // Business rule: check email uniqueness
        $existing = $this->userRepository->findByEmail($data['email']);
        if ($existing) {
            throw new ConflictException('Email already in use');
        }

        // Create user with profile
        return $this->userRepository->create([
            'email' => $data['email'],
            'name' => $data['name'],
            'profile' => [
                'first_name' => $data['first_name'],
                'last_name' => $data['last_name'],
                'age' => $data['age'],
            ],
        ]);
    }

    public function update(int $id, array $data): User
    {
        // Check exists
        $existing = $this->userRepository->findById($id);
        if (!$existing) {
            throw new NotFoundException('User not found');
        }

        // Business rule: email uniqueness if changing
        if (isset($data['email']) && $data['email'] !== $existing->email) {
            $emailTaken = $this->userRepository->findByEmail($data['email']);
            if ($emailTaken) {
                throw new ConflictException('Email already in use');
            }
        }

        return $this->userRepository->update($id, $data);
    }

    public function delete(int $id): void
    {
        $existing = $this->userRepository->findById($id);
        if (!$existing) {
            throw new NotFoundException('User not found');
        }

        $this->userRepository->delete($id);
    }
}
```

---

## Complete Route File

### api.php

```php
// routes/api.php
use App\Http\Controllers\UserController;
use Illuminate\Support\Facades\Route;

Route::middleware(['auth:sanctum', 'audit'])->group(function () {
    // GET /api/users - List all users
    Route::get('/users', [UserController::class, 'index']);

    // GET /api/users/{id} - Get single user
    Route::get('/users/{id}', [UserController::class, 'show']);

    // POST /api/users - Create user
    Route::post('/users', [UserController::class, 'store']);

    // PUT /api/users/{id} - Update user
    Route::put('/users/{id}', [UserController::class, 'update']);

    // DELETE /api/users/{id} - Delete user
    Route::delete('/users/{id}', [UserController::class, 'destroy']);
});

// Or use resource route
Route::middleware(['auth:sanctum', 'audit'])->group(function () {
    Route::apiResource('users', UserController::class);
});
```

---

## Complete Repository

### UserRepository

```php
// app/Repositories/UserRepository.php
namespace App\Repositories;

use App\Models\User;
use Illuminate\Database\Eloquent\Collection;
use Illuminate\Support\Facades\DB;

class UserRepository
{
    public function findById(int $id): ?User
    {
        return User::with('profile')->find($id);
    }

    public function findByEmail(string $email): ?User
    {
        return User::with('profile')
            ->where('email', $email)
            ->first();
    }

    public function findActive(): Collection
    {
        return User::with('profile')
            ->where('is_active', true)
            ->orderBy('created_at', 'desc')
            ->get();
    }

    public function create(array $data): User
    {
        return DB::transaction(function () use ($data) {
            $profileData = $data['profile'] ?? [];
            unset($data['profile']);

            $user = User::create($data);

            if (!empty($profileData)) {
                $user->profile()->create($profileData);
                $user->load('profile');
            }

            return $user;
        });
    }

    public function update(int $id, array $data): User
    {
        $user = User::findOrFail($id);

        return DB::transaction(function () use ($user, $data) {
            $profileData = $data['profile'] ?? [];
            unset($data['profile']);

            $user->update($data);

            if (!empty($profileData) && $user->profile) {
                $user->profile->update($profileData);
            }

            return $user->fresh('profile');
        });
    }

    public function delete(int $id): void
    {
        // Soft delete
        $user = User::findOrFail($id);
        $user->update([
            'is_active' => false,
            'deleted_at' => now(),
        ]);
    }
}
```

---

## Refactoring Example: Bad to Good

### BEFORE: Business Logic in Routes ❌

```php
// routes/api.php (BAD - 200+ lines in route closure)
Route::post('/posts', function (Request $request) {
    try {
        $username = $request->user()->name;
        $responses = $request->input('responses');
        $stepInstanceId = $request->input('stepInstanceId');

        // ❌ Permission check in route
        $userId = app(UserProfileService::class)
            ->getProfileByEmail($username)
            ->id;

        $canComplete = app(PermissionService::class)
            ->canCompleteStep($userId, $stepInstanceId);

        if (!$canComplete) {
            return response()->json(['error' => 'No permission'], 403);
        }

        // ❌ Business logic in route
        $post = Post::create([
            'title' => $request->input('title'),
            'content' => $request->input('content'),
            'author_id' => $userId,
        ]);

        // ❌ More business logic...
        if (session()->has('impersonating')) {
            // Store impersonation context...
        }

        // ... 100+ more lines

        return response()->json(['success' => true, 'data' => $result]);
    } catch (\Throwable $e) {
        return response()->json(['error' => $e->getMessage()], 500);
    }
});
```

### AFTER: Clean Separation ✅

**1. Clean Route:**

```php
// routes/api.php
use App\Http\Controllers\PostController;

Route::middleware(['auth:sanctum', 'audit'])->group(function () {
    // ✅ CLEAN: Single line!
    Route::post('/posts', [PostController::class, 'store']);
});
```

**2. Controller:**

```php
// app/Http/Controllers/PostController.php
namespace App\Http\Controllers;

use App\Http\Requests\CreatePostRequest;
use App\Services\PostService;
use Illuminate\Http\JsonResponse;

class PostController extends BaseController
{
    public function __construct(
        private readonly PostService $postService
    ) {}

    public function store(CreatePostRequest $request): JsonResponse
    {
        try {
            $validated = $request->validated();

            $result = $this->postService->createPost(
                $validated,
                $request->user()->id
            );

            return $this->handleSuccess($result, 'Post created successfully');
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }
}
```

**3. Service:**

```php
// app/Services/PostService.php
namespace App\Services;

use App\Repositories\PostRepository;
use App\Exceptions\ForbiddenException;
use Illuminate\Support\Facades\Context;

class PostService
{
    public function __construct(
        private readonly PostRepository $postRepository,
        private readonly PermissionService $permissionService
    ) {}

    public function createPost(array $data, int $userId): array
    {
        // Permission check
        $canComplete = $this->permissionService->canCompleteStep(
            $userId,
            $data['step_instance_id']
        );

        if (!$canComplete) {
            throw new ForbiddenException('No permission to complete step');
        }

        // Execute workflow
        $engine = app(WorkflowEngine::class);
        $command = new CompleteStepCommand(
            $data['step_instance_id'],
            $userId,
            $data['responses']
        );
        $events = $engine->executeCommand($command);

        // Handle impersonation
        $auditContext = Context::get('audit');
        if ($auditContext['impersonated_by'] ?? null) {
            $this->handleImpersonation($data['step_instance_id'], $auditContext);
        }

        return ['events' => $events, 'success' => true];
    }

    private function handleImpersonation(int $stepInstanceId, array $context): void
    {
        app(ImpersonationStore::class)->storeContext($stepInstanceId, [
            'original_user_id' => $context['impersonated_by'],
            'effective_user_id' => $context['user_id'],
        ]);
    }
}
```

**Result:**
- Route: 1 line (was 200+)
- Controller: 25 lines
- Service: 40 lines
- **Testable, maintainable, reusable!**

---

## End-to-End Feature Example

### Complete User Management Feature

**1. Model:**

```php
// app/Models/User.php
namespace App\Models;

use Illuminate\Database\Eloquent\Factories\HasFactory;
use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Relations\HasOne;

class User extends Model
{
    use HasFactory;

    protected $fillable = ['email', 'name', 'is_active'];

    protected $casts = [
        'is_active' => 'boolean',
    ];

    public function profile(): HasOne
    {
        return $this->hasOne(UserProfile::class);
    }
}
```

**2. Form Request (Validation):**

```php
// app/Http/Requests/CreateUserRequest.php
namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => 'required|email|unique:users',
            'name' => 'required|string|min:1|max:100',
            'first_name' => 'required|string|min:1|max:100',
            'last_name' => 'required|string|min:1|max:100',
            'age' => 'required|integer|min:18|max:120',
        ];
    }
}
```

**3. Repository:**

```php
// app/Repositories/UserRepository.php
namespace App\Repositories;

use App\Models\User;

class UserRepository
{
    public function findById(int $id): ?User
    {
        return User::with('profile')->find($id);
    }

    public function create(array $data): User
    {
        return User::create($data);
    }
}
```

**4. Service:**

```php
// app/Services/UserService.php
namespace App\Services;

use App\Repositories\UserRepository;
use App\Exceptions\ConflictException;
use App\Models\User;

class UserService
{
    public function __construct(
        private readonly UserRepository $userRepository
    ) {}

    public function create(array $data): User
    {
        $existing = $this->userRepository->findByEmail($data['email']);
        if ($existing) {
            throw new ConflictException('Email already exists');
        }

        return $this->userRepository->create([
            'email' => $data['email'],
            'name' => $data['name'],
            'profile' => [
                'first_name' => $data['first_name'],
                'last_name' => $data['last_name'],
                'age' => $data['age'],
            ],
        ]);
    }
}
```

**5. Controller:**

```php
// app/Http/Controllers/UserController.php
namespace App\Http\Controllers;

use App\Http\Requests\CreateUserRequest;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;

class UserController extends BaseController
{
    public function __construct(
        private readonly UserService $userService
    ) {}

    public function store(CreateUserRequest $request): JsonResponse
    {
        try {
            $user = $this->userService->create($request->validated());
            return $this->handleSuccess($user, 'User created', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }
}
```

**6. Routes:**

```php
// routes/api.php
use App\Http\Controllers\UserController;

Route::middleware('auth:sanctum')->group(function () {
    Route::post('/users', [UserController::class, 'store']);
});
```

**Complete Request Flow:**

```
POST /api/users
  ↓
Route matches /users
  ↓
auth:sanctum middleware authenticates
  ↓
CreateUserRequest validates input
  ↓
UserController::store called
  ↓
UserService::create called
  ↓
Checks business rules
  ↓
UserRepository::create called
  ↓
Eloquent creates user
  ↓
Returns up the chain
  ↓
Controller formats response
  ↓
201 Created sent to client
```

---

**Related Files:**
- [SKILL.md](SKILL.md)
- [routing-and-controllers.md](routing-and-controllers.md)
- [services-and-repositories.md](services-and-repositories.md)
- [validation-patterns.md](validation-patterns.md)
