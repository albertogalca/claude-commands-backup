---
name: rails-development
description: Write sustainable Rails code following battle-tested patterns for long-term maintainability. Use when building Rails applications, designing routes, organizing business logic, creating views, writing tests, or discussing Rails architecture. Emphasizes sustainability over cleverness, consistency over novelty.
---

# Sustainable Rails Development

Write Rails code optimized for long-term maintainability, not short-term convenience.

## Core Philosophy

- **Sustainability** = ability to sustain development velocity over years
- Minimize carrying costs (ongoing maintenance burden)
- Strategically incur opportunity costs (accept constraints for stability)
- Consistency and quality are foundational values
- Automation over documentation

## Architecture Guidelines

### 1. Business Logic Placement

**Never put business logic in Active Records.** Active Records have high fan-in (used everywhere). Bugs in high fan-in classes cause system-wide problems.

```ruby
# BAD - logic in Active Record
class Order < ApplicationRecord
  def complete!
    update!(status: "complete")
    InventoryService.decrement(line_items)
    OrderMailer.confirmation(self).deliver_later
  end
end

# GOOD - isolated service object
class CompleteOrder
  def initialize(order)
    @order = order
  end

  def call
    @order.update!(status: "complete")
    InventoryService.decrement(@order.line_items)
    OrderMailer.confirmation(@order).deliver_later
  end
end
```

Create service objects for each business concept. Keep Active Records focused on database access only.

### 2. Route Design

Always use canonical routes conforming to Rails defaults:

```ruby
# GOOD - explicit, minimal routes
resources :orders, only: [:index, :show, :create]
resources :users, only: [:show, :edit, :update]

# BAD - implicit routes you don't need
resources :orders  # Creates 7 routes, you probably don't need all of them
```

**Route principles:**
- Use `resources` with `only:` parameter always
- Never configure unused routes
- Avoid custom actions—create new resources instead
- Vanity URLs redirect to canonical routes
- Nest routes max 1 level deep

```ruby
# Instead of custom action
resources :orders do
  post :cancel, on: :member  # BAD
end

# Create a new resource
resources :orders, only: [:show]
resources :order_cancellations, only: [:create]  # GOOD
```

### 3. Controller Structure

One instance variable per action, named after the resource:

```ruby
class OrdersController < ApplicationController
  def show
    @order = Order.find(params[:id])
  end

  def index
    @orders = current_user.orders.recent
  end
end
```

Exceptions allowed: reference data, global context, UI state flags.

### 4. View Layer

**HTML templates:**
- Use semantic HTML for content and controls
- Use `<div>` and `<span>` only for styling hooks
- Just use ERB (avoid HAML/Slim—they solve non-problems)
- Use partials with strict `locals:` for simple re-use

```erb
<%# GOOD - semantic HTML %>
<article>
  <h1><%= @post.title %></h1>
  <p><%= @post.body %></p>
</article>

<%# Partial with explicit locals %>
<%= render "order_row", order: order, show_actions: true %>
```

**View Components** for complex UI requiring logic and testing:

```ruby
class AlertComponent < ViewComponent::Base
  def initialize(type:, message:)
    @type = type
    @message = message
  end

  def css_class
    case @type
    when :error then "alert-danger"
    when :success then "alert-success"
    else "alert-info"
    end
  end
end
```

### 5. Helpers

Best for: global UI state, generating inline markup. Use Rails APIs (`content_tag`) to avoid security issues.

```ruby
# GOOD - simple markup generation
def status_badge(status)
  content_tag :span, status.humanize, class: "badge badge-#{status}"
end

# BAD - domain logic in helper
def order_total_with_discount(order)
  # This belongs in a service or model
end
```

Consolidate helpers in `application_helper.rb` unless you have a clear modular strategy.

### 6. CSS Strategy

Adopt a design system with defined: font sizes, spacing scale, color palette.

**Functional CSS (Tailwind) is highly sustainable:**
- HTML templates become the unit of re-use
- No dead CSS accumulation
- Changes are local to the template

