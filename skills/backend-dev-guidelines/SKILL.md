---
name: backend-dev-guidelines
description: Comprehensive backend development guide for Rails + Inertia.js applications. Use when creating routes, controllers, services, models, or working with Rails APIs, ActiveRecord, Inertia.js responses, validation, dependency injection, or async patterns. Covers layered architecture (routes → controllers → services → models), controller patterns, error handling, performance monitoring, testing strategies, and Rails best practices.
---

# Backend Development Guidelines

## Purpose

Establish consistency and best practices for Rails + Inertia.js applications using modern Ruby/Rails patterns.

## When to Use This Skill

Automatically activates when working on:
- Creating or modifying routes, endpoints, APIs
- Building controllers, services, models
- Implementing middleware (auth, validation, error handling)
- Database operations with ActiveRecord
- Error tracking and logging
- Input validation with Strong Parameters
- Configuration management
- Inertia.js responses and shared data
- Backend testing and refactoring

---

## Quick Start

### New Backend Feature Checklist

- [ ] **Route**: Clean definition in config/routes.rb
- [ ] **Controller**: Resourceful or custom controller
- [ ] **Service**: Business logic with DI (if needed)
- [ ] **Model**: ActiveRecord model with validations and associations
- [ ] **Strong Parameters**: Parameter whitelisting in controller
- [ ] **Serializer**: JSON serialization (if API)
- [ ] **Tests**: RSpec/Minitest tests
- [ ] **Config**: Use ENV and Rails.application.credentials

### New Rails Module Checklist

- [ ] Directory structure (see architecture-overview.md)
- [ ] Concern/Module inclusion (if needed)
- [ ] Middleware registration (if needed)
- [ ] Model factories and seeds
- [ ] Database migrations
- [ ] Exception handling
- [ ] Testing setup (Model + Request tests)

---

## Architecture Overview

### Layered Architecture

```
HTTP Request
    ↓
Routes (routing only)
    ↓
Middleware (auth, validation, etc.)
    ↓
Controllers (request handling)
    ↓
Strong Parameters (validation)
    ↓
Services (business logic)
    ↓
Models (ActiveRecord ORM)
    ↓
Database
```

**Key Principle:** Each layer has ONE responsibility.

---

## Directory Structure

```
app/
├── controllers/           # Request handlers
│   ├── api/              # API controllers
│   └── concerns/         # Shared controller logic
├── services/             # Business logic
├── models/               # ActiveRecord models
│   └── concerns/         # Shared model logic
├── serializers/          # JSON serializers
├── jobs/                 # Background jobs
└── mailers/              # Email handling
config/
├── routes.rb             # Route definitions
├── initializers/         # App configuration
└── credentials.yml.enc   # Encrypted secrets
db/
├── migrate/              # Database migrations
└── seeds.rb              # Database seeds
spec/                     # RSpec tests
├── models/               # Model tests
├── requests/             # Request/integration tests
├── services/             # Service tests
└── factories/            # Test factories
test/                     # Minitest (alternative to RSpec)
lib/                      # Custom libraries
```

**Naming Conventions:**
- Controllers: `PascalCase` - `UsersController`
- Services: `PascalCase` - `UserService`
- Models: `PascalCase` (singular) - `User`
- Files: `snake_case` - `users_controller.rb`

---

## Core Principles (7 Key Rules)

### 1. Routes Only Route, Controllers Control

```ruby
# ❌ NEVER: Business logic in routes
Rails.application.routes.draw do
  get '/submit' do
    # 200 lines of logic
  end
end

# ✅ ALWAYS: Delegate to controller
Rails.application.routes.draw do
  post '/submit', to: 'submissions#create'
  # Or use resourceful routes
  resources :submissions, only: [:create]
end
```

### 2. Use Strong Parameters for Validation

```ruby
# ✅ ALWAYS: Strong parameters in controller
class UsersController < ApplicationController
  def create
    @user = User.new(user_params)

    if @user.save
      redirect_to @user
    else
      render :new, status: :unprocessable_entity
    end
  end

  private

  def user_params
    params.require(:user).permit(:email, :name)
  end
end

# Model validations
class User < ApplicationRecord
  validates :email, presence: true, uniqueness: true
  validates :name, presence: true, length: { maximum: 255 }
end
```

### 3. Return Inertia Responses for Pages

```ruby
class PostsController < ApplicationController
  def index
    render inertia: {
      posts: Post.page(params[:page]).per(10)
    }
  end
end
```

**See [resources/inertia-rails-patterns.md](resources/inertia-rails-patterns.md) for complete Inertia.js patterns**

