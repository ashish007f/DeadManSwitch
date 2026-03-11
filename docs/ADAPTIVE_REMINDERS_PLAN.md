# Feature Plan: Adaptive Reminder Tone (GenAI)

This feature integrates Google Gemini to dynamically generate check-in reminder messages. By varying the tone based on urgency, we improve user responsiveness and reduce notification "blindness."

## 1. Objective
Replace static, repetitive notification text with AI-generated messages that scale in urgency as a user's check-in deadline approaches. Additionally, include a **Direct Check-In Action** within the notification to allow users to confirm safety with a single tap.

## 2. Architecture
- **Service:** `GenAIService` (Backend) - Orchestrates calls to Gemini 1.5 Flash.
- **Trigger:** `CheckInScheduler` - Determines the "Urgency Level" and requests a message from the GenAI service.
- **Provider:** Google Generative AI (SDK).
- **Fallback:** Standard static messages (ensures reliability if the AI API fails or is unavailable).

## 3. Implementation Phases

### Phase 1: Backend Setup
- [ ] Add `google-generativeai` to `backend/requirements.txt`.
- [ ] Add `GEMINI_API_KEY` to environment variables and Cloud Run configuration.
- [ ] Create `backend/app/services/genai_service.py` with a `generate_reminder` method.

### Phase 2: Urgency Logic
- [ ] Update `CheckInScheduler` to calculate `urgency_level` based on current status and time:
    - `GENTLE`: Status is DUE_SOON.
    - `FIRM`: Status is MISSED.
    - `CRITICAL`: Status is GRACE_PERIOD (final warning before contacts are alerted).

### Phase 3: Prompt Engineering
- [ ] Design prompts that provide context to the LLM:
    - User's Display Name.
    - Time remaining or time since missed.
    - Required urgency level (Gentle, Firm, Critical).
    - Constraint: Keep messages under 160 characters for SMS/Push compatibility.

### Phase 4: Integration & Fallback
- [ ] Update `CheckInScheduler._send_reminder` to call `GenAIService`.
- [ ] Implement robust error handling to revert to static messages if GenAI fails.
- [ ] **Notification Action:** Add a "Check In Now" action/link to the notification payload:
    - For Push (FCM): An interactive action button that triggers the check-in API.

### Phase 5: Action Handling (New)
- [ ] Create a lightweight endpoint `/api/checkin/quick` that accepts a secure token for one-tap check-ins.
- [ ] Update Frontend to handle incoming notification clicks and trigger the check-in logic immediately.

### Phase 6: Validation
- [ ] Add unit tests for `GenAIService` logic.
- [ ] Verify tone variation in system logs during scheduled runs.

## 4. Example Tone Variations
| Level | AI Tone Goal | Example Output |
| :--- | :--- | :--- |
| **Gentle** | Casual, friendly nudge | "Hey [Name]! Just a quick tap needed to let us know you're doing good today." |
| **Firm** | Serious, direct | "[Name], your check-in is now overdue. Please confirm your status as soon as possible." |
| **Critical** | Urgent, high-stakes | "FINAL WARNING: [Name], we will notify your emergency contacts in 30 minutes if you don't check in now." |
