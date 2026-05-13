# Code Style Guidelines

## Python (Django Backend)

### General Rules
- Use Python 3.11+ features
- Follow PEP 8 style guide
- Use type hints where appropriate
- Maximum line length: 120 characters
- Use double quotes for strings

### Django Conventions
- Models: Use singular names (e.g., `ReversalZone`, not `ReversalZones`)
- Views: Use function-based views with `@api_view` decorator
- Serializers: Keep in separate `serializers.py` files
- URL patterns: Use descriptive names with hyphens

### File Organization
```
app_name/
├── __init__.py
├── models.py          # Database models
├── serializers.py     # DRF serializers
├── views.py           # API endpoints
├── tasks.py           # Celery tasks
├── consumers.py       # WebSocket consumers
├── urls.py            # URL routing
└── tests.py           # Unit tests
```

### Naming Conventions
- Functions: `snake_case`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Private methods: `_leading_underscore`

### Logging
```python
import logging
logger = logging.getLogger(__name__)

# Use emoji prefixes for visibility
logger.info("✅ Success message")
logger.warning("⚠️ Warning message")
logger.error("❌ Error message")
```

## TypeScript (Next.js Frontend)

### General Rules
- Use TypeScript strict mode
- Prefer `const` over `let`, never use `var`
- Use arrow functions for components
- Maximum line length: 100 characters
- Use single quotes for strings

### React/Next.js Conventions
- Use functional components with hooks
- Use `'use client'` directive for client components
- Keep components in `components/` directory
- Use `lib/` for utilities and contexts

### File Organization
```
app/
├── page.tsx           # Route pages
├── layout.tsx         # Layouts
└── api/              # API routes

components/
├── Navigation.tsx     # Reusable components
└── ChartComponent.tsx

lib/
├── config.ts         # Configuration
├── AuthContext.tsx   # React contexts
└── utils.ts          # Utility functions
```

### Naming Conventions
- Components: `PascalCase.tsx`
- Utilities: `camelCase.ts`
- Constants: `UPPER_SNAKE_CASE`
- Hooks: `use` prefix (e.g., `useAuth`)

### State Management
- Use React Context for global state
- Use `useState` for local state
- Use `useEffect` for side effects
- Use `useCallback` for memoized functions

## CSS/TailwindCSS

### Conventions
- Use Tailwind utility classes
- Custom colors defined in `tailwind.config.ts`
- Responsive design: mobile-first approach
- Dark theme by default

### Color Palette
- Background: `bg-[#0a0e1a]`, `bg-[#0f1419]`
- Primary: `cyan-500`, `blue-600`
- Success: `emerald-400`
- Error: `rose-400`
- Text: `white`, `slate-300`, `slate-400`

## Git Commit Messages

### Format
```
<type>: <subject>

<body (optional)>
```

### Types
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Adding tests
- `chore`: Maintenance tasks

### Examples
```
feat: Add WebSocket fallback to REST API for stale prices
fix: Use correct token name (access_token) for authentication
docs: Update API documentation for signal endpoints
```

## Error Handling

### Backend
```python
try:
    # Operation
    pass
except SpecificException as e:
    logger.error(f"❌ Error: {e}", exc_info=True)
    return Response({'error': str(e)}, status=500)
```

### Frontend
```typescript
try {
  // Operation
} catch (error) {
  console.error('Error:', error);
  // Show user-friendly message
}
```

## Security Best Practices
1. Never commit `.env` files
2. Use environment variables for secrets
3. Validate all user inputs
4. Use HTTPS in production
5. Implement CORS properly
6. Use parameterized queries (Django ORM handles this)
