  # Code Review Guidelines

## Review Checklist

### General
- [ ] Code follows project style guidelines
- [ ] No hardcoded credentials or secrets
- [ ] Environment variables used for configuration
- [ ] Error handling implemented
- [ ] Logging added for important operations
- [ ] Comments explain complex logic
- [ ] No debugging code (console.log, print statements)

### Backend (Django)
- [ ] Models have proper indexes
- [ ] Queries are optimized (no N+1 problems)
- [ ] Serializers validate input data
- [ ] Views use proper permissions
- [ ] API responses follow standard format
- [ ] Migrations are reversible
- [ ] Celery tasks are idempotent
- [ ] WebSocket consumers handle disconnections

### Frontend (Next.js)
- [ ] Components are properly typed
- [ ] No prop drilling (use Context if needed)
- [ ] Loading states implemented
- [ ] Error boundaries in place
- [ ] Accessibility attributes added
- [ ] Responsive design tested
- [ ] WebSocket cleanup on unmount
- [ ] API calls have error handling

### Security
- [ ] User input is validated
- [ ] SQL injection prevented (use ORM)
- [ ] XSS prevented (React escapes by default)
- [ ] CSRF protection enabled
- [ ] Authentication required for protected routes
- [ ] Sensitive data not logged
- [ ] HTTPS used in production

### Performance
- [ ] Database queries use select_related/prefetch_related
- [ ] API responses are cached where appropriate
- [ ] Large lists are paginated
- [ ] Images are optimized
- [ ] Bundle size is reasonable
- [ ] No unnecessary re-renders

## Code Review Process

### Before Submitting PR
```bash
# Run linters
npm run lint
python manage.py check

# Run tests
npm test
python manage.py test

# Check for TypeScript errors
npm run type-check

# Build to verify no errors
npm run build
```

### Review Commands
```bash
# View changes
git diff main

# View commit history
git log --oneline -10

# Check file changes
git diff --stat main
```

### Common Issues to Look For

#### Backend
```python
# BAD: N+1 query problem
for user in User.objects.all():
    print(user.profile.phone)  # Queries database each time

# GOOD: Use select_related
for user in User.objects.select_related('profile').all():
    print(user.profile.phone)  # Single query

# BAD: Hardcoded values
API_KEY = "abc123"

# GOOD: Use environment variables
API_KEY = os.getenv('API_KEY')

# BAD: No error handling
data = requests.get(url).json()

# GOOD: Handle errors
try:
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    data = response.json()
except requests.RequestException as e:
    logger.error(f"API error: {e}")
    return None
```

#### Frontend
```typescript
// BAD: No cleanup
useEffect(() => {
  const ws = new WebSocket(url);
  ws.onmessage = handleMessage;
}, []);

// GOOD: Cleanup on unmount
useEffect(() => {
  const ws = new WebSocket(url);
  ws.onmessage = handleMessage;
  return () => ws.close();
}, []);

// BAD: Inline styles
<div style={{ color: 'red' }}>Error</div>

// GOOD: Use Tailwind classes
<div className="text-rose-400">Error</div>

// BAD: Any type
const data: any = await fetch(...);

// GOOD: Proper typing
interface ApiResponse {
  success: boolean;
  data: Data;
}
const data: ApiResponse = await fetch(...);
```

## Review Comments Format

### Severity Levels
- **CRITICAL**: Security issue, data loss risk, production blocker
- **MAJOR**: Bug, performance issue, incorrect logic
- **MINOR**: Code style, optimization suggestion
- **NITPICK**: Personal preference, optional improvement

### Comment Examples
```
CRITICAL: Hardcoded API key exposed
- Move to environment variable
- Rotate the exposed key immediately

MAJOR: N+1 query in user list
- Use select_related('profile') to optimize

MINOR: Missing error handling
- Add try/catch for API call

NITPICK: Consider using const instead of let
- Variable is never reassigned
```

## Approval Criteria

### Must Have
- No critical or major issues
- All tests passing
- No security vulnerabilities
- Follows code style guidelines
- Has proper error handling

### Nice to Have
- Code comments for complex logic
- Performance optimizations
- Accessibility improvements
- Additional test coverage

## Post-Review Actions

### After Approval
```bash
# Merge to main
git checkout main
git merge feature-branch
git push origin main

# Delete feature branch
git branch -d feature-branch
git push origin --delete feature-branch
```

### After Deployment
- Monitor logs for errors
- Check health endpoints
- Verify feature works in production
- Update documentation if needed

## Review Tools

### Static Analysis
```bash
# Python
pylint app_name/
flake8 app_name/
mypy app_name/

# TypeScript
npm run lint
npm run type-check
```

### Security Scanning
```bash
# Python dependencies
pip-audit

# npm dependencies
npm audit

# Fix vulnerabilities
npm audit fix
```

### Code Coverage
```bash
# Backend
coverage run --source='.' manage.py test
coverage report
coverage html

# Frontend
npm test -- --coverage
```

## Documentation Review

### Check Documentation
- [ ] README updated if needed
- [ ] API documentation current
- [ ] Environment variables documented
- [ ] Deployment steps updated
- [ ] Architecture diagrams current

### Update Documentation
```bash
# Update API docs
# Edit API_DOCUMENTATION.md

# Update deployment guide
# Edit AWS_DEPLOYMENT_GUIDE.md

# Update architecture
# Edit ARCHITECTURE.md
```

## Continuous Improvement

### Metrics to Track
- Code review turnaround time
- Number of issues found per review
- Test coverage percentage
- Build success rate
- Deployment frequency

### Regular Reviews
- Weekly: Review open PRs
- Monthly: Review code quality metrics
- Quarterly: Review architecture decisions
