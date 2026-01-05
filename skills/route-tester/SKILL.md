---
name: route-tester
description: Test routes in your Rails application using authentication. Use this skill when testing API endpoints, validating route functionality, or debugging authentication issues. Includes patterns for testing with Devise, session auth, and RSpec/Minitest.
---

# Rails Route Tester Skill

## Purpose
This skill provides patterns for testing authenticated routes in Rails applications.

## When to Use This Skill
- Testing new API endpoints
- Validating route functionality after changes
- Debugging authentication issues
- Testing POST/PUT/DELETE operations
- Verifying request/response data

## Rails Authentication Overview

Rails supports multiple authentication methods:
- **Session-based** - Traditional web authentication (default for web)
- **Devise** - Popular authentication gem
- **JWT** - Token-based authentication for APIs
- **Rails built-in** - has_secure_password with bcrypt

## Testing Methods

### Method 1: RSpec Request Tests (RECOMMENDED)

Rails request tests are the best way to test routes.

**Location**: `spec/requests/`

#### Basic GET Request Test

```ruby
# spec/requests/posts_spec.rb
require 'rails_helper'

RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }

  describe 'GET /posts' do
    it 'returns a successful response' do
      sign_in user
      get posts_path

      expect(response).to have_http_status(:success)
    end

    context 'with Inertia' do
      it 'renders the correct component' do
        sign_in user
        get posts_path

        expect(response).to have_http_status(:success)
        # Check Inertia props if needed
        props = JSON.parse(response.headers['X-Inertia'])
        expect(props['component']).to eq('Posts/Index')
      end
    end
  end
end
```

#### POST Request Test with Validation

```ruby
RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }

  describe 'POST /posts' do
    context 'with valid params' do
      it 'creates a new post' do
        sign_in user

        expect {
          post posts_path, params: { post: { title: 'Test', content: 'Content' } }
        }.to change(Post, :count).by(1)

        expect(response).to have_http_status(:redirect)
        expect(Post.last.user).to eq(user)
      end
    end

    context 'with invalid params' do
      it 'does not create a post' do
        sign_in user

        expect {
          post posts_path, params: { post: { title: '' } }
        }.not_to change(Post, :count)

        expect(response).to have_http_status(:unprocessable_entity)
      end
    end
  end
end
```

#### API Request Test with Token Auth

```ruby
# spec/requests/api/users_spec.rb
require 'rails_helper'

RSpec.describe 'API::Users', type: :request do
  let(:user) { create(:user) }
  let(:token) { JWT.encode({ user_id: user.id }, Rails.application.secret_key_base) }

  describe 'GET /api/users/:id' do
    it 'returns user data' do
      get api_user_path(user), headers: { 'Authorization' => "Bearer #{token}" }

      expect(response).to have_http_status(:success)
      json = JSON.parse(response.body)
      expect(json['id']).to eq(user.id)
      expect(json['email']).to eq(user.email)
    end

    it 'returns unauthorized without token' do
      get api_user_path(user)

      expect(response).to have_http_status(:unauthorized)
    end
  end
end
```

### Method 2: Minitest Integration Tests

```ruby
# test/integration/posts_test.rb
require 'test_helper'

class PostsTest < ActionDispatch::IntegrationTest
  setup do
    @user = users(:one)
    sign_in @user
  end

  test 'should get index' do
    get posts_url
    assert_response :success
  end

  test 'should create post' do
    assert_difference('Post.count') do
      post posts_url, params: { post: { title: 'Test', content: 'Content' } }
    end

    assert_redirected_to post_url(Post.last)
  end
end
```

### Method 3: Manual Testing with curl

```bash
# Start Rails server
rails server

# Session auth - Get CSRF token and cookie
CSRF_TOKEN=$(curl -c cookies.txt http://localhost:3000/login \
  -s | grep csrf-token | sed 's/.*content="\([^"]*\)".*/\1/')

# Login
curl -b cookies.txt -c cookies.txt \
  -X POST http://localhost:3000/login \
  -H "Content-Type: application/json" \
  -H "X-CSRF-Token: $CSRF_TOKEN" \
  -d '{"user":{"email":"test@example.com","password":"password"}}'

# Use session for subsequent requests
curl -b cookies.txt http://localhost:3000/posts

# JWT token auth
TOKEN="your-jwt-token-here"
curl -H "Authorization: Bearer $TOKEN" \
     -H "Accept: application/json" \
     http://localhost:3000/api/users
```

