# Fix templates

Drafted text and exact edits for the recurring findings. Everything with `<...>` is a
placeholder you fill from what the scan and the screenshots already told you. Offer
these filled in, then let the user edit — never present a template with the blanks
still showing.

## Review notes (page 07)

The notes field is where most avoidable rejections are prevented. Draft it to cover
the three things a reviewer needs, in order.

### SMS-OTP login with a test-number bypass

> Sign-in uses a phone number and an SMS one-time code. For review, use
> `<test-number>` with code `<code>`. This number bypasses SMS delivery on our
> backend and always accepts that code, so no live SMS is required.
>
> `<If regional:>` Delivery and payment are available only in `<country>`. Please use
> a `<country>` postal address at checkout; payment runs through `<gateway>`.

Only include the second paragraph if page 03 produced a territory finding. Confirm the
bypass actually works before promising it — this is attested by the user, not
verified.

### Built-in demo mode (the 2.1 alternative)

Offer this when a real demo account is impossible for legal or security reasons:

> Sign-in cannot use a shared demo account for `<reason>`. The app includes a demo
> mode: `<how to reach it>`. It exercises the full feature set without a live account.

Note that Apple requires prior approval for demo mode under 2.1 — mention that to the
user.

### Regional availability, no login

> The app serves `<country>` only. Payment uses `<gateway>` and delivery requires a
> `<country>` address. To test checkout, please use `<example valid postcode>`.

## Privacy manifest (page 04, code fix)

When `PrivacyInfo.xcprivacy` declares no tracking while the app ships an
advertising-identifier SDK, the manifest is what changes. Show the diff:

```xml
<!-- ios/<target>/PrivacyInfo.xcprivacy -->
<key>NSPrivacyTracking</key>
<true/>
```

If tracking domains are known, they belong here too:

```xml
<key>NSPrivacyTrackingDomains</key>
<array>
    <string><domain the ad SDK contacts></string>
</array>
```

And `NSPrivacyCollectedDataTypes` must stop being empty — it needs an entry per data
type the app actually collects. This is not a mechanical fix: the entries depend on
what the SDKs collect, so walk the user through it against the App Privacy labels
rather than pasting a canned array. The manifest and the labels must end up saying the
same thing.

Do not apply this blindly. Confirm first that tracking genuinely occurs — an app with
only analytics and crash reporting is correctly declaring no tracking, and flipping
the flag would make the manifest *wrong*.

## Unused permission (page-level, code fix)

For a usage-description key nothing exercises, the fix is deletion:

```xml
<!-- remove from ios/<target>/Info.plist -->
<key>NSLocationAlwaysAndWhenInUseUsageDescription</key>
<string>...</string>
```

Before removing a location key, confirm `UIBackgroundModes` does not list `location`
and no code requests always-authorisation — both already checked in `findings.json`.
If the app does use foreground location, keep `NSLocationWhenInUseUsageDescription`
and remove only the Always variant.

## Version alignment (page 06, code fix)

When an extension's `MARKETING_VERSION` differs from the app's, align them. Show each
edit separately:

```
# ios/<project>.xcodeproj/project.pbxproj
# every target, app and extensions, on one value:
MARKETING_VERSION = <chosen-version>;
```

State the direction explicitly:

- If a build with the code's version is **already uploaded**, that binary is frozen —
  change the **listing field** to match it (page 06), do not touch the code.
- If no build is uploaded yet, set every target to one version in the code, which
  fixes the extensions too, then bump `CURRENT_PROJECT_VERSION` above the highest
  number already uploaded.

Pick one versioning scheme and keep it — `1.0.0` semver, next release `1.0.1`, not
`1.1`. Note the Android `versionName` if the project ships both and they disagree.

## Keywords (page 05)

Cosmetic, LOW. Offer the arithmetic, not a rewrite:

> Keywords use `<n>`/100 characters. `<word>` appears twice (once inside `<phrase>`),
> and `<category-word>` duplicates your category, which Apple already indexes.
> Removing those frees `<m>` characters for terms you do not otherwise rank on.

Do not propose specific replacement keywords — that is ASO, out of scope.

## The closing tally (Step 8)

Not a template to fill so much as a shape to hold to. Counts per outcome, then only
what remains open:

```
Done. <n> checks needed attention.
  verified fixed      <n>
  attested by you     <n>   (<what, and why no tool can confirm it>)
  pending Apple       <n>   (<what you are waiting on, e.g. trader verification>)
  pending your build  <n>   (<e.g. build 3 upload + processing>)
  skipped             <n>

Before you hit Submit:
  · <the one or two things still genuinely open>
```

No long report. Everything else was resolved in the loop.
