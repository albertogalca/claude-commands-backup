# Validation Patterns - Form Requests and Validation

Complete guide to input validation using Laravel Form Requests for type-safe validation.

## Table of Contents

- [Why Form Requests?](#why-form-requests)
- [Basic Form Request Patterns](#basic-form-request-patterns)
- [Form Request Examples](#form-request-examples)
- [Controller Validation](#controller-validation)
- [Custom Validation Rules](#custom-validation-rules)
- [Error Handling](#error-handling)
- [Advanced Patterns](#advanced-patterns)

---

## Why Form Requests?

### Benefits Over Manual Validation

**Type Safety:**
- ✅ Separated validation logic
- ✅ Reusable validation rules
- ✅ Authorization logic included

**Developer Experience:**
- ✅ Clean controllers
- ✅ Composable rules
- ✅ Excellent error messages

**Performance:**
- ✅ Fast validation
- ✅ Automatic validation before controller
- ✅ Built-in Laravel framework

### Laravel Form Requests vs Manual Validation

```php
// ❌ OLD - Manual validation (avoid)
public function store(Request $request)
{
    $validated = $request->validate([
        'email' => 'required|email',
        'name' => 'required|min:3',
    ]);
}

// ✅ NEW - Form Requests (preferred)
public function store(CreateUserRequest $request)
{
    $validated = $request->validated();
}
```

---

## Basic Form Request Patterns

### Creating Form Requests

```bash
php artisan make:request CreateUserRequest
php artisan make:request UpdateUserRequest
```

### Basic Structure

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CreateUserRequest extends FormRequest
{
    /**
     * Determine if the user is authorized to make this request.
     */
    public function authorize(): bool
    {
        return true; // Or add authorization logic
    }

    /**
     * Get the validation rules that apply to the request.
     */
    public function rules(): array
    {
        return [
            'email' => 'required|email|unique:users',
            'name' => 'required|string|min:2|max:100',
            'age' => 'required|integer|min:18|max:120',
        ];
    }

    /**
     * Get custom messages for validator errors.
     */
    public function messages(): array
    {
        return [
            'email.required' => 'Please provide an email address',
            'email.email' => 'Please provide a valid email address',
            'email.unique' => 'This email is already registered',
            'name.min' => 'Name must be at least 2 characters',
            'age.min' => 'You must be at least 18 years old',
        ];
    }
}
```

### Common Validation Rules

```php
// Strings
'name' => 'required|string|min:2|max:100',
'email' => 'required|email',
'url' => 'required|url',
'uuid' => 'required|uuid',

// Numbers
'age' => 'required|integer|min:18',
'price' => 'required|numeric|min:0',
'percentage' => 'required|integer|between:0,100',

// Booleans
'is_active' => 'required|boolean',

// Dates
'birth_date' => 'required|date',
'starts_at' => 'required|date_format:Y-m-d H:i:s',
'expires_at' => 'required|date|after:starts_at',

// Enums
'role' => 'required|in:admin,operations,user',
'status' => 'required|in:PENDING,APPROVED,REJECTED',

// Arrays
'tags' => 'required|array|min:1|max:10',
'tags.*' => 'string|max:50',

// Files
'avatar' => 'required|image|max:2048', // 2MB max
'document' => 'required|file|mimes:pdf,doc,docx|max:10240', // 10MB max
```

---

## Form Request Examples

### User Validation

**File:** `app/Http/Requests/CreateUserRequest.php`

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class CreateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'email' => [
                'required',
                'email',
                'max:255',
                Rule::unique('users')->whereNull('deleted_at'),
            ],
            'name' => 'required|string|min:2|max:100',
            'password' => 'required|string|min:8|confirmed',
            'roles' => 'required|array',
            'roles.*' => Rule::in(['admin', 'operations', 'user']),
        ];
    }

    public function messages(): array
    {
        return [
            'email.unique' => 'This email address is already registered.',
            'password.confirmed' => 'Password confirmation does not match.',
            'roles.*.in' => 'Invalid role selected.',
        ];
    }
}
```

**File:** `app/Http/Requests/UpdateUserRequest.php`

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class UpdateUserRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        $userId = $this->route('id');

        return [
            'email' => [
                'sometimes',
                'email',
                'max:255',
                Rule::unique('users')->ignore($userId)->whereNull('deleted_at'),
            ],
            'name' => 'sometimes|string|min:2|max:100',
            'roles' => 'sometimes|array',
            'roles.*' => Rule::in(['admin', 'operations', 'user']),
        ];
    }
}
```

### Form Validation Schemas

**File:** `app/Http/Requests/CreateQuestionRequest.php`

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class CreateQuestionRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'form_id' => 'required|integer|exists:forms,id',
            'section_id' => 'required|integer|exists:sections,id',
            'label' => 'required|string|max:500',
            'description' => 'nullable|string|max:5000',
            'type' => [
                'required',
                Rule::in([
                    'input', 'textbox', 'editor', 'dropdown',
                    'autocomplete', 'checkbox', 'radio', 'upload'
                ]),
            ],
            'upload_types' => 'nullable|array',
            'upload_types.*' => Rule::in(['pdf', 'image', 'excel', 'video', 'powerpoint', 'word']),
            'input_type' => 'nullable|in:date,number,input,currency',
            'options' => 'nullable|array',
            'options.*.label' => 'required|string|max:100',
            'options.*.control_tag' => 'nullable|string|max:150',
            'options.*.order' => 'required|integer|min:0',
            'required' => 'required|boolean',
            'is_standard' => 'nullable|boolean',
            'max_length' => 'nullable|integer|min:1',
        ];
    }
}
```

### Proxy Relationship Validation

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;

class CreateProxyRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'original_user_id' => 'required|string|exists:users,id',
            'proxy_user_id' => 'required|string|exists:users,id|different:original_user_id',
            'starts_at' => 'required|date',
            'expires_at' => 'required|date|after:starts_at',
        ];
    }

    public function messages(): array
    {
        return [
            'proxy_user_id.different' => 'Proxy user must be different from original user.',
            'expires_at.after' => 'Expiration date must be after start date.',
        ];
    }
}
```

### Workflow Validation

```php
<?php

namespace App\Http\Requests;

use Illuminate\Foundation\Http\FormRequest;
use Illuminate\Validation\Rule;

class StartWorkflowRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'workflow_code' => 'required|string',
            'entity_type' => Rule::in(['Post', 'User', 'Comment']),
            'entity_id' => 'required|integer',
            'dry_run' => 'nullable|boolean',
        ];
    }
}

