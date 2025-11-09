# Pi Zero 2W Refactoring Implementation Plan

**Version:** 1.0 (High-Level)
**Date:** November 9, 2025
**Status:** DRAFT - Ready for Review

---

## Overview

**Goal:** Refactor the codebase to support dual input methods (GPIO button + touchscreen), improve modularity, modernize WebUI, and add comprehensive testing.

**Estimated Timeline:** 4-6 weeks
**Risk Level:** MEDIUM (major refactoring with backwards compatibility concerns)

---

## Phase 0: Cleanup - Remove Unused Apps
**Duration:** 1-2 hours
**Risk:** LOW

### Objective
Remove MBTA, Weather, and Pomodoro apps to simplify scope and focus on core functionality.

### Tasks
1. Delete app files: `mbta_app.py`, `weather_cal_app.py`, `pomodoro_app.py`
2. Remove from `menu_button.py` and `menu_simple.py` app lists
3. Remove icons: `mbta.bmp`, `weather.bmp`, `clock.bmp`, `pomodoro.bmp`
4. Clean config sections from `config.json`
5. Update documentation to reflect removal

### Deliverables
- [ ] Apps removed from codebase
- [ ] Menus updated (4 apps remaining: Medicine, Disney, Flights, Forbidden, Reboot)
- [ ] Config cleaned
- [ ] Commit: "Phase 0: Remove MBTA, Weather, Pomodoro apps"

---

## Phase 1: Input Abstraction System
**Duration:** 1-2 days
**Risk:** MEDIUM (foundation for all other changes)

### Phase 1.1: Create Input Abstraction (4-6 hours)

#### Objective
Create unified input handler that works with both GPIO button and touchscreen.

#### Tasks
1. Create `input_handler.py` with abstract base class:
   - `InputHandler` base class
   - `ButtonInputHandler` (GPIO-only)
   - `TouchInputHandler` (touchscreen)
   - `DualInputHandler` (both)
2. Define common interface:
   - `wait_for_click()` → returns position or None
   - `wait_for_hold()` → returns True/False
   - `check_exit()` → returns True/False
3. Event-based architecture (replace polling)

#### Deliverables
- [ ] `input_handler.py` created
- [ ] All three handler types implemented
- [ ] Basic integration tests pass

### Phase 1.2: Hardware Detection (2-3 hours)

#### Objective
Auto-detect available hardware (button vs touch vs both) and configure accordingly.

#### Tasks
1. Create `hardware_config.py`:
   - Probe GPIO pin 3 for button
   - Probe I2C for GT1151 touch controller
   - Return hardware capabilities
2. Create `config_manager.py`:
   - Load/save config with hardware profile
   - Support environment variable overrides
3. Update startup to auto-configure

#### Deliverables
- [ ] `hardware_config.py` with detection logic
- [ ] `config_manager.py` for centralized config
- [ ] Startup auto-configuration works

---

## Phase 2: Medicine App Enhancements
**Duration:** 1 day
**Risk:** LOW

### Phase 2.1: Add Skip Functionality (6-8 hours)

#### Objective
Allow users to skip medicines (mark as "skipped" instead of "taken").

#### Tasks
1. Update `medicine_data.json` schema:
   - Add `"skipped": true` option to tracking entries
2. Update `medicine_app.py`:
   - Add skip UI state (3-button choice: Take / Skip / Exit)
   - Visual: "Click: Take | Double-click: Skip | Hold: Exit"
3. Update API endpoints:
   - `POST /api/medicine/mark-skipped`
   - Update `GET /api/medicine/data` to show skipped vs taken
4. Update WebUI to display skip status

#### Deliverables
- [ ] Skip functionality in medicine app
- [ ] API endpoints for skip
- [ ] WebUI shows skipped medicines differently
- [ ] Commit: "Phase 2.1: Add medicine skip functionality"

---

## Phase 3: Refactor All Apps for Dual-Input
**Duration:** 2-3 days
**Risk:** MEDIUM (touches all apps)

### Strategy
Refactor each app to use new `InputHandler` instead of direct GPIO/touch access.

### Phase 3.1: Medicine App (4-6 hours)
- Replace `pthread_irq()` with `InputHandler`
- Update button logic to use abstraction
- Test with both input methods
- **Commit:** "Phase 3.1: Refactor Medicine app for dual-input"

### Phase 3.2: Disney App (3-4 hours)
- Same pattern as Medicine
- **Commit:** "Phase 3.2: Refactor Disney app for dual-input"

### Phase 3.3: Flights App (3-4 hours)
- Same pattern
- **Commit:** "Phase 3.3: Refactor Flights app for dual-input"

### Phase 3.4: Forbidden App (1-2 hours)
- Simple app, quick refactor
- **Commit:** "Phase 3.4: Refactor Forbidden app for dual-input"

