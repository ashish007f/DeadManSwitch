# I'mGood - Test Plan

## Test Scope

### 1. Authentication & User Management
- [ ] Firebase ID Token validation
- [ ] User creation on first login (with hashed identity)
- [ ] Session management (cookies / Phase 2 JWT)
- [ ] Display name updates
- [ ] Logout functionality

### 2. Check-in Functionality
- [ ] Record check-in (authenticated)
- [ ] Record check-in (unauthenticated - should fail)
- [ ] Check-in upsert behavior (only one row per user)
- [ ] Check-in with custom timestamp (testing helper)

### 3. Status Calculation
- [ ] Status transitions: SAFE → DUE_SOON → MISSED → GRACE_PERIOD → NOTIFIED
- [ ] Hours until due calculation
- [ ] No check-in scenario (should be MISSED)
- [ ] Edge cases around thresholds

### 4. Settings Management
- [ ] Get settings (defaults)
- [ ] Update check-in interval
- [ ] Update missed buffer hours
- [ ] Update grace period hours
- [ ] Update contacts list
- [ ] Settings persistence

### 5. Instructions Management
- [ ] Save instructions
- [ ] Get instructions
- [ ] Instructions persistence
- [ ] Empty instructions handling

### 6. Two-Tier Notification System
- [ ] First notification sent at GRACE_PERIOD (simple message)
- [ ] Second notification sent at NOTIFIED (with instructions)
- [ ] Notification deduplication (one per missed cycle)
- [ ] Multiple contacts receive notifications
- [ ] No duplicate notifications for same status

### 7. API Endpoints
- [ ] All endpoints require authentication
- [ ] Proper error handling (401, 404, 400)
- [ ] Response models match schema
- [ ] Cookie handling

### 8. Edge Cases & Error Handling
- [ ] Invalid phone number format (E.164)
- [ ] Expired or invalid Firebase ID Token
- [ ] User not found scenarios
- [ ] Database errors
- [ ] Missing required fields

### 9. Integration Tests
- [ ] Full user flow: signup → check-in → status check
- [ ] Settings update → check-in → status reflects new interval
- [ ] Notification flow simulation

## Test Execution

Running comprehensive test suite...
