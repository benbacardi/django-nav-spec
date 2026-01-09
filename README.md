# Django Nav Spec

Define your site’s navigation in settings, and simplify your templates. 

## Rationale

A site’s navigation can be complex, and can lead to unwieldy templates full of repetitive and lengthy `if` conditionals to determine whether a particular navigation item should be displayed for the current user, or complicated logic to figure out which link is active for the current request. Add in dropdown menus where you only want the main dropdown to be visible if any of its children are, and your navigation bar template can quickly get out of hand. 

`django-nav-spec` aims to simplify this, by defining your navigation in a single central place, and giving you the tools you need to easily mark a navigation item as active or remove it entirely based on the current request. Your template context receives a single object containing everything it needs to know to iterate and render your site’s navigation. 

## Features

*   Define navigation structures in your `settings.py`.
*   Supports single or multiple navigation menus.
*   Automatic active state detection based on URL names or custom logic.
*   Conditionally display navigation items based on user permissions or other request attributes.
*   Supports nested navigation structures.
*   Two usage modes: context processor (automatic) or template tag (on-demand).

## Quick Start

Install `django-nav-spec` however you normally would:

```bash
pip install django-nav-spec
poetry add django-nav-spec
uv add django-nav-spec
```

Import `NavigationItem` in your settings and define your navigation as a list of items in the `NAV_SPEC` setting:

```python
from nav_spec import NavigationItem

NAV_SPEC = [
    NavigationItem(title="Home", link="/", active_urls=["home"]),
    NavigationItem(title="About", link="/about/", active_urls=["about"]),
    NavigationItem(
        title="Admin",
        link="/admin/",
        displayed=lambda r: r.user.is_staff
    ),
]
```

Then choose one of two ways to use it in your templates:

### Option 1: Context Processor (automatic)

Add the context processor to your project's settings:

```python
TEMPLATES = [
    {
        ...
        'OPTIONS': {
            'context_processors': [
                ...
                'nav_spec.context_processors.nav_spec',
                ...
            ],
        },
    },
]
```

The navigation will automatically be available as `NAV_SPEC` in all templates:

```django
<nav>
  <ul>
    {% for item in NAV_SPEC %}
    <li class="{% if item.is_active %}active{% endif %}">
      <a href="{{ item.link }}">{{ item.title }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>
```

### Option 2: Template Tag (on-demand)

Add `nav_spec` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'nav_spec',
]
```

Load the template tag and call it where needed:

```django
{% load nav_spec %}
{% get_nav_spec as nav %}

<nav>
  <ul>
    {% for item in nav %}
    <li class="{% if item.is_active %}active{% endif %}">
      <a href="{{ item.link }}">{{ item.title }}</a>
    </li>
    {% endfor %}
  </ul>
</nav>
```

**When to use which approach:**
- **Context Processor**: Best when navigation is needed on every page. Processed automatically for all templates.
- **Template Tag**: Best for selective use. Only processed when explicitly called, which can improve performance if navigation isn't needed everywhere.

This example may not look like it's saved you much, but the power comes as you add more items, hierarchy, or permissions. Read below for all the available options. 

## `NavigationItem` options

For each `NavigationItem`, ensure you set both its `title` and `link` for you to pull out in the template. In the examples above, the links are hard-coded URLs, but they could also be a reversed URL using `django.urls.reverse_lazy`:

```python
from django.urls import reverse_lazy

NavigationItem(
    title="Blog",
    link=reverse_lazy("blog-index"),
)
```

> **Note:** you must use `reverse_lazy` instead of `reverse`, as settings are evaluated before any URLs and `reverse` will fail. 

### Defining a `NavigationItem`’s active state

You can pass a list of URL pattern names to mark the item as active when any of the patterns are a match for the current URL:

```python
NavigationItem(
    title="Blog",
    link="/blog/",
    active_urls=[
        "blog-index",
        "blog-post",
    ],
)
```

Or pass a function that takes a `request` object and returns True if the current item should be marked as active:

```python
NavigationItem(
    title="Blog",
    link="/blog/",
    is_active=lambda request: True
)
```

In either case, the resulting `NavigationItem` object available in the template context will have a `is_active` property the template can use to toggle the item’s active state in the HTML/CSS.  

### Controlling whether a `NavigationItem` is displayed

You can control whether a navigation item appears in the final structure sent to the template with the `displayed` property. This can either be a string, which is used as a permission check:

```python
NavigationItem(
    title="Comments",
    link="/comments/",
    displayed="blog.can_moderate_comments",
)
```

Or a callable that takes the `request` object and returns `True` if the item should be displayed:

```python
NavigationItem(
    title="Admin",
    link="/admin/",
    displayed=lambda r: r.user.is_staff
)
```

### Nested Navigation

To create nested navigation, use the `children` attribute:

```python
# settings.py
NAV_SPEC = [
    NavigationItem(
        title="Products",
        children=[
            NavigationItem(title="Product A", link="/products/a/"),
            NavigationItem(title="Product B", link="/products/b/"),
        ]
    ),
]
```

A parent item will be considered active if any of its children are active. A parent item will be displayed if any of its children are displayed, or if it has its own `displayed` attribute that evaluates to True.

You can then render the nested navigation in your template:

```html
<ul>
    {% for item in NAV_SPEC %}
    <li class="{% if item.is_active %}active{% endif %}">
        {% if item.link %}<a href="{{ item.link }}">{{ item.title }}</a>{% else %}{{ item.title }}{% endif %}
        {% if item.children %}
        <ul>
            {% for child in item.children %}
            <li class="{% if child.is_active %}active{% endif %}">
                <a href="{{ child.link }}">{{ child.title }}</a>
            </li>
            {% endfor %}
        </ul>
        {% endif %}
    </li>
    {% endfor %}
</ul>
```

## Multiple Navigation Menus

You can define multiple navigation menus by setting `NAV_SPEC` to a dictionary:

```python
# settings.py
NAV_SPEC = {
    "main_nav": [
        NavigationItem(title="Home", link="/", active_urls=["home"]),
    ],
    "footer_nav": [
        NavigationItem(title="Terms", link="/terms/", active_urls=["terms"]),
    ],
}
```

Then, in your template, you can access each menu as required:

**With context processor:**
```html
<ul>
    {% for item in NAV_SPEC.main_nav %}
    ...
    {% endfor %}
</ul>
```

**With template tag:**
```django
{% load nav_spec %}
{# Get a specific menu #}
{% get_nav_spec "main_nav" as main_nav %}
<ul>
    {% for item in main_nav %}
    ...
    {% endfor %}
</ul>

{# Or get all menus #}
{% get_nav_spec as all_nav %}
<ul>
    {% for item in all_nav.footer_nav %}
    ...
    {% endfor %}
</ul>
```

## Customizing the Context Variable Name

**Note:** This only applies when using the context processor.

By default, the navigation is available in templates as `NAV_SPEC`. You can customize this by setting `NAV_SPEC_CONTEXT_VAR_NAME`:

```python
# settings.py
NAV_SPEC_CONTEXT_VAR_NAME = 'navigation'
```

Then use the custom name in your templates:

```django
{% for item in navigation %}
    ...
{% endfor %}
```

When using the template tag, you control the variable name directly in the template with the `as` clause.

## Development

```bash
uv sync
uv run pytest
```

## Requirements

- Python 3.10+
- Django 4.2+

## License

MIT
