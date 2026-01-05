# Inertia.js Rails Patterns

Complete guide for using Inertia.js with Rails on the server-side.

## Installation & Setup

### 1. Install the Gem

```bash
bundle add inertia_rails
```

### 2. Run the Generator

```bash
bin/rails generate inertia:install
```

This automatically:
- Sets up Vite Rails integration
- Configures TypeScript (optional)
- Installs your chosen frontend framework (React/Vue/Svelte)
- Sets up Tailwind CSS (optional)
- Creates example controller and routes

### 3. Configure Root Template

```erb
<!-- app/views/layouts/application.html.erb -->
<!DOCTYPE html>
<html>
  <head>
    <title>My App</title>
    <%= csrf_meta_tags %>
    <%= csp_meta_tag %>

    <%= inertia_ssr_head %>
    <%= vite_client_tag %>
    <%= vite_javascript_tag 'application' %>
  </head>
  <body>
    <%= yield %>
  </body>
</html>
```

### 4. Configure Inertia (Optional)

```ruby
# config/initializers/inertia_rails.rb
InertiaRails.configure do |config|
  # Custom layout
  config.layout = 'my_inertia_layout'

  # Enable deep merging of shared data
  config.deep_merge_shared_data = true

  # SSR configuration
  config.ssr_enabled = Rails.env.production?
  config.ssr_url = 'http://localhost:13714'
end
```

---

## Rendering Inertia Responses

### Basic Pattern

```ruby
class EventsController < ApplicationController
  def show
    event = Event.find(params[:id])

    # Renders app/frontend/pages/events/show.(jsx|vue|svelte)
    render inertia: { event: }
  end
end
```

### Custom Component Name

```ruby
class EventsController < ApplicationController
  def my_event
    event = Event.find(params[:id])

    render inertia: 'events/show', props: {
      event: event.as_json(only: [:id, :title, :start_date, :description])
    }
  end
end
```

### Using Instance Variables as Props

```ruby
class EventsController < ApplicationController
  use_inertia_instance_props

  def index
    @events = Event.all
    # @events automatically becomes the 'events' prop
    render inertia: 'events/index'
  end
end
```

### View Data (Non-Prop Data)

Pass data to ERB template without sending to JavaScript:

```ruby
def show
  event = Event.find(params[:id])

  render inertia: { event: }, view_data: {
    meta_description: event.description,
    og_image: event.image_url
  }
end
```

Access in layout:

```erb
<meta name="description" content="<%= local_assigns.fetch(:meta_description, 'Default') %>">
```

---

## Shared Data

### Global Shared Data

```ruby
class ApplicationController < ActionController::Base
  # Static data
  inertia_share app_name: Rails.configuration.app_name

  # Dynamic data with block
  inertia_share do
    {
      user: current_user&.as_json(only: [:id, :name, :email]),
      notifications_count: current_user&.unread_notifications_count
    } if user_signed_in?
  end

  # Lambda syntax
  inertia_share total_users: -> { User.count }
end
```

### Controller-Specific Shared Data

```ruby
class DashboardController < ApplicationController
  # Only share on dashboard
  inertia_share stats: -> {
    {
      total_orders: Order.count,
      revenue: Order.sum(:total)
    }
  }
end
```

### Conditional Sharing

```ruby
class ApplicationController < ActionController::Base
  # Share only when authenticated
  inertia_share if: :user_signed_in? do
    {
      auth: {
        user: current_user.as_json(only: [:id, :name, :email, :avatar_url])
      }
    }
  end

  # Share only on specific actions
  inertia_share only: [:index, :show] do
    { meta: { version: '1.0', last_updated: Time.current } }
  end

  # Supported options: only, except, if, unless
end
```

### Share Once (Cached Across Navigation)

```ruby
class ApplicationController < ActionController::Base
  # Resolved once and remembered
  inertia_share countries: InertiaRails.once { Country.all }
end
```

### Deep Merging

```ruby
# Override partial shared data structures
render inertia: {
  user: { role: 'admin' }
}, deep_merge: true

# Or enable globally
InertiaRails.configure do |config|
  config.deep_merge_shared_data = true
end
```

---

## Redirects

### Standard Redirects

```ruby
class UsersController < ApplicationController
  def create
    user = User.new(user_params)

    if user.save
      # Automatically uses 303 status for non-GET redirects
      redirect_to users_url, notice: 'User created successfully'
    else
      # Pass validation errors back
      redirect_to new_user_url, inertia: { errors: user.errors }
    end
  end
end
```

**Important:** Inertia Rails automatically converts redirects to `303` status after PUT/PATCH/DELETE to ensure the next request is GET.

### External Redirects

```ruby
def redirect_external
  # Forces a full page reload (409 Conflict response)
  inertia_location 'https://external-site.com'
end
```

### Flash Messages

```ruby
def create
  if resource.save
    redirect_to resource_path, notice: 'Success!'
  else
    redirect_to new_resource_path, alert: 'Error occurred'
  end
end

# Access in shared data
inertia_share flash: -> { flash.to_hash }
```

---

## Validation & Error Handling

### Return Validation Errors

```ruby
class PostsController < ApplicationController
  def create
    @post = Post.new(post_params)

    if @post.save
      redirect_to posts_path, notice: 'Post created'
    else
      # Redirect back with errors
      redirect_to new_post_path, inertia: {
        errors: @post.errors.messages
      }
    end
  end

  def update
    @post = Post.find(params[:id])

    if @post.update(post_params)
      redirect_to @post, notice: 'Post updated'
    else
      redirect_to edit_post_path(@post), inertia: {
        errors: @post.errors.messages
      }
    end
  end

  private

  def post_params
    params.require(:post).permit(:title, :content)
  end
end
```