### 4. Use ENV and Rails Credentials, NEVER Hardcode

```ruby
# ❌ NEVER
timeout = 5000

# ✅ BETTER: Use ENV
timeout = ENV.fetch('TIMEOUT_MS', 5000)

# ✅ BEST: Use Rails credentials
timeout = Rails.application.credentials.timeout
```

### 5. Use ActiveRecord Associations

```ruby
# ✅ Define associations in models
class User < ApplicationRecord
  has_many :posts, dependent: :destroy
end

class Post < ApplicationRecord
  belongs_to :user
end

# Use eager loading to avoid N+1
@users = User.includes(:posts).all
```

### 6. Use Service Objects for Complex Business Logic

```ruby
# Service → Model
class UserRegistrationService
  def initialize(user_params)
    @user_params = user_params
  end

  def call
    User.transaction do
      user = User.create!(@user_params)
      send_welcome_email(user)
      user
    end
  end

  private

  def send_welcome_email(user)
    UserMailer.welcome(user).deliver_later
  end
end

# In controller
def create
  service = UserRegistrationService.new(user_params)
  @user = service.call
  redirect_to @user
rescue ActiveRecord::RecordInvalid => e
  render :new, status: :unprocessable_entity
end
```

### 7. Comprehensive Testing Required

```ruby
# RSpec model test
RSpec.describe User, type: :model do
  it 'validates presence of email' do
    user = User.new(email: nil)
    expect(user).not_to be_valid
    expect(user.errors[:email]).to include("can't be blank")
  end
end

# RSpec request test
RSpec.describe 'Posts', type: :request do
  describe 'POST /posts' do
    it 'creates a new post' do
      user = create(:user)

      post '/posts', params: { post: { title: 'Test' } },
                     headers: { 'Authorization' => "Bearer #{user.token}" }

      expect(response).to have_http_status(:created)
      expect(Post.count).to eq(1)
    end
  end
end
```

---

## Common Imports

```ruby
# Rails Core
require 'rails'

# ActiveRecord
class User < ApplicationRecord
  # ...
end

# Controllers
class ApplicationController < ActionController::Base
  # ...
end

# Inertia
class PostsController < ApplicationController
  def index
    render inertia: 'Posts/Index', props: { posts: @posts }
  end
end

# Services
class MyService
  def initialize(params)
    @params = params
  end

  def call
    # Business logic
  end
end

# Background Jobs
class MyJob < ApplicationJob
  queue_as :default

  def perform(*args)
    # Job logic
  end
end
```

---

## Quick Reference

### HTTP Status Codes

| Code | Use Case | Rails Symbol |
|------|----------|--------------|
| 200 | Success | `:ok` |
| 201 | Created | `:created` |
| 400 | Bad Request | `:bad_request` |
| 401 | Unauthorized | `:unauthorized` |
| 403 | Forbidden | `:forbidden` |
| 404 | Not Found | `:not_found` |
| 422 | Unprocessable Entity | `:unprocessable_entity` |
| 500 | Server Error | `:internal_server_error` |

### Rails Patterns

**Resourceful Routes** - RESTful resource operations
**Concerns** - Shared logic extraction
**Strong Parameters** - Parameter whitelisting
**Serializers** - Data transformation layer
**Service Objects** - Business logic extraction

---

## Anti-Patterns to Avoid

❌ Business logic in controllers or routes
❌ Hardcoded configuration (use ENV or credentials)
❌ Missing error handling
❌ No input validation
❌ N+1 query problems (use `includes`, `eager_load`)
❌ Mass assignment vulnerabilities (use strong parameters)
❌ Raw SQL without parameter binding

---

## Navigation Guide

| Need to... | Read this |
|------------|-----------|
| **Use Inertia.js** | **[inertia-rails-patterns.md](resources/inertia-rails-patterns.md)** |
| Understand architecture | architecture-overview.md |
| Create routes/controllers | routing-and-controllers.md |
| Organize business logic | services-and-models.md |
| Validate input | validation-patterns.md |
| Add error tracking | sentry-and-monitoring.md |
| Create middleware | middleware-guide.md |
| Database access | database-patterns.md |
| Manage config | configuration.md |
| Handle async/errors | async-and-errors.md |
| Write tests | testing-guide.md |
| See examples | complete-examples.md |

---

## Related Skills

- **frontend-dev-guidelines** - Inertia.js + React/TypeScript patterns
- **error-tracking** - Error tracking and logging patterns
- **rails-dev** - Sustainable Rails development patterns

---

**Skill Status**: COMPLETE ✅
**Stack**: Rails + Inertia.js + React ✅
