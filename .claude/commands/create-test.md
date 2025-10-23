# Create Test Command

**Arguments:**
- `target` *(required)*: file/class/function to create tests for
- `type` *(optional)*: unit|integration|e2e (default: unit)
- `framework` *(optional)*: vitest|jest|playwright (auto-detect from project)
- `coverage` *(boolean)*: include coverage requirements (default: true)

**Success Criteria:** Test file created with comprehensive coverage, all tests pass, proper mocking setup

**Description:** AI-driven test creation that analyzes target code and generates comprehensive test suites with proper setup, mocking, and edge cases.

**Available Testing Commands:** Key commands for test creation and validation:
- `npm run test` - Run unit tests (nx run-many -t test)
- `npm run test:user-flow` - Basic user flow tests
- `npm run test:user-flow:enhanced` - Enhanced E2E tests with Playwright
- `npm run test:user-flow:login` - Login flow specific tests
- `npm run test:user-flow:admin` - Admin flow specific tests
- `npm run test:full` - Complete test suite (unit + user flow)
- `npm run lint` - Code linting to validate test syntax
- `npm run validate-types` - TypeScript validation for tests

## Test Creation Workflow (8 Steps)

### Step 1: Analyze Target Code
```bash
# Examine the target file structure and exports
echo "🔍 Analyzing target: $TARGET"

# Check if target exists
if [[ ! -f "$TARGET" ]]; then
  echo "❌ Target file not found: $TARGET"
  exit 1
fi

# Identify file type and framework context
FILE_EXT="${TARGET##*.}"
if [[ "$FILE_EXT" != "ts" && "$FILE_EXT" != "js" && "$FILE_EXT" != "tsx" && "$FILE_EXT" != "jsx" ]]; then
  echo "⚠️  Unsupported file type: $FILE_EXT"
  echo "Supported: .ts, .js, .tsx, .jsx"
  exit 1
fi

echo "✅ Target validated: $TARGET ($FILE_EXT)"
```

### Step 2: Determine Test Framework and Location
```bash
# Auto-detect testing framework from project
if [[ -f "vitest.config.ts" || -f "vitest.config.js" ]]; then
  FRAMEWORK="vitest"
  TEST_EXT="test.ts"
elif [[ -f "jest.config.js" || -f "jest.config.ts" ]]; then
  FRAMEWORK="jest"
  TEST_EXT="test.ts"
elif [[ -f "playwright.config.ts" ]]; then
  FRAMEWORK="playwright"
  TEST_EXT="spec.ts"
else
  echo "⚠️  No test framework detected, defaulting to vitest"
  FRAMEWORK="vitest"
  TEST_EXT="test.ts"
fi

# Determine test file location
if [[ "$TARGET" == *"/src/"* ]]; then
  # Place test next to source file
  TEST_FILE="${TARGET%.*}.$TEST_EXT"
else
  # Place in __tests__ directory
  TARGET_DIR=$(dirname "$TARGET")
  TARGET_NAME=$(basename "$TARGET" .${TARGET##*.})
  TEST_FILE="$TARGET_DIR/__tests__/$TARGET_NAME.$TEST_EXT"
  mkdir -p "$TARGET_DIR/__tests__"
fi

echo "📁 Test framework: $FRAMEWORK"
echo "📄 Test file: $TEST_FILE"
```

### Step 3: Extract Code Structure and Dependencies
```bash
# Read and analyze the target file
echo "🔬 Extracting code structure..."

# Identify exports, functions, classes, and dependencies
EXPORTS=$(grep -E "^export" "$TARGET" || echo "")
IMPORTS=$(grep -E "^import" "$TARGET" || echo "")
FUNCTIONS=$(grep -E "(function|const.*=.*=>|class)" "$TARGET" || echo "")

echo "📋 Found exports:"
echo "$EXPORTS"
echo ""
echo "📦 Found imports:"
echo "$IMPORTS"
echo ""
echo "⚙️  Found functions/classes:"
echo "$FUNCTIONS"
```

