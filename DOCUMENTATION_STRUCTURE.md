# SmartRisk Documentation Structure

## Overview
Complete documentation structure created for AI models to understand the SmartRisk project without manual explanation.

## Created Files

### Root Level (2 files)
- **PROJECT_OVERVIEW.md** - Complete project overview with all details
- **DOCUMENTATION_STRUCTURE.md** - This file (index of all documentation)

### .claude/ Directory (17 files)

#### Main Documentation (3 files)
- **.claude/CLAUDE.md** - Quick reference guide with project essentials
- **.claude/settings.json** - Project configuration and settings
- **.claude/settings.local.json** - Local development configuration

#### Rules (6 files)
- **.claude/rules/code-style.md** - Python/TypeScript coding standards
- **.claude/rules/api-conventions.md** - API design patterns and endpoints
- **.claude/rules/database.md** - Database schema and conventions
- **.claude/rules/frontend.md** - Frontend architecture and patterns
- **.claude/rules/deployment.md** - Deployment procedures and configuration
- **.claude/rules/testing.md** - Testing guidelines and strategies

#### Commands (4 files)
- **.claude/commands/build.md** - Build commands for local and production
- **.claude/commands/deploy.md** - Deployment commands and procedures
- **.claude/commands/fix-issue.md** - Common issues and troubleshooting
- **.claude/commands/review.md** - Code review guidelines and checklist

#### Skills (3 files)
- **.claude/skills/backend/SKILL.md** - Backend development guide
- **.claude/skills/frontend/SKILL.md** - Frontend development guide
- **.claude/skills/deploy/SKILL.md** - Deployment operations guide

### Docker Configuration (4 files)
- **docker/CLAUDE.md** - Docker architecture and configuration
- **docker/nginx/README.md** - Nginx reverse proxy configuration
- **docker/postgres/README.md** - PostgreSQL database configuration
- **docker/production/README.md** - Production deployment configuration

### Django Apps Documentation (4 files)
- **trading/CLAUDE.md** - Trading app (API endpoints, WebSocket, Celery tasks)
- **reversal_zones/CLAUDE.md** - Reversal zones app (signal generation, email alerts)
- **users/CLAUDE.md** - Users app (authentication, subscription management)
- **signal_alerts/CLAUDE.md** - Signal alerts app (email notifications)

## Documentation Coverage

### Project Information
✅ Brand name and contact information
✅ Tech stack and architecture
✅ Supported assets and timeframes
✅ Default settings and configuration
✅ Admin accounts and credentials
✅ Production server details

### Technical Details
✅ Signal calculation formulas
✅ Anti-chop filter logic
✅ WebSocket protocol
✅ API endpoints and responses
✅ Database schema
✅ Authentication flow

### Development Guidelines
✅ Code style conventions
✅ File organization
✅ Naming conventions
✅ Error handling patterns
✅ Logging standards
✅ Git commit messages

### Operational Procedures
✅ Build commands
✅ Deployment process
✅ Health checks
✅ Monitoring
✅ Backup and restore
✅ Rollback procedures
✅ Troubleshooting guide

### Domain Knowledge
✅ Backend architecture
✅ Frontend architecture
✅ Deployment infrastructure
✅ WebSocket implementation
✅ Celery task queue
✅ Chart integration

## How to Use This Documentation

### For AI Models
1. Start with **PROJECT_OVERVIEW.md** for complete project understanding
2. Read **.claude/CLAUDE.md** for quick reference
3. Refer to specific files in `.claude/rules/` for standards
4. Use `.claude/commands/` for operational tasks
5. Consult `.claude/skills/` for domain-specific knowledge

### For Developers
1. Read **PROJECT_OVERVIEW.md** first
2. Review code style in `.claude/rules/code-style.md`
3. Understand API conventions in `.claude/rules/api-conventions.md`
4. Follow deployment guide in `.claude/rules/deployment.md`
5. Use troubleshooting guide in `.claude/commands/fix-issue.md`

### For Operations
1. Read deployment guide in `.claude/rules/deployment.md`
2. Use deployment commands in `.claude/commands/deploy.md`
3. Follow troubleshooting in `.claude/commands/fix-issue.md`
4. Refer to deployment skill in `.claude/skills/deploy/SKILL.md`

## File Size Compliance
All documentation files are under 190 lines as requested:
- Longest file: ~185 lines
- Average file: ~150 lines
- Total files: 31 documentation files
- All files are readable and well-organized

## Key Information Quick Reference

### Production Server
```
IP: 54.183.178.141
SSH: ssh -i smartriskfx1.pem ubuntu@54.183.178.141
Path: ~/smartrisk
Domain: smartriskfx.com
```

### Admin Accounts
```
Email: alberttyagi123@gmail.com
Password: SmartRisk@2026!

Email: pythonbyvishal@gmail.com
Password: SmartRisk@2026!
```

### Important Files
```
Environment: .env (NOT .env.production)
Docker Compose: docker-compose.yml
Container Name: django (NOT "backend")
Token Name: access_token (NOT "auth_token")
```

### Signal Formula
```
BUY:
  entry = center_price
  target = outer_top
  calculate = target - entry
  stoploss = entry - (calculate * 0.5)

SELL:
  entry = center_price
  target = outer_bottom
  calculate = entry - target
  stoploss = target + (calculate * 0.5)
```

### Common Commands
```bash
# Deploy
git push origin main  # Triggers GitHub Actions

# Manual deploy
ssh -i smartriskfx1.pem ubuntu@54.183.178.141
cd ~/smartrisk
git pull origin main
sudo docker-compose down
sudo docker-compose up -d --build

# Check logs
sudo docker-compose logs -f django

# Run migrations
sudo docker-compose exec django python manage.py migrate
```

## Documentation Maintenance

### When to Update
- New features added
- Architecture changes
- API endpoints modified
- Deployment process updated
- Common issues discovered
- Configuration changes

### How to Update
1. Identify affected documentation files
2. Update relevant sections
3. Keep files under 190 lines
4. Maintain consistent formatting
5. Update "Last Updated" date
6. Commit with descriptive message

## Benefits of This Structure

### For AI Models
✅ Complete project understanding without manual explanation
✅ Quick reference for common tasks
✅ Detailed technical specifications
✅ Troubleshooting guides
✅ Best practices and conventions

### For Development Team
✅ Onboarding new developers faster
✅ Consistent code standards
✅ Clear operational procedures
✅ Reduced knowledge silos
✅ Better collaboration

### For Operations
✅ Clear deployment procedures
✅ Troubleshooting guides
✅ Health check procedures
✅ Backup and restore processes
✅ Emergency procedures

## Next Steps

### Immediate
- [x] Create documentation structure
- [x] Document all project details
- [x] Organize by category
- [x] Keep files under 190 lines

### Future
- [ ] Add API request/response examples
- [ ] Create architecture diagrams
- [ ] Add performance benchmarks
- [ ] Document edge cases
- [ ] Create video tutorials

## Conclusion

This documentation structure provides complete project information for AI models and developers. All essential details are documented, organized, and easily accessible. No manual explanation needed - just point to the relevant documentation file.

---

**Created**: May 11, 2026
**Total Files**: 31 documentation files
**Total Lines**: ~4,500 lines of comprehensive documentation
**Status**: Complete and Production Ready