class CompleteStepRequest extends FormRequest
{
    public function authorize(): bool
    {
        return true;
    }

    public function rules(): array
    {
        return [
            'step_instance_id' => 'required|integer|exists:step_instances,id',
            'answers' => 'required|array',
            'answers.*' => 'required',
            'dry_run' => 'nullable|boolean',
        ];
    }
}
```

---

## Controller Validation

### Pattern: Controller with Form Request (Recommended)

```php
<?php

namespace App\Http\Controllers;

use App\Http\Requests\CreateUserRequest;
use App\Http\Requests\UpdateUserRequest;
use App\Services\UserService;
use Illuminate\Http\JsonResponse;

class UserController extends Controller
{
    public function __construct(
        private UserService $userService
    ) {}

    public function store(CreateUserRequest $request): JsonResponse
    {
        try {
            // Validation already done by Form Request
            $validated = $request->validated();

            $user = $this->userService->create($validated);

            return $this->handleSuccess($user, 'User created successfully', 201);
        } catch (\Throwable $e) {
            return $this->handleError($e, 'store');
        }
    }

    public function update(UpdateUserRequest $request, string $id): JsonResponse
    {
        try {
            $validated = $request->validated();

            $user = $this->userService->update($id, $validated);

            return $this->handleSuccess($user, 'User updated successfully');
        } catch (\Throwable $e) {
            return $this->handleError($e, 'update');
        }
    }
}
```

**Pros:**
- Clean separation
- Reusable validation
- Easy to test
- Automatic validation before controller

---

## Custom Validation Rules

### Creating Custom Rules

```bash
php artisan make:rule Uppercase
```

```php
<?php

namespace App\Rules;

use Closure;
use Illuminate\Contracts\Validation\ValidationRule;

class Uppercase implements ValidationRule
{
    /**
     * Run the validation rule.
     */
    public function validate(string $attribute, mixed $value, Closure $fail): void
    {
        if (strtoupper($value) !== $value) {
            $fail('The :attribute must be uppercase.');
        }
    }
}
```

**Usage:**

```php
use App\Rules\Uppercase;

public function rules(): array
{
    return [
        'code' => ['required', 'string', new Uppercase()],
    ];
}
```

### Conditional Validation

```php
public function rules(): array
{
    return [
        'type' => 'required|in:NEW,UPDATE',
        'post_id' => Rule::requiredIf($this->input('type') === 'UPDATE'),
    ];
}
```

### Database Validation

```php
use Illuminate\Validation\Rule;

