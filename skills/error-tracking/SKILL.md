---
name: error-tracking
description: Add Sentry error tracking and performance monitoring to your Rails project. Use this skill when adding error handling, creating new controllers, instrumenting background jobs, or tracking database performance. ALL ERRORS MUST BE CAPTURED TO SENTRY - no exceptions.
---

# Rails Sentry Integration Skill

## Purpose
This skill enforces comprehensive Sentry error tracking and performance monitoring across all Rails applications following Sentry Ruby SDK patterns.

## When to Use This Skill
- Adding error handling to any code
- Creating new controllers or routes
- Instrumenting Rake tasks and background jobs
- Tracking database performance
- Adding performance spans
- Handling application errors

## 🚨 CRITICAL RULE

**ALL ERRORS MUST BE CAPTURED TO SENTRY** - No exceptions. Never use Rails.logger.error alone without Sentry.

## Sentry Integration Patterns

### 1. Controller Error Handling

```ruby
# app/controllers/posts_controller.rb
class PostsController < ApplicationController
  def create
    @post = Post.new(post_params)

    if @post.save
      redirect_to @post
    else
      render :new, status: :unprocessable_entity
    end
  rescue StandardError => e
    # Automatically sends to Sentry with context
    Sentry.capture_exception(e)

    render json: { error: 'Internal server error' }, status: :internal_server_error
  end
end
```

### 2. Global Error Handling with Middleware

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.breadcrumbs_logger = [:active_support_logger, :http_logger]

  # Performance monitoring
  config.traces_sample_rate = 0.1
  config.profiles_sample_rate = 0.1

  # Set environment
  config.environment = Rails.env

  # Filter sensitive data
  config.send_default_pii = false

  # Set user context automatically
  config.before_send = lambda do |event, hint|
    if Current.user
      event.user = {
        id: Current.user.id,
        email: Current.user.email
      }
    end
    event
  end
end
```

### 3. Application-Wide Error Handler

```ruby
# app/controllers/application_controller.rb
class ApplicationController < ActionController::Base
  rescue_from StandardError, with: :handle_standard_error
  rescue_from ActiveRecord::RecordNotFound, with: :handle_not_found

  private

  def handle_standard_error(exception)
    Sentry.capture_exception(exception)

    respond_to do |format|
      format.html { render 'errors/500', status: :internal_server_error }
      format.json { render json: { error: 'Internal server error' }, status: :internal_server_error }
    end
  end

  def handle_not_found(exception)
    Sentry.capture_exception(exception)

    respond_to do |format|
      format.html { render 'errors/404', status: :not_found }
      format.json { render json: { error: 'Not found' }, status: :not_found }
    end
  end
end
```

### 4. Background Jobs (ActiveJob with Solid Queue)

```ruby
# app/jobs/process_data_job.rb
class ProcessDataJob < ApplicationJob
  queue_as :default

  def perform(*args)
    transaction = Sentry.start_transaction(
      name: 'ProcessDataJob',
      op: 'queue.job'
    )

    Sentry.get_current_scope.set_span(transaction)

    begin
      # Your job logic here
      process_data(args)

      transaction.set_http_status(200)
    rescue StandardError => e
      Sentry.capture_exception(e, extra: {
        job: self.class.name,
        args: args,
        queue: queue_name
      })

      transaction.set_http_status(500)
      raise # Re-raise to mark job as failed
    ensure
      transaction.finish
    end
  end
end
```

### 5. Rake Tasks

```ruby
# lib/tasks/data_processing.rake
namespace :data do
  desc 'Process data with Sentry tracking'
  task process: :environment do
    transaction = Sentry.start_transaction(
      name: 'rake:data:process',
      op: 'task'
    )

    Sentry.get_current_scope.set_span(transaction)

    begin
      puts 'Starting data processing...'
      # Your task logic here

      transaction.set_http_status(200)
      puts 'Completed successfully'
    rescue StandardError => e
      Sentry.capture_exception(e, tags: {
        task: 'data:process',
        error_type: 'execution_error'
      })

      transaction.set_http_status(500)
      puts "Error: #{e.message}"
      raise
    ensure
      transaction.finish
    end
  end
end
```

### 6. Database Performance Monitoring

```ruby
# config/initializers/sentry.rb
require 'sentry-ruby'
require 'sentry-rails'

