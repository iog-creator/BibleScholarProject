# Templates

This directory contains HTML templates for the STEPBible Explorer web application.

## Templates Overview

- **Layout Templates**
  - `base.html`: Base template with common layout elements (header, footer, navigation)
  - `error.html`: Error page template

- **Home and Search**
  - `index.html`: Home page template with feature overview and statistics
  - `search.html`: Search interface template with multiple search types

- **Lexicon Templates**
  - `lexicon_entry.html`: Lexicon entry detail template
  - `lexicon_search.html`: Specialized lexicon search interface

- **Bible Text Templates**
  - `verse_detail.html`: Bible verse detail template with tagged words
  - `verse_with_resources.html`: Verse display with external resources
  - `concordance.html`: Concordance display for word occurrences
  - `cross_references.html`: Cross-references display

- **Morphology Templates**
  - `morphology_detail.html`: Morphology code explanation template
  - `morphology_search.html`: Search interface for morphology codes

- **Proper Names Templates**
  - `names_home.html`: Proper names search interface
  - `name_detail.html`: Proper name detail template
  - `name_search_results.html`: Results list for name searches

- **Arabic Bible Templates**
  - `arabic_bible_home.html`: Arabic Bible interface
  - `arabic_verse.html`: Arabic verse detail template
  - `arabic_parallel.html`: Parallel view of Arabic with other translations

## Template Structure

The templates use Flask's Jinja2 templating engine with a base template that defines common elements:

```
base.html
├── index.html
├── search.html
├── lexicon_entry.html
│   └── lexicon_search.html
├── verse_detail.html
│   ├── concordance.html
│   ├── cross_references.html
│   └── verse_with_resources.html
├── names_home.html
│   ├── name_detail.html
│   └── name_search_results.html
└── arabic_bible_home.html
    ├── arabic_verse.html
    └── arabic_parallel.html
```

## Template Blocks

Key template blocks defined in `base.html`:

- `{% block title %}{% endblock %}`: Page title
- `{% block head %}{% endblock %}`: Additional head elements
- `{% block styles %}{% endblock %}`: Page-specific styles
- `{% block content %}{% endblock %}`: Main page content
- `{% block scripts %}{% endblock %}`: Page-specific scripts

## Styling

The templates use a combination of:

- **Bootstrap 5**: Core styling framework
- **Custom CSS**: Additional styling in `static/css/style.css`
- **Responsive design**: Mobile-first approach for all templates
- **RTL support**: Right-to-left text support for Hebrew and Arabic

## JavaScript

JavaScript functionality includes:

- **Interactive elements**: Dropdowns, toggles, and interactive UI elements
- **AJAX requests**: Asynchronous loading of data for better performance
- **Word highlighting**: Highlighting words on mouseover
- **Export functionality**: Export data to CSV or other formats

## Best Practices

When modifying templates:

1. **Extend base.html**: Always extend the base template
2. **Use block structure**: Place content in appropriate blocks
3. **Maintain responsive design**: Test all changes on mobile devices
4. **Follow naming conventions**: Use consistent naming for templates and blocks
5. **Comment complex sections**: Add comments for complex template logic
6. **Escape user input**: Always use `{{ variable|escape }}` for user-provided content
7. **Minimize duplicate code**: Use includes for repeated elements
8. **Optimize performance**: Minimize DOM manipulations and large data transfers

## Accessibility

The templates are designed with accessibility in mind:

- Semantic HTML5 elements
- ARIA attributes for interactive elements
- Keyboard navigation support
- Sufficient color contrast
- Text alternatives for non-text content

## Testing

Templates should be tested:

1. Across different browsers (Chrome, Firefox, Safari, Edge)
2. On mobile and desktop devices
3. With different text sizes and zoom levels
4. With screen readers for accessibility 