## Common Testing Patterns

### Test with Devise

```ruby
# spec/rails_helper.rb
RSpec.configure do |config|
  config.include Devise::Test::IntegrationHelpers, type: :request
end

# spec/requests/posts_spec.rb
RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }

  it 'allows authenticated user to access posts' do
    sign_in user
    get posts_path

    expect(response).to have_http_status(:success)
  end

  it 'redirects unauthenticated user' do
    get posts_path

    expect(response).to have_http_status(:redirect)
    expect(response).to redirect_to(new_user_session_path)
  end
end
```

### Test Inertia Response

```ruby
RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }

  it 'renders Inertia page with correct data' do
    sign_in user
    create_list(:post, 3)

    get posts_path

    expect(response).to have_http_status(:success)

    # Parse Inertia response
    inertia_data = JSON.parse(response.headers['X-Inertia'])
    expect(inertia_data['component']).to eq('Posts/Index')
    expect(inertia_data['props']['posts'].size).to eq(3)
  end
end
```

### Test API JSON Response

```ruby
RSpec.describe 'API::Posts', type: :request do
  let(:user) { create(:user) }
  let(:auth_headers) { { 'Authorization' => "Bearer #{user.token}" } }

  it 'returns JSON with correct structure' do
    get api_posts_path, headers: auth_headers

    expect(response).to have_http_status(:success)
    expect(response.content_type).to match(/application\/json/)

    json = JSON.parse(response.body)
    expect(json).to have_key('data')
    expect(json['data']).to be_an(Array)
  end
end
```

### Test Authorization

```ruby
RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }
  let(:other_user) { create(:user) }
  let(:post) { create(:post, user: other_user) }

  it 'prevents user from deleting another user\'s post' do
    sign_in user

    expect {
      delete post_path(post)
    }.not_to change(Post, :count)

    expect(response).to have_http_status(:forbidden)
  end

  it 'allows user to delete their own post' do
    my_post = create(:post, user: user)
    sign_in user

    expect {
      delete post_path(my_post)
    }.to change(Post, :count).by(-1)

    expect(response).to have_http_status(:redirect)
  end
end
```

### Test File Upload

```ruby
RSpec.describe 'Uploads', type: :request do
  let(:user) { create(:user) }

  it 'uploads a file successfully' do
    sign_in user

    file = fixture_file_upload('test.jpg', 'image/jpeg')

    post uploads_path, params: { upload: { file: file } }

    expect(response).to have_http_status(:success)
    expect(Upload.last.file).to be_attached
  end
end
```

### Test with Database Transactions

```ruby
RSpec.configure do |config|
  config.use_transactional_fixtures = true
end

RSpec.describe 'Users', type: :request do
  it 'creates a new user' do
    expect {
      post users_path, params: {
        user: {
          email: 'test@example.com',
          password: 'password',
          password_confirmation: 'password'
        }
      }
    }.to change(User, :count).by(1)

    expect(response).to have_http_status(:redirect)
    expect(User.last.email).to eq('test@example.com')
  end
end
```

## Rails Route Testing Best Practices

### 1. Use FactoryBot for Test Data

```ruby
# spec/factories/users.rb
FactoryBot.define do
  factory :user do
    sequence(:email) { |n| "user#{n}@example.com" }
    password { 'password123' }

    trait :admin do
      role { :admin }
    end
  end
end

# Usage
admin = create(:user, :admin)
users = create_list(:user, 5)
```

### 2. Test Middleware/Filters

```ruby
RSpec.describe 'Admin::Dashboard', type: :request do
  let(:user) { create(:user) }
  let(:admin) { create(:user, :admin) }

  it 'denies access to regular users' do
    sign_in user
    get admin_dashboard_path

    expect(response).to have_http_status(:forbidden)
  end

  it 'allows access to admins' do
    sign_in admin
    get admin_dashboard_path

    expect(response).to have_http_status(:success)
  end
end
```

