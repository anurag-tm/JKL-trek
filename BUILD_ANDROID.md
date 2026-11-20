# Build the JKL Trekker Android app (APK)

The Android app is the same `web/` app packed inside a native shell (Capacitor).
Extra over the website: **GPS recording keeps running with the screen off or in
other apps**, and the app opens fully offline.

## You need

- Node.js 20 or newer (`node -v` to check)
- Android Studio (latest), with an Android SDK installed
- An Android phone with USB debugging on, or an emulator

## 1. First build

Open PowerShell in the `trek` folder:

```powershell
npm install
npx cap sync android
npx cap open android
```

Android Studio opens the `android` folder. Wait for "Gradle sync" to finish
(the first time takes a few minutes), connect your phone, and press **Run ▶**.

To get an APK file you can copy to any phone:
**Build → Build App Bundle(s) / APK(s) → Build APK(s)**, then click "locate".
The file is `android/app/build/outputs/apk/debug/app-debug.apk`.
On the phone, allow "Install unknown apps" for your file manager once.

## 2. After you change the app

Whenever you edit anything in `web/`:

```powershell
npx cap sync android
```

then press Run again in Android Studio.

## 3. Phone settings for reliable background tracking

- Allow location **"Allow all the time"** or at least "While using the app"
  (the recording notification keeps the app counted as "in use").
- Allow notifications (Android 13+ asks on first start). The notification
  "JKL Trekker is recording your track" must be visible while recording.
- Xiaomi / Redmi / POCO, Vivo, Oppo, Realme, OnePlus, Samsung: set
  Settings → Apps → JKL Trekker → Battery → **No restrictions / Unrestricted**.
  Otherwise the phone may stop the app after some minutes.

## 4. Optional: Google sign-in inside the app

Google does not allow its sign-in page inside apps' web views, so the app uses
a native sign-in plugin. It needs your Firebase project to know the app:

1. Get the SHA-1 of your debug key: in Android Studio open the Gradle panel →
   `android → app → Tasks → android → signingReport` (or run
   `cd android; .\gradlew signingReport`). Copy the **SHA1** of variant `debug`.
2. Firebase Console → Project settings → **Add app → Android**:
   package name `com.jktrek.explorer`, paste the SHA-1, register.
3. Download **google-services.json** and put it in `android/app/`.
4. Install the plugin and sync:

   ```powershell
   npm install @capacitor-firebase/authentication firebase
   npx cap sync android
   ```

5. Run the app again. "Sign in with Google" now opens the native Google account picker.

Do not install the plugin without `google-services.json`: the app would crash on start.

## Troubleshooting

| Problem | Fix |
|---|---|
| Gradle asks for a newer JDK | Android Studio → Settings → Build Tools → Gradle → Gradle JDK: pick the bundled JBR (21) |
| "SDK location not found" | Open the `android` folder once in Android Studio; it creates `local.properties` |
| Recording stops after a few minutes | Battery setting → Unrestricted (step 3) |
| Map is blank offline | Map tiles are cached only for areas you viewed while online. Browse your trek area before going |
