# Architecture Overview - Laravel + Inertia.js

Complete guide to the layered architecture pattern used in Laravel + Inertia.js applications.

## Table of Contents

- [Layered Architecture Pattern](#layered-architecture-pattern)
- [Request Lifecycle](#request-lifecycle)
- [Directory Structure Rationale](#directory-structure-rationale)
- [Module Organization](#module-organization)
- [Separation of Concerns](#separation-of-concerns)

---

## Layered Architecture Pattern

### The Five Layers

```
┌─────────────────────────────────────┐
│         HTTP Request                │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 1: ROUTES                    │
│  - Route definitions only           │
│  - Middleware registration          │
│  - Delegate to controllers          │
│  - NO business logic                │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 2: MIDDLEWARE                │
│  - Authentication                   │
│  - Authorization                    │
│  - Request transformation           │
│  - Inertia shared data              │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 3: CONTROLLERS               │
│  - Request/response handling        │
│  - Call Form Requests (validation)  │
│  - Call services                    │
│  - Return Inertia responses         │
│  - Error handling                   │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 4: SERVICES                  │
│  - Business logic                   │
│  - Orchestration                    │
│  - Call repositories                │
│  - No HTTP knowledge                │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│  Layer 5: REPOSITORIES              │
│  - Data access abstraction          │
│  - Eloquent operations              │
│  - Query optimization               │
│  - Caching                          │
└───────────────┬─────────────────────┘
                ↓
┌─────────────────────────────────────┐
│         Database (MySQL/Postgres)   │
└─────────────────────────────────────┘
```

### Why This Architecture?

**Testability:**
- Each layer can be tested independently
- Easy to mock dependencies
- Clear test boundaries

**Maintainability:**
- Changes isolated to specific layers
- Business logic separate from HTTP concerns
- Easy to locate bugs

**Reusability:**
- Services can be used by routes, commands, jobs
- Repositories hide database implementation
- Business logic not tied to HTTP

**Scalability:**
- Easy to add new endpoints
- Clear patterns to follow
- Consistent structure

---

## Request Lifecycle

### Complete Flow Example

```php
1. HTTP POST /users
   ↓
2. Laravel routing matches route in routes/web.php
   ↓
3. Middleware chain executes (Global + Route specific):
   - HandleInertiaRequests (Inertia setup)
   - Authenticate (authentication)
   - Authorize (authorization)
   ↓
4. Route handler delegates to controller:
   Route::post('/users', [UserController::class, 'store'])
   ↓
5. Controller receives Form Request:
   public function store(StoreUserRequest $request)
   - Laravel auto-validates via Form Request
   - Call userService->create($request->validated())
   - Return Inertia response
   ↓
6. Service executes business logic:
   - Check business rules
   - Call userRepository->create($data)
   - Return result
   ↓
7. Repository performs database operation:
   - User::create($data)
   - Handle database errors
   - Return created user
   ↓
8. Response flows back:
   Repository → Service → Controller → Inertia → React Component
```

### Middleware Execution Order

**Critical:** Middleware executes in registration order

**Global Middleware (app/Http/Kernel.php):**
```php
protected $middleware = [
    \App\Http\Middleware\TrustProxies::class,              // 1. Trust proxies
    \Illuminate\Http\Middleware\HandleCors::class,         // 2. CORS
    \Illuminate\Foundation\Http\Middleware\PreventRequestsDuringMaintenance::class, // 3. Maintenance mode
    \Illuminate\Foundation\Http\Middleware\ValidatePostSize::class, // 4. Validate post size
    \App\Http\Middleware\TrimStrings::class,               // 5. Trim strings
    \Illuminate\Foundation\Http\Middleware\ConvertEmptyStringsToNull::class, // 6. Convert empty strings
];
```

**Middleware Groups:**
```php
protected $middlewareGroups = [
    'web' => [
        \App\Http\Middleware\EncryptCookies::class,
        \Illuminate\Cookie\Middleware\AddQueuedCookiesToResponse::class,
        \Illuminate\Session\Middleware\StartSession::class,
        \Illuminate\View\Middleware\ShareErrorsFromSession::class,
        \App\Http\Middleware\VerifyCsrfToken::class,
        \Illuminate\Routing\Middleware\SubstituteBindings::class,
        \App\Http\Middleware\HandleInertiaRequests::class, // Inertia
    ],
];
```

**Rule:** Error handling is automatic via exception handler!

---

## Directory Structure Rationale

### Controllers Directory (app/Http/Controllers/)

**Purpose:** Handle HTTP request/response concerns

**Contents:**
- `Controller.php` - Base controller
- `{Feature}Controller.php` - Feature-specific controllers

**Naming:** PascalCase + Controller

**Responsibilities:**
- Receive Form Requests (auto-validated)
- Call appropriate service methods
- Return Inertia or JSON responses
- Handle errors (via exception handler)

**Types of Controllers:**
```php
// Resource Controller (RESTful)
class UserController extends Controller
{
    public function index() {}
    public function create() {}
    public function store(StoreUserRequest $request) {}
    public function show(User $user) {}
    public function edit(User $user) {}
    public function update(UpdateUserRequest $request, User $user) {}
    public function destroy(User $user) {}
}

// Invokable Controller (Single action)
class GenerateReportController extends Controller
{
    public function __invoke(GenerateReportRequest $request)
    {
        // Single responsibility
    }
}
```

### Form Requests Directory (app/Http/Requests/)

**Purpose:** Validation logic

**Contents:**
- `Store{Entity}Request.php` - Creation validation
- `Update{Entity}Request.php` - Update validation

**Naming:** `{Action}{Entity}Request`

**Responsibilities:**
- Define validation rules
- Authorization logic
- Custom validation messages
- Data preparation

**Example:**
```php
class StoreUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true; // or Gate::allows('create-user')
    }

    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'email', 'unique:users'],
        ];
    }
}
```

### Services Directory (app/Services/)

**Purpose:** Business logic and orchestration

**Contents:**
- `{Feature}Service.php` - Feature business logic

**Naming:** PascalCase + Service

**Responsibilities:**
- Implement business rules
- Orchestrate multiple repositories
- Transaction management
- Business validations
- No HTTP knowledge (no Request/Response types)

**Dependency Injection:**
```php
class UserService
{
    public function __construct(
        private UserRepository $userRepository,
        private NotificationService $notificationService
    ) {}
}
```

### Repositories Directory (app/Repositories/)

**Purpose:** Data access abstraction

**Contents:**
- `{Entity}Repository.php` - Database operations for entity

**Naming:** PascalCase + Repository

**Responsibilities:**
- Eloquent query operations
- Query optimization
- Database error handling
- Caching layer
- Hide Eloquent implementation details

**Example:**
```php
class UserRepository
{
    public function findActive(): Collection
    {
        return User::where('active', true)->get();
    }

    public function create(array $data): User
    {
        return User::create($data);
    }
}
```

**When to Use Repositories:**
- Complex queries used in multiple places
- Need to cache results
- Want to abstract database layer
- Testing requires mocking data access

**When NOT to Use Repositories:**
- Simple CRUD operations (use Eloquent directly)
- One-off queries
- Over-engineering risk

### Models Directory (app/Models/)

**Purpose:** Eloquent models and relationships

**Contents:**
- `{Entity}.php` - Model with relationships, accessors, mutators

**Naming:** PascalCase (singular)

**Responsibilities:**
- Define table name (if non-standard)
- Define fillable/guarded fields
- Define relationships (hasMany, belongsTo, etc.)
- Define accessors/mutators
- Define casts
- Define scopes

**Example:**
```php
class User extends Model
{
    protected $fillable = ['name', 'email', 'password'];

    protected $hidden = ['password', 'remember_token'];

    protected $casts = [
        'email_verified_at' => 'datetime',
        'is_admin' => 'boolean',
    ];

    public function posts(): HasMany
    {
        return $this->hasMany(Post::class);
    }
}
```

### Resources Directory (app/Http/Resources/)

**Purpose:** API response transformation

**Contents:**
- `{Entity}Resource.php` - Single model transformation
- `{Entity}Collection.php` - Collection transformation

**Naming:** PascalCase + Resource/Collection

**Use Cases:**
- API endpoints (not Inertia pages)
- Consistent data formatting
- Hide sensitive fields
- Add computed fields

**Example:**
```php
class UserResource extends JsonResource
{
    public function toArray($request): array
    {
        return [
            'id' => $this->id,
            'name' => $this->name,
            'email' => $this->email,
            'posts_count' => $this->posts->count(),
            'created_at' => $this->created_at->toDateString(),
        ];
    }
}
```

### Middleware Directory (app/Http/Middleware/)

**Purpose:** Cross-cutting concerns

**Contents:**
- Authentication middleware
- Authorization middleware
- Inertia shared data
- Custom middleware

**Naming:** PascalCase

**Types:**
- Before middleware (process request before controller)
- After middleware (process response after controller)
- Terminable middleware (after response sent to browser)

**HandleInertiaRequests Example:**
```php
class HandleInertiaRequests extends Middleware
{
    public function share(Request $request): array
    {
        return array_merge(parent::share($request), [
            'auth' => [
                'user' => $request->user(),
            ],
            'flash' => [
                'success' => $request->session()->get('success'),
                'error' => $request->session()->get('error'),
            ],
        ]);
    }
}
```

### Config Directory (config/)

**Purpose:** Configuration management

**Contents:**
- `app.php` - Application config
- `database.php` - Database connections
- `services.php` - Third-party services
- Custom config files

**Pattern:** Use config() helper, NEVER env() outside config files

**Example:**
```php
// config/services.php
return [
    'stripe' => [
        'key' => env('STRIPE_KEY'),
        'secret' => env('STRIPE_SECRET'),
    ],
];

// Usage in code
$stripeKey = config('services.stripe.key');
```

---

## Module Organization

### Feature-Based Organization

For large features, use subdirectories:

```
app/Modules/Workflow/
├── Controllers/       # Workflow controllers
├── Services/          # Workflow services
├── Models/            # Workflow models
├── Requests/          # Workflow validation
└── Repositories/      # Workflow data access
```

**When to use:**
- Feature has 5+ related files
- Clear domain boundaries exist
- Logical grouping improves clarity

**Implementation:**
```php
// Use custom namespace
namespace App\Modules\Workflow\Controllers;

// Or use service provider to register module
```

### Flat Organization

For simple features:

```
app/
├── Http/Controllers/UserController.php
├── Services/UserService.php
├── Models/User.php
└── Repositories/UserRepository.php
```

**When to use:**
- Simple features (< 5 files)
- No clear sub-domains
- Flat structure is clearer

---

## Separation of Concerns

### What Goes Where

**Routes Layer:**
- ✅ Route definitions
- ✅ Middleware registration
- ✅ Controller delegation
- ✅ Route grouping
- ❌ Business logic
- ❌ Database operations
- ❌ Validation logic (use Form Requests)

**Controllers Layer:**
- ✅ Receive Form Requests
- ✅ Service calls
- ✅ Return Inertia/JSON responses
- ✅ Flash messages
- ❌ Business logic
- ❌ Database operations
- ❌ Validation rules (use Form Requests)

**Services Layer:**
- ✅ Business logic
- ✅ Business rules enforcement
- ✅ Orchestration (multiple repos)
- ✅ Transaction management
- ❌ HTTP concerns (Request/Response)
- ❌ Direct Eloquent calls (use repositories for complex queries)

**Repositories Layer:**
- ✅ Eloquent operations
- ✅ Query construction
- ✅ Database error handling
- ✅ Caching
- ❌ Business logic
- ❌ HTTP concerns

### Example: User Creation

**Route (routes/web.php):**
```php
Route::post('/users', [UserController::class, 'store'])
    ->middleware(['auth', 'verified']);
```

**Form Request:**
```php
class StoreUserRequest extends FormRequest
{
    public function rules(): array
    {
        return [
            'name' => ['required', 'string', 'max:255'],
            'email' => ['required', 'email', 'unique:users'],
        ];
    }
}
```

**Controller:**
```php
class UserController extends Controller
{
    public function __construct(private UserService $userService) {}

    public function store(StoreUserRequest $request)
    {
        $user = $this->userService->create($request->validated());

        return redirect()->route('users.show', $user)
            ->with('success', 'User created successfully');
    }
}
```

**Service:**
```php
class UserService
{
    public function __construct(private UserRepository $userRepository) {}

    public function create(array $data): User
    {
        // Business rule: hash password
        $data['password'] = Hash::make($data['password']);

        return $this->userRepository->create($data);
    }
}
```

**Repository:**
```php
class UserRepository
{
    public function create(array $data): User
    {
        return User::create($data);
    }
}
```

**Notice:** Each layer has clear, distinct responsibilities!

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main guide
- [routing-and-controllers.md](routing-and-controllers.md) - Routes and controllers details
- [services-and-repositories.md](services-and-repositories.md) - Service and repository patterns
