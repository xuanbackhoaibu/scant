# Google login and Sheets consent

Basic sign-in requests only `openid email profile`. It does not request offline access or aggregate previously granted data scopes. `/api/auth/google?intent=sheets` starts an explicit authenticated connection in a popup, requesting Sheets write access for existing synchronization features. No new Drive scope is requested.

The callback validates the OAuth state and binds the connection to the app user who started it. `/auth/google/connect` stores credentials under `google_data` without changing login identity or issuing another app session. Existing `google` credentials remain usable for Sheets when their recorded scopes permit it; basic sign-in does not overwrite them. Refresh expiry now includes the returned lifetime.

The popup callback posts a same-origin result to its opener. The parent validates the sending window and reloads connection status, retaining its URL and workspace. Auth bootstrap is skipped inside the connection callback because closing the popup can abort its requests and inadvertently clear shared localStorage. A blocked popup produces a recoverable message.

Connection controls appear in Settings / Security, URL source setup, and Google Sheets analysis workspaces. Public URL import remains available without a connection. Private-link import behavior is unchanged.

Validation: 74 frontend tests, 16 focused backend tests (connection, Sheets sync, account controls), typecheck and production build. ESLint has 103 existing warnings and zero errors. Playwright with mocked consent confirms popup closure, unchanged parent session/URL, and no horizontal overflow at 1280px and 390px. Live port 3050 authorization redirect requests only identity scopes. Real Google consent and Cloud publishing status require the owner's Google account; they were not changed or tested through actual authorization.