public function rules(): array
{
    return [
        'email' => [
            'required',
            'email',
            Rule::unique('users')->where(function ($query) {
                return $query->where('is_active', true);
            }),
        ],
        'category_id' => 'required|exists:categories,id,deleted_at,NULL',
    ];
}
```

---

## Error Handling

### Validation Error Format

Laravel automatically formats validation errors:

```json
{
    "message": "The given data was invalid.",
    "errors": {
        "email": [
            "The email field is required."
        ],
        "name": [
            "The name must be at least 2 characters."
        ]
    }
}
```

### Custom Error Messages

```php
public function messages(): array
{
    return [
        'email.required' => 'Please provide an email address',
        'email.email' => 'Please provide a valid email address',
        'name.min' => 'Name must be at least :min characters',
        'age.min' => 'You must be at least :min years old',
    ];
}
```

### Custom Attributes

```php
public function attributes(): array
{
    return [
        'email' => 'email address',
        'password_confirmation' => 'password confirmation',
    ];
}
```

### Formatted Error Response

```php
// In app/Exceptions/Handler.php

use Illuminate\Validation\ValidationException;

protected function invalidJson($request, ValidationException $exception)
{
    return response()->json([
        'success' => false,
        'message' => 'Validation failed',
        'errors' => collect($exception->errors())->map(function ($errors, $field) {
            return [
                'field' => $field,
                'messages' => $errors,
            ];
        })->values(),
    ], $exception->status);
}
```

---

## Advanced Patterns

### After Validation Hook

```php
public function withValidator($validator)
{
    $validator->after(function ($validator) {
        if ($this->somethingElseIsInvalid()) {
            $validator->errors()->add('field', 'Something is wrong with this field!');
        }
    });
}
```

### Prepare For Validation

```php
protected function prepareForValidation()
{
    $this->merge([
        'email' => strtolower($this->email),
        'name' => trim($this->name),
    ]);
}
```

### Array Validation

```php
public function rules(): array
{
    return [
        'users' => 'required|array|min:1',
        'users.*.name' => 'required|string',
        'users.*.email' => 'required|email|unique:users,email',
        'users.*.roles' => 'required|array',
        'users.*.roles.*' => 'string|in:admin,user',
    ];
}
```

### Conditional Rules

```php
use Illuminate\Validation\Rule;

public function rules(): array
{
    return [
        'notification_type' => 'required|in:email,sms',
        'email_address' => Rule::requiredIf($this->notification_type === 'email'),
        'phone_number' => Rule::requiredIf($this->notification_type === 'sms'),
    ];
}
```

### Custom Authorization

```php
public function authorize(): bool
{
    $user = $this->user();

    // Only allow admins or the user themselves to update
    return $user->isAdmin() || $user->id === $this->route('id');
}
```

### Validation with Enums (PHP 8.1+)

```php
<?php

namespace App\Enums;

enum UserRole: string
{
    case ADMIN = 'admin';
    case OPERATIONS = 'operations';
    case USER = 'user';

    public static function values(): array
    {
        return array_column(self::cases(), 'value');
    }
}
```

```php
use App\Enums\UserRole;
use Illuminate\Validation\Rule;

public function rules(): array
{
    return [
        'role' => ['required', Rule::in(UserRole::values())],
        // Or with Laravel 10+:
        'role' => ['required', Rule::enum(UserRole::class)],
    ];
}
```

### Sometimes Validation

```php
public function rules(): array
{
    return [
        // Only validate if present
        'email' => 'sometimes|email|unique:users',
        'name' => 'sometimes|string|min:2',

        // Use for partial updates
        'profile.bio' => 'sometimes|string|max:500',
    ];
}
```

### Nested Object Validation

```php
public function rules(): array
{
    return [
        'user' => 'required|array',
        'user.name' => 'required|string',
        'user.email' => 'required|email',
        'user.address' => 'required|array',
        'user.address.street' => 'required|string',
        'user.address.city' => 'required|string',
        'user.address.zip' => 'required|regex:/^\d{5}$/',
    ];
}
```

### File Validation

```php
public function rules(): array
{
    return [
        'avatar' => 'required|image|mimes:jpeg,png,jpg,gif|max:2048',
        'document' => 'required|file|mimes:pdf,doc,docx|max:10240',
        'csv_file' => 'required|file|mimetypes:text/csv,text/plain',
    ];
}
```

---

**Related Files:**
- [SKILL.md](SKILL.md) - Main guide
- [routing-and-controllers.md](routing-and-controllers.md) - Using validation in controllers
- [services-and-repositories.md](services-and-repositories.md) - Using validated data in services
- [async-and-errors.md](async-and-errors.md) - Error handling patterns