### 3. Test Strong Parameters

```ruby
RSpec.describe 'Posts', type: :request do
  let(:user) { create(:user) }

  it 'filters unpermitted parameters' do
    sign_in user

    post posts_path, params: {
      post: {
        title: 'Test',
        content: 'Content',
        admin_only: true  # unpermitted
      }
    }

    expect(Post.last.admin_only).to be_nil
  end
end
```

### 4. Test Route Constraints

```ruby
RSpec.describe 'Posts', type: :request do
  it 'returns 404 for invalid id format' do
    get post_path('invalid')

    expect(response).to have_http_status(:not_found)
  end

  it 'returns post for valid id' do
    post = create(:post)
    get post_path(post)

    expect(response).to have_http_status(:success)
  end
end
```

## Authentication Testing Patterns

### Session-Based (Web Routes)

```ruby
RSpec.describe 'Dashboard', type: :request do
  it 'redirects guest to login' do
    get dashboard_path

    expect(response).to have_http_status(:redirect)
    expect(response).to redirect_to(login_path)
  end

  it 'shows dashboard to authenticated user' do
    user = create(:user)
    sign_in user

    get dashboard_path

    expect(response).to have_http_status(:success)
  end
end
```

### JWT Token (API Routes)

```ruby
RSpec.describe 'API::Users', type: :request do
  let(:user) { create(:user) }

  def auth_headers(user)
    token = JWT.encode({ user_id: user.id }, Rails.application.secret_key_base)
    { 'Authorization' => "Bearer #{token}" }
  end

  it 'returns 401 without token' do
    get api_user_path(user)

    expect(response).to have_http_status(:unauthorized)
  end

  it 'returns user data with valid token' do
    get api_user_path(user), headers: auth_headers(user)

    expect(response).to have_http_status(:success)
  end
end
```

## Testing Checklist

Before testing a route:

- [ ] Identify route type (web/api)
- [ ] Determine authentication method (Devise/JWT/session)
- [ ] Check filter/middleware requirements
- [ ] Prepare test data using factories
- [ ] Write test for authenticated access
- [ ] Write test for unauthenticated access
- [ ] Test validation rules
- [ ] Test authorization
- [ ] Verify database changes
- [ ] Test different user roles/permissions

## Running Tests

```bash
# Run all tests
bundle exec rspec

# Run specific test file
bundle exec rspec spec/requests/posts_spec.rb

# Run specific test
bundle exec rspec spec/requests/posts_spec.rb:12

# Run with documentation format
bundle exec rspec --format documentation

# Run in parallel (faster)
bundle exec parallel_rspec spec/

# With coverage
COVERAGE=true bundle exec rspec
```

## Debugging Failed Tests

### 401 Unauthorized

**Possible causes**:
1. Missing authentication
2. Expired token
3. Session not started

**Solutions**:
```ruby
# Ensure sign_in is called
sign_in user
get protected_path

# For API, use proper headers
get api_path, headers: { 'Authorization' => "Bearer #{token}" }
```

### 403 Forbidden

**Possible causes**:
1. User lacks permissions
2. Authorization check failed
3. CSRF token mismatch

**Solutions**:
```ruby
# Test with correct permissions
admin = create(:user, :admin)
sign_in admin
get admin_path
```

### 404 Not Found

**Possible causes**:
1. Route not defined
2. Incorrect route path
3. Resource doesn't exist

**Solutions**:
```bash
# Check routes
rails routes | grep posts

# Check specific route
rails routes -c posts
```

### 422 Unprocessable Entity

**Expected behavior** - test it:
```ruby
it 'returns 422 for invalid data' do
  sign_in user

  post posts_path, params: { post: { title: '' } }

  expect(response).to have_http_status(:unprocessable_entity)
end
```

## Related Skills

- Use **backend-dev-guidelines** for controller/route patterns
- Use **error-tracking** for testing error handling
- Use **rails-dev** for sustainable Rails patterns

## Key Files

- `spec/requests/` - Request specs
- `spec/factories/` - FactoryBot factories
- `spec/rails_helper.rb` - RSpec configuration
- `test/integration/` - Minitest integration tests
