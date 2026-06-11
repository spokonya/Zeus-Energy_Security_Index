# Role-Based Access Control (RBAC)

Zeus uses lightweight RBAC in Streamlit: users pick a persona on the Home page (no passwords in this demo). Session state drives which sidebar links and pages are available.

## Session keys set at login

| Key | Purpose |
|-----|---------|
| `authenticated` | `True` after a persona is selected |
| `role` | `household_owner`, `journalist`, or `energy_trader` |
| `user_id` | Database user row for API calls |
| `first_name` | Display name shown in the UI |

## How access is enforced

1. **`SideBarLinks()`** in `app/src/modules/nav.py` renders only the links for the current `role`.
2. Pages call `SideBarLinks()` near the top; unauthenticated users are redirected to `Home.py`.
3. Default Streamlit multipage navigation is disabled in `app/src/.streamlit/config.toml` so the sidebar is fully custom.

## Page numbering

| Prefix | Persona / scope |
|--------|-----------------|
| `30_` | Shared (About) |
| `40_`–`42_` | Household owner |
| `51_`–`53_` | Energy trader |
| `60_`–`63_` | Journalist |

## Persona routes

Defined in `PERSONA_ROUTES` inside `nav.py` for bottom-of-page prev/next navigation within each persona flow.

## Database alignment

Demo users and personas are seeded in `database-files/02_zeus_core.sql`. The `users.persona` enum matches the three Streamlit roles above.
