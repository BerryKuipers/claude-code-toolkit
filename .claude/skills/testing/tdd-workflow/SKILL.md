# TDD Workflow Skill

Test-Driven Development workflow for implementing features with tests first.

## Overview

This skill enforces the Red-Green-Refactor cycle:
1. **RED**: Write failing tests first
2. **GREEN**: Write minimal code to pass tests
3. **REFACTOR**: Improve code while keeping tests green

## When to Use

- Implementing new features
- Fixing bugs (regression test first)
- Adding functionality to existing modules
- When coverage threshold must be met (80%+)

## Workflow Steps

### Step 1: Define User Journey

Before writing any code, define the user story:

```markdown
**As a** [role/persona]
**I want to** [action/feature]
**So that** [benefit/value]

**Acceptance Criteria:**
- [ ] Criterion 1
- [ ] Criterion 2
- [ ] Criterion 3
```

### Step 2: Generate Test Cases

Create comprehensive test suite BEFORE implementation:

```typescript
// tests/feature.test.ts

describe('FeatureName', () => {
  // Happy path tests
  describe('when valid input', () => {
    it('should return expected result', () => {
      // Arrange
      const input = { /* valid data */ };

      // Act
      const result = featureFunction(input);

      // Assert
      expect(result).toEqual(expectedOutput);
    });
  });

  // Edge cases
  describe('edge cases', () => {
    it('should handle empty input', () => {
      expect(featureFunction({})).toBeNull();
    });

    it('should handle boundary values', () => {
      expect(featureFunction({ limit: 0 })).toEqual([]);
    });
  });

  // Error scenarios
  describe('error handling', () => {
    it('should throw on invalid input', () => {
      expect(() => featureFunction(null)).toThrow('Invalid input');
    });

    it('should handle network failures gracefully', async () => {
      mockApi.mockRejectedValue(new Error('Network error'));
      await expect(featureFunction()).rejects.toThrow('Network error');
    });
  });
});
```

### Step 3: RED Phase - Verify Tests Fail

```bash
# Run tests - they MUST fail
npm test -- --testPathPattern="feature.test.ts"

# Expected output: X failing tests
# If tests pass without implementation, tests are wrong
```

**Checkpoint**: All tests should fail with clear error messages.

### Step 4: Implement Minimal Code

Write the **minimum code** to make tests pass:

```typescript
// src/feature.ts

export function featureFunction(input: FeatureInput): FeatureOutput {
  // Minimal implementation - just enough to pass tests
  if (!input) {
    throw new Error('Invalid input');
  }

  // Implementation...
  return result;
}
```

**Rules for this phase:**
- Write ONLY what tests require
- No premature optimization
- No additional features
- No "while I'm here" improvements

### Step 5: GREEN Phase - Verify Tests Pass

```bash
# Run tests - they MUST pass now
npm test -- --testPathPattern="feature.test.ts"

# Expected: All tests passing
```

**Checkpoint**: All tests green before proceeding.

### Step 6: Refactor (Optional)

With green tests as safety net, improve code quality:

```bash
# After each refactor, verify tests still pass
npm test -- --testPathPattern="feature.test.ts"
```

**Safe refactoring operations:**
- Extract helper functions
- Rename for clarity
- Remove duplication
- Simplify logic
- Add types

**Unsafe without more tests:**
- Change behavior
- Add features
- Modify API contract

### Step 7: Coverage Validation

```bash
# Check coverage meets threshold (80%+)
npm test -- --coverage --collectCoverageFrom="src/feature.ts"

# Output should show:
# - Statements: 80%+
# - Branches: 80%+
# - Functions: 80%+
# - Lines: 80%+
```

If coverage < 80%, add more tests for:
- Uncovered branches
- Error paths
- Edge cases

## Three-Layer Testing Strategy

### Unit Tests (Jest/Vitest)
- Test individual functions in isolation
- Mock all dependencies
- Fast execution (<1s per test)

```typescript
// Unit test example
it('calculates total correctly', () => {
  const items = [{ price: 10 }, { price: 20 }];
  expect(calculateTotal(items)).toBe(30);
});
```

### Integration Tests
- Test API endpoints with real database (test DB)
- Verify service interactions
- Test complete request/response cycle

```typescript
// Integration test example
it('POST /api/orders creates order', async () => {
  const response = await request(app)
    .post('/api/orders')
    .send({ items: [{ productId: 1, quantity: 2 }] });

  expect(response.status).toBe(201);
  expect(response.body.orderId).toBeDefined();
});
```

### E2E Tests (Playwright)
- Test complete user workflows
- Real browser automation
- No mocks - full system

```typescript
// E2E test example
test('user can complete checkout', async ({ page }) => {
  await page.goto('/products');
  await page.click('[data-testid="add-to-cart"]');
  await page.click('[data-testid="checkout"]');
  await page.fill('[name="email"]', 'test@example.com');
  await page.click('[data-testid="place-order"]');
  await expect(page.locator('.order-confirmation')).toBeVisible();
});
```

## Test Quality Patterns

### Descriptive Test Names
```typescript
// Bad
it('works', () => {});

// Good
it('returns empty array when user has no orders', () => {});
```

### Arrange-Act-Assert Structure
```typescript
it('calculates discount for premium members', () => {
  // Arrange
  const user = { membership: 'premium' };
  const order = { total: 100 };

  // Act
  const discount = calculateDiscount(user, order);

  // Assert
  expect(discount).toBe(15); // 15% for premium
});
```

### Independent Tests
```typescript
// Bad - tests depend on order
let sharedState;
it('creates item', () => { sharedState = create(); });
it('uses item', () => { use(sharedState); }); // Fails if run alone

// Good - each test is self-contained
it('creates and uses item', () => {
  const item = create();
  const result = use(item);
  expect(result).toBeDefined();
});
```

## Coverage Thresholds

| Metric | Minimum | Target | Excellent |
|--------|---------|--------|-----------|
| Statements | 70% | 80% | 90%+ |
| Branches | 70% | 80% | 85%+ |
| Functions | 80% | 90% | 95%+ |
| Lines | 70% | 80% | 90%+ |

## Output Contract

When this skill completes, report:

```markdown
## TDD Workflow Complete

### User Story
As a [role], I want to [action] so that [benefit]

### Test Coverage
- Statements: X%
- Branches: X%
- Functions: X%
- Lines: X%
- **Status**: [MEETS THRESHOLD / BELOW THRESHOLD]

### Tests Created
| File | Tests | Passing |
|------|-------|---------|
| feature.test.ts | 12 | 12 |

### Implementation
| File | Lines | Coverage |
|------|-------|----------|
| feature.ts | 45 | 85% |

### Verification
- [x] RED phase: Tests failed before implementation
- [x] GREEN phase: All tests passing
- [x] Coverage meets 80% threshold
- [x] No skipped tests
```

## Integration with Wrappers

The `/bk-implement` wrapper can invoke this skill:

```markdown
"Before implementing, I need to follow TDD workflow.

1. Create test file with failing tests
2. Verify tests fail (RED)
3. Implement minimal code
4. Verify tests pass (GREEN)
5. Check coverage threshold

Feature: [DESCRIPTION]
"
```

## Common Mistakes to Avoid

1. **Writing tests after code** - Defeats the purpose
2. **Testing implementation, not behavior** - Fragile tests
3. **Too many mocks** - Tests don't reflect reality
4. **Skipping edge cases** - Bugs in production
5. **100% coverage obsession** - Diminishing returns past 90%
6. **Slow tests** - Developers skip them