### Phase 3.5: Reboot App (1-2 hours)
- Same pattern
- **Commit:** "Phase 3.5: Refactor Reboot app for dual-input"

### Final Commit
**Commit:** "Phase 0-3 complete: Input abstraction and app refactoring"

---

## Phase 4: WebUI Redesign
**Duration:** 3-4 days
**Risk:** MEDIUM (major UI overhaul)

### Phase 4.1: Redesign WebUI Architecture (1 day)

#### Objective
Modern component-based architecture with better separation of concerns.

#### Tasks
1. Split monolithic `web_config.py` into:
   - `web/server.py` - Flask app
   - `web/api.py` - REST endpoints
   - `web/templates/` - HTML templates (separate from Python)
   - `web/static/` - CSS/JS files
2. Add template engine (Jinja2)
3. Modern CSS framework (consider Tailwind or keep custom)
4. Modular JavaScript (ES6 modules)

#### Deliverables
- [ ] Restructured web directory
- [ ] Template system working
- [ ] Static assets organized

### Phase 4.2: Medicine Management UI (1 day)

#### Objective
Enhanced medicine management with better UX.

#### Tasks
1. Redesign medicine list:
   - Grid/card layout instead of list
   - Inline editing
   - Drag-to-reorder
2. Add features:
   - Bulk operations
   - Export/import medicines (JSON/CSV)
   - Medicine history view (last 30 days)
3. Skip status indicators

#### Deliverables
- [ ] New medicine UI components
- [ ] Enhanced features working
- [ ] Mobile-responsive design

### Phase 4.3: System Configuration UI (4-6 hours)

#### Objective
Better system settings and diagnostics.

#### Tasks
1. System status dashboard:
   - Hardware detected (button/touch/both)
   - Display info (model, refresh count)
   - Disk space, uptime
2. Settings panels:
   - Display settings (rotation, partial refresh limit)
   - Input method preferences
   - Time windows configuration
3. Diagnostics:
   - Test button
   - Test touch
   - Test display refresh

#### Deliverables
- [ ] System dashboard
- [ ] Settings panels
- [ ] Diagnostic tools

### Phase 4.4: API Integration (4-6 hours)

#### Objective
Update API to match new architecture and add missing endpoints.

#### Tasks
1. Add authentication:
   - API key in header or config
   - Simple token-based auth
2. New endpoints:
   - `GET /api/system/status`
   - `GET /api/system/hardware`
   - `POST /api/system/test-input`
3. Improve error handling:
   - Consistent error response format
   - Input validation with schemas
4. Add rate limiting

#### Deliverables
- [ ] API authentication implemented
- [ ] New endpoints working
- [ ] Better error handling
- [ ] **Commit:** "Phase 4: Complete WebUI redesign"

---