### Step 4: Generate Test Template
```bash
# Create comprehensive test file based on analysis
echo "📝 Generating test template for $FRAMEWORK..."

# The test template will be created by analyzing:
# - Function signatures and return types
# - Class methods and properties
# - Dependencies that need mocking
# - Edge cases and error conditions
# - Integration points

echo "Creating test file: $TEST_FILE"
```
*This step creates the actual test file with proper structure, imports, mocks, and test cases*

### Step 5: Setup Mocks and Test Data
```bash
# Configure mocking for dependencies
echo "🎭 Setting up mocks and test data..."

# Identify external dependencies that need mocking
EXTERNAL_DEPS=$(echo "$IMPORTS" | grep -E "from ['\"](?!\.)" || echo "")

if [[ -n "$EXTERNAL_DEPS" ]]; then
  echo "🔧 Dependencies requiring mocks:"
  echo "$EXTERNAL_DEPS"
  echo "   Setting up appropriate mocks..."
fi

# Create realistic test data based on function signatures
echo "🎲 Generating test data and fixtures..."
```

### Step 6: Generate Comprehensive Test Cases
```bash
# Create test cases covering:
echo "🧪 Generating comprehensive test cases..."

echo "📋 Test coverage includes:"
echo "   ✅ Happy path scenarios"
echo "   ✅ Edge cases and boundary conditions"
echo "   ✅ Error handling and invalid inputs"
echo "   ✅ Integration points and side effects"
echo "   ✅ Async operations and promises"
echo "   ✅ Type validation (TypeScript)"

# Generate specific tests based on code analysis
```

### Step 7: Validate and Run Generated Tests
```bash
# Ensure generated tests are valid and pass
echo "✅ Validating generated tests..."

# 1. Check TypeScript compilation
npm run validate-types
if [ $? -ne 0 ]; then
  echo "❌ TypeScript validation failed in generated tests"
  echo "🔧 Fixing type issues..."
  # Auto-fix common type issues
fi

# 2. Run the new tests
npm run test -- "$TEST_FILE"
if [ $? -ne 0 ]; then
  echo "❌ Generated tests are failing"
  echo "🔧 Analyzing and fixing test issues..."
  # Debug and fix test failures
else
  echo "✅ All generated tests pass!"
fi

# 3. Check test coverage
if [[ "$coverage" == "true" ]]; then
  echo "📊 Checking test coverage..."
  # Generate coverage report for the target file
fi
```

### Step 8: Report Test Creation Results
```bash
# Provide summary of test creation
echo ""
echo "📊 Test Creation Summary:"
echo "🎯 Target: $TARGET"
echo "📄 Test file: $TEST_FILE"
echo "🧪 Framework: $FRAMEWORK"
echo "📈 Test cases generated: [COUNT]"
echo "✅ Coverage: [PERCENTAGE]%"
echo ""
echo "🎉 Test creation completed successfully!"
echo "💡 Next: Run '/refactor $TARGET' to proceed with safe refactoring"
```

## Test Templates by Framework

### Vitest Template Structure
```typescript
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { [TARGET_EXPORTS] } from './[TARGET_NAME]'

describe('[TARGET_NAME]', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('[FUNCTION_NAME]', () => {
    it('should handle happy path', () => {
      // Test implementation
    })

    it('should handle edge cases', () => {
      // Edge case tests
    })

    it('should handle errors gracefully', () => {
      // Error handling tests
    })
  })
})
```

### Integration with Other Commands
- **Called by**: `/refactor` when no tests exist
- **Calls**: None (leaf command)
- **Output**: Creates test file ready for refactoring workflow

## Example Usage
```bash
/create-test src/services/ProfileService.ts
/create-test src/components/UserCard.tsx --type=integration
/create-test src/utils/validation.ts --coverage=true
```