Sentry.init do |config|
  # ... other config

  # Track slow queries
  config.rails.report_rescued_exceptions = true

  # Custom breadcrumbs for SQL queries
  ActiveSupport::Notifications.subscribe('sql.active_record') do |name, start, finish, id, payload|
    duration = ((finish - start) * 1000).round(2)

    if duration > 100 # slow query threshold in ms
      Sentry.add_breadcrumb(
        Sentry::Breadcrumb.new(
          category: 'query',
          message: payload[:sql],
          data: {
            duration: duration,
            name: payload[:name]
          },
          level: :warning
        )
      )
    end
  end
end
```

### 7. Service Objects with Sentry

```ruby
# app/services/user_registration_service.rb
class UserRegistrationService
  def initialize(user_params)
    @user_params = user_params
  end

  def call
    transaction = Sentry.start_transaction(
      name: 'UserRegistrationService',
      op: 'service'
    )

    Sentry.get_current_scope.set_span(transaction)

    begin
      User.transaction do
        user = User.create!(@user_params)
        send_welcome_email(user)
        user
      end

      transaction.set_http_status(200)
    rescue StandardError => e
      Sentry.capture_exception(e, extra: {
        service: 'UserRegistrationService',
        params: @user_params.except(:password)
      })

      transaction.set_http_status(500)
      raise
    ensure
      transaction.finish
    end
  end

  private

  def send_welcome_email(user)
    UserMailer.welcome(user).deliver_later
  end
end
```

### 8. Custom Context and Tags

```ruby
# In controllers or services
Sentry.configure_scope do |scope|
  # Set user context
  scope.set_user(
    id: current_user.id,
    email: current_user.email,
    username: current_user.username
  )

  # Set tags for filtering
  scope.set_tag('feature', 'checkout')
  scope.set_tag('payment_method', 'stripe')

  # Set custom context
  scope.set_context('order', {
    id: order.id,
    total: order.total,
    status: order.status
  })
end

# Capture exception with context
Sentry.capture_exception(exception)
```

### 9. Performance Spans

```ruby
# app/services/complex_calculation_service.rb
class ComplexCalculationService
  def call
    transaction = Sentry.get_current_scope.get_transaction
    return perform_calculation unless transaction

    span = transaction.start_child(
      op: 'calculation',
      description: 'Complex calculation'
    )

    begin
      result = perform_calculation
      span.set_http_status(200)
      result
    rescue StandardError => e
      span.set_http_status(500)
      raise
    ensure
      span.finish
    end
  end

  private

  def perform_calculation
    # Complex logic here
  end
end
```

## Error Levels

Use appropriate severity levels:

- **fatal**: System is unusable (database down, critical service failure)
- **error**: Operation failed, needs immediate attention
- **warning**: Recoverable issues, degraded performance
- **info**: Informational messages, successful operations
- **debug**: Detailed debugging information (dev only)

```ruby
Sentry.capture_message('User action completed', level: :info)
Sentry.capture_message('Slow query detected', level: :warning)
Sentry.capture_exception(error, level: :error)
```

## Required Context

```ruby
Sentry.configure_scope do |scope|
  # ALWAYS include these if available
  scope.set_user(
    id: user.id,
    email: user.email,
    username: user.username
  )

  scope.set_tag('environment', Rails.env)
  scope.set_tag('service', 'api') # or 'web', 'worker', etc.

  # Add operation-specific context
  scope.set_context('operation', {
    type: 'checkout',
    order_id: order.id,
    amount: order.total
  })
end

Sentry.capture_exception(error)
```

## Rails Configuration

### Gemfile

```ruby
# Gemfile
gem 'sentry-ruby'
gem 'sentry-rails'
gem 'solid_queue' # Background job processing
```

### Configuration File

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  config.dsn = ENV['SENTRY_DSN']
  config.breadcrumbs_logger = [:active_support_logger, :http_logger]

  # Performance Monitoring
  config.traces_sample_rate = 0.1 # 10% of transactions
  config.profiles_sample_rate = 0.1 # 10% for profiling

  # Environment
  config.environment = Rails.env
  config.enabled_environments = %w[production staging]

  # Release tracking
  config.release = ENV['APP_VERSION'] || 'unknown'

  # Don't send sensitive data
  config.send_default_pii = false

  # Filter sensitive params
  config.excluded_exceptions += ['ActionController::RoutingError']

  # Custom before_send hook
  config.before_send = lambda do |event, hint|
    # Filter sensitive data
    if event.request&.data
      event.request.data = event.request.data.except(:password, :token)
    end

    event
  end
end
```

### Environment Variables

```bash
# .env
SENTRY_DSN=your-sentry-dsn
APP_VERSION=1.0.0
```

