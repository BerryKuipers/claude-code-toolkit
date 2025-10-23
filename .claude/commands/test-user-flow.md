# Test User Flow Command

Automates complete user flow testing with Loki tracing for debugging and development.

## Usage

```bash
/test-user-flow [stage] [options]
```

## Stages

- `register` - Create new test user
- `login` - Login and get auth token
- `profile` - Create/update profile with gender/interests
- `browse` - Test profile browsing/discovery
- `like` - Test liking profiles (when implemented)
- `match` - Test matching system (when implemented)
- `message` - Test messaging (when implemented)
- `full` - Complete end-to-end flow
- `debug-gender` - Specific test for GET vs PUT gender issue
- `notifications` - Test notification delivery and presence replay functionality

## Options

- `--user=<email>` - Use specific test user (default: generates unique user)
- `--gender=<male|female|non-binary|other>` - Set gender for testing
- `--trace` - Enable detailed Loki tracing
- `--dashboard` - Open Grafana dashboard after test

## Examples

```bash
/test-user-flow full --trace --dashboard
/test-user-flow debug-gender --gender=female --trace
/test-user-flow profile --user=test@example.com
```

## Output

- Creates test users with realistic data
- Logs all API calls and responses
- Sends structured logs to Loki for dashboard analysis
- Reports success/failure of each stage
- Provides links to Grafana dashboard queries

## Benefits

- 🔍 **Instant debugging** - Fire command, check Loki dashboard
- 🤖 **AI workflow improvement** - Pattern recognition from logs
- ⚡ **Fast development** - No manual testing steps
- 📊 **Traceability** - Full data flow visibility
- 🐛 **Issue reproduction** - Consistent test scenarios

## Command Evaluation and Self-Improvement

After each execution, the command evaluates its performance and automatically updates itself with improvements:

```bash
# Evaluation metrics tracked:
# - Test execution time
# - Success/failure rates per stage
# - API response times
# - Loki integration effectiveness
# - Issues discovered and resolved

# Auto-improvements applied:
# - Enhanced error handling patterns
# - Optimized API call sequences
# - Better Loki query generation
# - Improved test data generation
# - Streamlined dashboard integration

# The command file is automatically updated with:
# - Lessons learned from each execution
# - Performance optimizations discovered
# - Error patterns and their solutions
# - Best practices for user flow testing
```

This ensures the command continuously evolves and improves based on real usage patterns and discovered issues.