```erb
<button class="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700">
  Submit
</button>
```

### 7. JavaScript Approach

**JavaScript is a liability.** Prefer server-rendered views by default.

```ruby
# config/initializers/turbo.rb
# Reduce perceived latency
Turbo.config.drive.progress_bar_delay = 100  # Default 500ms is too long
```

**When JavaScript is needed:**
- Use Hotwire (Turbo + Stimulus) for interactivity
- Custom elements for basic interactions
- Choose at most one framework, choose for longevity
- Ensure system tests break when JavaScript breaks

## Model & Database

### Active Record Responsibilities

Active Record is for **database access only**:
- Associations
- Scopes for common queries
- Validations (for UX, not data integrity)

```ruby
class Order < ApplicationRecord
  belongs_to :user
  has_many :line_items

  scope :recent, -> { order(created_at: :desc).limit(10) }
  scope :pending, -> { where(status: "pending") }

  validates :email, presence: true  # UX feedback
end
```

### Database Constraints

**The database enforces correctness, not Rails:**

```ruby
# Migration
add_column :orders, :total_cents, :integer, null: false
add_index :orders, :email, unique: true
add_foreign_key :line_items, :orders
```

Use `structure.sql` (SQL schema), not `schema.rb`.

### Minimize Callbacks

Callbacks create hidden coupling. Prefer explicit service objects.

```ruby
# BAD - hidden side effect
after_create :send_welcome_email

# GOOD - explicit in service
class CreateUser
  def call(params)
    user = User.create!(params)
    UserMailer.welcome(user).deliver_later
    user
  end
end
```

## Testing Strategy

### Test Pyramid

1. **System tests** - User flows, integration points
2. **Unit tests** - Business logic (service objects)
3. **Model tests** - Database constraints, scopes

```ruby
# System test for user flow
class CheckoutFlowTest < ApplicationSystemTestCase
  test "user can complete checkout" do
    visit products_path
    click_on "Add to Cart"
    click_on "Checkout"
    fill_in "Email", with: "test@example.com"
    click_on "Place Order"
    assert_text "Order confirmed"
  end
end

# Unit test for business logic
class CompleteOrderTest < ActiveSupport::TestCase
  test "marks order complete and sends confirmation" do
    order = orders(:pending)
    CompleteOrder.new(order).call
    assert_equal "complete", order.reload.status
  end
end
```

Use Factory Bot for valid model instances. Test database constraints explicitly.

## Project Setup

### Environment Configuration

```ruby
# Use UNIX environment for all runtime config
# config/database.yml
production:
  url: <%= ENV["DATABASE_URL"] %>

# .env for development (via dotenv gem)
DATABASE_URL=postgres://localhost/myapp_dev
REDIS_URL=redis://localhost:6379
```

### Essential Scripts

```bash
# bin/setup - Idempotent setup
#!/bin/bash
set -e
bundle install
bin/rails db:prepare
yarn install

# bin/dev - Local development
#!/bin/bash
foreman start -f Procfile.dev

# bin/ci - Quality checks
#!/bin/bash
set -e
bundle exec rubocop
bundle exec brakeman -q
bundle exec rails test
bundle exec rails test:system
```

### Production Logging

```ruby
# Gemfile
gem "lograge"

# config/environments/production.rb
config.lograge.enabled = true
```

## Best Practices

### DO:
- Keep Active Records focused on persistence
- Use service objects for business logic
- Define explicit, minimal routes
- Write semantic HTML
- Let the database enforce correctness
- Test user flows with system tests
- Automate setup and CI

### DON'T:
- Put business logic in models or controllers
- Use `resources` without `only:`
- Create custom route actions
- Use callbacks for business logic
- Trust validations for data integrity
- Write JavaScript when Turbo suffices
- Skip database constraints

## Summary

Write Rails code for the developer who inherits it in 3 years. Sustainability comes from consistency, explicit code paths, and letting Rails conventions work for you. The framework is mature—trust its patterns, but keep business logic in dedicated service objects where it can be tested and understood in isolation.
