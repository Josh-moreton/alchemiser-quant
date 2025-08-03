# Next.js ➜ Capacitor iOS Conversion Checklist

---

## 1. Project Structure & Build Configuration

- **Static export**
  - Update `next.config.js` → `output: 'export'`.
  - Disable Next image optimizer (`images.unoptimized: true` or custom loader).
  - Ensure `next build && next export` produces all needed pages in `out/`.

- **Remove server-only code**
  - Strip or refactor Server Components, API routes, `middleware`, `getServerSideProps`, Server Actions.
  - Replace server calls with client-side fetches to an external backend.
  - Identify dynamic routes. Convert to client-side data fetching or pre-generate pages.
    - Shell pages read params from `window.location` and fetch data on load.
    - Provide loading states and error handling.

- **PWA support**
  - Add/verify `manifest.json` with name, icons, theme colors.
  - Include service worker for caching/offline behavior; handle offline UI gracefully.

- **Capacitor setup**
  - `npm install @capacitor/core @capacitor/cli`.
  - `npx cap init` → set `webDir: "out"` in `capacitor.config`.
  - `npx cap add ios`.
  - Build script: `next build && next export && npx cap sync ios`.

- **Exclude landing page**
  - Remove marketing landing from static export or redirect to app home.
  - Ensure initial route inside Capacitor is the app dashboard/login.

- **Routing**
  - Use `<Link>`/`useRouter` for navigation; replace `<a>` tags causing full reloads.
  - Consider a wildcard page to bootstrap React for unknown routes.

---

## 2. UI/UX for an App-like Experience

- **Responsive/mobile audit**
  - Tailwind breakpoints for small screens; test all pages on iPhone sizes.
  - Adjust ShadCN components (dialogs, drawers) to full-screen on mobile.
  - Replace hover interactions with tap equivalents.

- **Navigation patterns**
  - Convert top nav bars to bottom tabs or hamburger menu.
  - Remove web-only headers/footers or marketing banners.
  - Use mobile terminology (“tap”, not “click”).

- **Styling & theming**
  - Use system font or ensure custom fonts render well.
  - Prefer iOS-style icons (SF Symbols or high-res icons).
  - Ensure color contrast and touch feedback.
  - Add `<meta name="viewport" content="viewport-fit=cover">`.
  - Handle safe areas with `env(safe-area-inset-*)` CSS.
  - Customize splash screen storyboard and status bar color via Capacitor plugins/Info.plist.

- **Web-behavior cleanup**
  - Remove PWA install prompts, pull-to-refresh, etc.
  - External links → open with `Capacitor Browser` or InAppBrowser.
  - Test file inputs/photo uploads within WebView.

---

## 3. Native Integration

- **Plugins to consider**
  - Push notifications (`@capacitor/push-notifications`).
  - Geolocation (`@capacitor/geolocation`) for location-based features.
  - Camera or Filesystem if profile photos/uploads needed.
  - Add `Info.plist` usage descriptions for any permissions.

- **Device testing**
  - Run on iPhone simulators & physical devices.
  - Test deep links, navigation, performance, and offline behavior.
  - Verify Clerk authentication flows, including OAuth redirects via `App.addListener('appUrlOpen', …)`.

- **Info.plist & native tweaks**
  - Add permission strings, ATS exceptions if necessary (prefer HTTPS).
  - Lock orientation (likely portrait), define background modes if needed.
  - Remove PWA install prompts; ensure icons & launch screen assets exist.
  - Document native changes so `cap sync` doesn’t overwrite.

- **Performance optimization**
  - Remove large/unneeded assets; compress images.
  - Ensure production builds (no source maps, debug logs).
  - Lazy-load heavy modules.

---

## 4. App Store Compliance

- **Human Interface Guidelines**
  - Clean, intuitive UI; consistent spacing; back navigation within the app.
  - Avoid dummy content or broken links.
  - Provide in-app “About/Privacy Policy” screens; avoid web references.

- **Privacy & user data**
  - Support account deletion in-app (Guideline 5.1.1(v)).
  - Provide Privacy Policy & Terms links in-app and in metadata.
  - If using third-party logins, enable Sign in with Apple or an equivalent privacy-friendly option.
  - Prepare App Privacy responses for data collection.

- **User-generated content policies**
  - Include reporting/blocking features.
  - Terms of Use/EULA accessible.
  - Ensure moderation process is documented.

- **Payments**
  - For real-world services, external payments (Stripe, etc.) allowed.
  - Any digital goods/subscriptions must use In-App Purchase.
  - Clarify payment model in review notes.

- **Performance & functionality**
  - No crashes or “coming soon” pages.
  - Provide a demo account for reviewers.
  - Avoid thin-wrapper impression—highlight native-like features (notifications, camera, etc.).

- **Other guideline checks**
  - No forbidden APIs, no deceptive system dialogs.
  - Handle encryption compliance.
  - Respect gestures (swipe back).
  - If video/audio capturing is added, request permissions and disclose usage.

---

## 5. Testing & Submission

- **Comprehensive QA**
  - Test all flows: signup/login, browse listings, messaging, profile edits, etc.
  - Confirm production API endpoints & environment variables.
  - Run on multiple devices/iOS versions; consider TestFlight beta.

- **App Store metadata prep**
  - App name, description, keywords.
  - Privacy Policy & Support URLs.
  - Contact info.
  - Screenshots for 5.5" & 6.5" iPhones.
  - 1024x1024 app icon, prepared asset catalog.

- **Review notes**
  - Provide demo credentials, describe key features, mention moderation and account deletion.
  - Explain external payment usage if applicable.

- **Final guideline pass**
  - Verify against App Store Review Guidelines sections 1–5.
  - Ensure no disallowed content or behavior.

---

## 6. Conclusion & TODO Highlights

### Key TODOs
1. Configure static export in `next.config.js`.
2. Remove SSR/server actions and convert dynamic routes to client-side fetching.
3. Add/validate manifest and service worker.
4. Set up Capacitor (`init`, `add ios`, `sync`).
5. Replace landing page with app home; ensure client-side routing only.
6. Audit and revise UI for mobile (navigation, safe areas, ShadCN components).
7. Integrate native plugins (push, geolocation, camera) as needed; update `Info.plist`.
8. Implement account deletion, reporting/blocking, privacy links.
9. Prepare app icons, splash screen, and App Store metadata.
10. Conduct full QA and provide demo account for review.

Following this roadmap will produce a self-contained iOS app that feels native, is compliant with Apple’s policies, and is ready for App Store submission.

