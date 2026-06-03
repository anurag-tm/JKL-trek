# Android Wrapper for JK Trek Explorer

This is an Android WebView wrapper for the JK Trek Explorer web app.

## How to use

1. Open `android-app` in Android Studio.
2. If Android Studio asks to install missing components, allow it.
3. Open `app/src/main/java/com/jktrek/explorer/MainActivity.kt` and update the `publishedUrl` constant.
4. Replace `webAppUrl` in `MainActivity.kt` with your published GitHub Pages URL when ready.

### Local development

To test on an Android emulator:
- Start the local web server from the project folder:
  ```powershell
  cd "C:\Users\anura\Downloads\trek"
  python -m http.server 8000
  ```
- In the Android app, use:
  ```kotlin
  private val webAppUrl = "http://10.0.2.2:8000"
  ```

### Publish URL

After the site is live, update `MainActivity.kt` to use:
```kotlin
private val webAppUrl = "https://YOUR_GITHUB_USERNAME.github.io/your-repo-name"
```

## Permissions

This app requests:
- `INTERNET`
- `ACCESS_FINE_LOCATION`
- `ACCESS_COARSE_LOCATION`

The WebView is configured for geolocation, so the app can use the GPS features of your web page.