### Error Bags (Multiple Forms)

```ruby
def create_company
  company = Company.new(company_params)

  unless company.save
    redirect_to new_company_path, inertia: {
      errors: company.errors.messages,
      errorBag: 'createCompany'
    }
  end
end

def create_user
  user = User.new(user_params)

  unless user.save
    redirect_to new_user_path, inertia: {
      errors: user.errors.messages,
      errorBag: 'createUser'
    }
  end
end
```

---

## Request Detection

### Check if Inertia Request

```ruby
def some_action
  if request.inertia?
    # Handle Inertia request
    render inertia: { data: 'value' }
  else
    # Handle regular request
    render html: '<h1>Hello</h1>'
  end
end
```

### Check Partial Reload

```ruby
def index
  if request.inertia_partial?
    # Only loading partial data
    render inertia: { limited_data: true }
  else
    # Full page load
    render inertia: { all_data: true }
  end
end
```

### Mixed Response Types

```ruby
def show
  @resource = Resource.find(params[:id])

  respond_to do |format|
    format.html { render inertia: { resource: @resource } }
    format.json { render json: @resource }
  end
end
```

---

## Advanced Patterns

### Lazy Evaluation Props

```ruby
def index
  render inertia: {
    posts: Post.all,
    # Only loaded when requested
    stats: InertiaRails.lazy do
      {
        total: Post.count,
        published: Post.published.count
      }
    end
  }
end
```

### Partial Reloads

```ruby
# Client requests only specific props
# Server automatically filters based on X-Inertia-Partial-Data header

def show
  render inertia: {
    user: current_user,
    posts: Post.all,
    stats: expensive_calculation  # Only sent if requested
  }
end
```

### Custom Serialization

```ruby
class EventsController < ApplicationController
  def show
    event = Event.find(params[:id])

    render inertia: {
      event: EventSerializer.new(event).as_json
    }
  end
end

# Or use as_json with options
def index
  render inertia: {
    events: Event.includes(:organizer).map { |e|
      e.as_json(
        only: [:id, :title, :start_date],
        include: {
          organizer: { only: [:id, :name] }
        }
      )
    }
  }
end
```

---

## Best Practices

### 1. Always Use Strong Parameters

```ruby
def create
  resource = Resource.new(resource_params)
  # ...
end

private

def resource_params
  params.require(:resource).permit(:name, :description)
end
```

### 2. Serialize Carefully

```ruby
# ❌ BAD: Sends entire AR object (includes timestamps, internal fields)
render inertia: { user: User.first }

# ✅ GOOD: Explicit serialization
render inertia: {
  user: User.first.as_json(only: [:id, :name, :email])
}
```

### 3. Use Shared Data for Global State

```ruby
# ✅ GOOD: Auth in shared data
inertia_share auth: -> { { user: current_user } }

# ❌ BAD: Passing auth on every action
def index
  render inertia: { posts: Post.all, auth: current_user }
end
```

### 4. Handle Validation Properly

```ruby
# ✅ GOOD: Redirect with errors
if resource.save
  redirect_to resource_path
else
  redirect_to new_resource_path, inertia: { errors: resource.errors }
end

# ❌ BAD: Rendering 422 (breaks Inertia flow)
if resource.save
  redirect_to resource_path
else
  render json: { errors: resource.errors }, status: :unprocessable_entity
end
```

---

## Common Patterns

### Index/List Page

```ruby
def index
  @posts = Post.includes(:author)
                .page(params[:page])
                .per(10)

  render inertia: {
    posts: @posts.map { |p|
      p.as_json(
        only: [:id, :title, :created_at],
        include: { author: { only: [:id, :name] } }
      )
    },
    pagination: {
      current_page: @posts.current_page,
      total_pages: @posts.total_pages,
      total_count: @posts.total_count
    }
  }
end
```

### Show/Detail Page

```ruby
def show
  @post = Post.includes(:author, :comments).find(params[:id])

  render inertia: {
    post: @post.as_json(
      only: [:id, :title, :content, :created_at],
      include: {
        author: { only: [:id, :name, :avatar_url] },
        comments: {
          only: [:id, :body, :created_at],
          include: { author: { only: [:id, :name] } }
        }
      }
    )
  }
end
```

### Create Form

```ruby
def new
  render inertia: {
    post: Post.new,
    categories: Category.all.as_json(only: [:id, :name])
  }
end

def create
  @post = Post.new(post_params)

  if @post.save
    redirect_to posts_path, notice: 'Post created'
  else
    redirect_to new_post_path, inertia: {
      errors: @post.errors.messages,
      post: @post.as_json
    }
  end
end
```

### Edit Form

```ruby
def edit
  @post = Post.find(params[:id])

  render inertia: {
    post: @post.as_json(only: [:id, :title, :content, :category_id]),
    categories: Category.all.as_json(only: [:id, :name])
  }
end

def update
  @post = Post.find(params[:id])

  if @post.update(post_params)
    redirect_to @post, notice: 'Post updated'
  else
    redirect_to edit_post_path(@post), inertia: {
      errors: @post.errors.messages
    }
  end
end
```

---

## Reference

- Official Docs: https://inertia-rails.dev/guide
- GitHub: https://github.com/inertiajs/inertia-rails
- React Adapter: https://inertiajs.com/client-side-setup