## Phase 5: Testing Infrastructure
**Duration:** 2-3 days
**Risk:** LOW (new code, doesn't break existing)

### Phase 5.1: Input Handler Tests (4-6 hours)

#### Objective
Unit tests for input abstraction layer.

#### Tasks
1. Create `tests/test_input_handler.py`
2. Mock GPIO and touch hardware
3. Test all three handler types
4. Coverage target: 80%+

#### Deliverables
- [ ] Unit tests for input handlers
- [ ] 80%+ coverage
- [ ] CI-ready test suite

### Phase 5.2: App Integration Tests (6-8 hours)

#### Objective
Integration tests for each app.

#### Tasks
1. Create `tests/test_medicine_app.py`
2. Test medicine tracking logic
3. Test skip functionality
4. Create similar tests for other apps
5. Coverage target: 60%+

#### Deliverables
- [ ] Integration tests for all apps
- [ ] 60%+ coverage

### Phase 5.3: WebUI Tests (4-6 hours)

#### Objective
API endpoint testing and basic frontend tests.

#### Tasks
1. Create `tests/test_api.py`
2. Test all endpoints with pytest
3. Test authentication
4. Add basic Selenium tests for critical flows
5. Coverage target: 70%+

#### Deliverables
- [ ] API endpoint tests
- [ ] Basic frontend tests
- [ ] **Commit:** "Phase 5: Add comprehensive test suite"

---

## Phase 6: Documentation & Deployment
**Duration:** 1-2 days
**Risk:** LOW

### Phase 6.1: Documentation (6-8 hours)

#### Objective
Update all documentation to reflect new architecture.

#### Tasks
1. Update `README.md`:
   - New architecture diagram
   - Dual-input support explanation
   - Updated setup instructions
2. Update `DOCUMENTATION.md`:
   - Input handler API docs
   - Hardware detection process
   - New WebUI features
3. Create `DEVELOPER_GUIDE.md`:
   - How to add new apps
   - Testing guidelines
   - Architecture decisions
4. Update `IPHONE_SHORTCUTS_GUIDE.md`:
   - New API endpoints
   - Authentication setup

#### Deliverables
- [ ] All docs updated
- [ ] Developer guide created
- [ ] Architecture diagrams updated

### Phase 6.2: Deployment Scripts (3-4 hours)

#### Objective
Automated deployment and setup.

#### Tasks
1. Create `requirements.txt` with pinned versions
2. Create `setup.sh`:
   - Detect hardware
   - Install dependencies
   - Configure systemd services
3. Create `deploy.sh`:
   - Update code
   - Restart services
   - Run health checks
4. Update systemd service files:
   - Separate services for menu and web
   - Auto-restart on failure
   - Proper environment variables

#### Deliverables
- [ ] Setup script working
- [ ] Deployment script working
- [ ] Systemd services updated
- [ ] **Commit:** "Phase 6: Documentation and deployment automation"

---

## Dependency Graph

```
Phase 0 (Cleanup)
    ↓
Phase 1.1 (Input Abstraction) ← Foundation
    ↓
Phase 1.2 (Hardware Detection)
    ↓
Phase 2.1 (Medicine Skip) ← Can be parallel
    ↓
Phase 3.x (Refactor Apps) ← Depends on 1.1, 1.2
    ↓
Phase 4.x (WebUI) ← Can start in parallel with 3.x
    ↓
Phase 5.x (Testing) ← After all code changes
    ↓
Phase 6.x (Docs & Deploy) ← Final phase
```

---

## Risk Assessment

### HIGH RISK
- **Phase 1.1:** Input abstraction is foundation - if wrong, everything breaks
  - **Mitigation:** Prototype quickly, test early with real hardware

### MEDIUM RISK
- **Phase 3.x:** Refactoring all apps touches a lot of code
  - **Mitigation:** One app at a time, commit frequently, test each

- **Phase 4.1:** WebUI restructure could break existing functionality
  - **Mitigation:** Keep old version as fallback, feature flag new UI

### LOW RISK
- **Phase 0:** Simple deletion
- **Phase 5:** New code (tests)
- **Phase 6:** Documentation

---

## Success Criteria

### Phase Completion Criteria
- [ ] All apps work with GPIO button (existing functionality)
- [ ] All apps work with touchscreen (if available)
- [ ] All apps work with both inputs simultaneously
- [ ] WebUI is functional and authenticated
- [ ] Test suite passes with 60%+ coverage
- [ ] Documentation is complete and accurate
- [ ] Setup script works on fresh Pi Zero 2W

### Code Quality Gates
- [ ] No pylint errors
- [ ] All tests passing
- [ ] No security vulnerabilities (bandit scan)
- [ ] API documented (OpenAPI/Swagger)

---

## Quick Start Recommendations

### Week 1
- [ ] Phase 0 (2 hours)
- [ ] Phase 1.1 (6 hours)
- [ ] Phase 1.2 (3 hours)
- [ ] Phase 2.1 (8 hours)
- **Total: ~19 hours**

### Week 2
- [ ] Phase 3.1 (6 hours)
- [ ] Phase 3.2 (4 hours)
- [ ] Phase 3.3 (4 hours)
- [ ] Phase 3.4 (2 hours)
- [ ] Phase 3.5 (2 hours)
- **Total: ~18 hours**

### Week 3
- [ ] Phase 4.1 (8 hours)
- [ ] Phase 4.2 (8 hours)
- [ ] Phase 4.3 (6 hours)
- **Total: ~22 hours**

### Week 4
- [ ] Phase 4.4 (6 hours)
- [ ] Phase 5.1 (6 hours)
- [ ] Phase 5.2 (8 hours)
- [ ] Phase 5.3 (6 hours)
- **Total: ~26 hours**

### Week 5-6 (Buffer)
- [ ] Phase 6.1 (8 hours)
- [ ] Phase 6.2 (4 hours)
- [ ] Bug fixes and polish (10-20 hours)
- **Total: ~22-32 hours**

**Total Estimated Effort:** 107-117 hours (3-4 weeks full-time, 6-8 weeks part-time)

---

## Open Questions for Discussion

1. **Input Priority:** If both button and touch are available, which takes precedence?
2. **Backwards Compatibility:** Keep support for old `menu_simple.py` or full migration?
3. **Database Migration:** Move from JSON to SQLite now or later?
4. **API Authentication:** Simple API key or full OAuth/JWT?
5. **Testing Strategy:** Mock hardware or require real Pi for tests?

---

## Next Steps

1. **Review this plan** - adjust timelines, scope, priorities
2. **Decide on open questions** above
3. **Start with Phase 0** - quick win to build momentum
4. **Prototype Phase 1.1** - validate input abstraction approach
5. **Iterate** - adjust plan based on learnings

---

**Status:** Ready for review and refinement
**Last Updated:** November 9, 2025