## Installation

```bash
# Install Sentry gems
bundle add sentry-ruby sentry-rails

# Install Solid Queue for background jobs
bundle add solid_queue
rails generate solid_queue:install

# Generate Sentry initializer (optional)
rails generate sentry
```

## Testing Sentry Integration

### Test Routes

```ruby
# config/routes.rb (only in development/staging)
if Rails.env.development? || Rails.env.staging?
  namespace :sentry do
    get 'test_error', to: 'test#error'
    get 'test_message', to: 'test#message'
  end
end

# app/controllers/sentry/test_controller.rb
module Sentry
  class TestController < ApplicationController
    def error
      raise StandardError, 'Test error for Sentry'
    end

    def message
      Sentry.capture_message('Test message from Rails', level: :info)
      render json: { message: 'Message sent to Sentry' }
    end
  end
end
```

### Test Commands

```bash
# Test basic error capture
curl http://localhost:3000/sentry/test_error

# Test message capture
curl http://localhost:3000/sentry/test_message

# Test Rake task
rails data:process

# Test background job
rails runner "ProcessDataJob.perform_later"
```

## Performance Monitoring

### Requirements

1. **All API endpoints** - Automatic transaction tracking
2. **Database queries > 100ms** - Automatically flagged
3. **N+1 queries** - Detected via Bullet gem integration
4. **Background jobs** - Must track execution time

### Transaction Tracking

```ruby
# Automatic for controllers via sentry-rails

# Manual transaction for custom operations
transaction = Sentry.start_transaction(
  name: 'custom_operation',
  op: 'operation'
)

Sentry.get_current_scope.set_span(transaction)

begin
  # Your operation
  perform_operation
ensure
  transaction.finish
end
```

### Integration with Bullet (N+1 detection)

```ruby
# config/environments/development.rb
config.after_initialize do
  Bullet.enable = true
  Bullet.sentry = true # Send N+1 queries to Sentry
  Bullet.alert = true
  Bullet.rails_logger = true
end
```

## Common Mistakes to Avoid

❌ **NEVER** use Rails.logger.error without Sentry
❌ **NEVER** swallow errors silently
❌ **NEVER** expose sensitive data in error context
❌ **NEVER** use generic error messages without context
❌ **NEVER** skip error handling in async operations
❌ **NEVER** forget to re-raise in background jobs

## Implementation Checklist

When adding Sentry to new code:

- [ ] Installed sentry-ruby and sentry-rails gems
- [ ] Configured config/initializers/sentry.rb
- [ ] All rescue blocks capture to Sentry
- [ ] Added meaningful context to errors
- [ ] Used appropriate error level
- [ ] No sensitive data in error messages
- [ ] Added performance tracking for slow operations
- [ ] Tested error handling paths
- [ ] For Jobs: re-raise after capturing
- [ ] For Rake tasks: wrapped in transaction

## Solid Queue Integration

```ruby
# config/initializers/sentry.rb
Sentry.init do |config|
  # ... other config
end

# ActiveJob with Solid Queue automatically works with Sentry
# All exceptions in jobs are captured automatically

# For more control and context:
class MyJob < ApplicationJob
  queue_as :default

  def perform(*args)
    # Job logic
  rescue StandardError => e
    Sentry.capture_exception(e, extra: {
      args: args,
      queue: queue_name,
      job_id: job_id
    })
    raise # Re-raise to mark job as failed
  end
end
```

### Solid Queue Configuration

```ruby
# config/queue.yml
production:
  dispatchers:
    - polling_interval: 1
      batch_size: 500
  workers:
    - queues: "*"
      threads: 3
      processes: 5
      polling_interval: 0.1
```

## Key Files

### Rails Application
- `config/initializers/sentry.rb` - Sentry configuration
- `app/controllers/application_controller.rb` - Global error handling
- `app/jobs/` - Background job error tracking
- `lib/tasks/` - Rake task instrumentation

### Configuration
- `.env` - Environment-specific configuration
- `Gemfile` - Sentry gem dependencies

## Documentation

- Official Sentry Rails: https://docs.sentry.io/platforms/ruby/guides/rails/
- Performance monitoring: https://docs.sentry.io/platforms/ruby/guides/rails/performance/
- Solid Queue: https://github.com/rails/solid_queue

## Related Skills

- Use **backend-dev-guidelines** for Rails patterns
- Use **route-tester** for testing error handling
- Use **rails-dev** for sustainable Rails development
