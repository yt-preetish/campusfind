# CampusFind Android App - Setup and Build Guide

## Prerequisites

### Required Software
1. **Java JDK 17 or higher** (JDK 21 recommended for Android API 36)
   - Download from: https://adoptium.net/ or https://www.oracle.com/java/technologies/downloads/
   - Install and set JAVA_HOME environment variable
   - Add Java bin directory to PATH

2. **Android Studio** (includes Android SDK and build tools)
   - Download from: https://developer.android.com/studio
   - Install with Android SDK Platform-Tools
   - Install Android SDK Build-Tools 34.0.0 or higher
   - Install Android SDK Platform API 36

3. **Node.js** (already installed for Capacitor)
   - Version 18 or higher recommended

### Environment Variables
Set the following environment variables:
```bash
JAVA_HOME=C:\Program Files\Eclipse Adoptium\jdk-21.x.x-hotspot
ANDROID_HOME=C:\Users\YourUsername\AppData\Local\Android\Sdk
```

Add to PATH:
```bash
%JAVA_HOME%\bin
%ANDROID_HOME%\platform-tools
%ANDROID_HOME%\emulator
```

## Project Structure

```
mobile/
├── android/              # Android native project
│   ├── app/
│   │   ├── build.gradle
│   │   └── src/main/
│   │       ├── AndroidManifest.xml
│   │       ├── java/com/campusfind/app/
│   │       │   └── MainActivity.java
│   │       └── res/
│   │           ├── drawable/
│   │           ├── mipmap-*/      # App icons
│   │           └── values/
│   │               ├── colors.xml
│   │               └── styles.xml
│   ├── build.gradle
│   └── variables.gradle
├── capacitor.config.json
├── package.json
└── www/
    └── index.html
```

## Configuration Summary

### App Details
- **App Name**: CampusFind
- **Package ID**: com.campusfind.app
- **Production URL**: https://campusfind-1-yrgg.onrender.com
- **Min SDK**: 23 (Android 6.0)
- **Target SDK**: 36 (Android 16)
- **Compile SDK**: 36

### Features Configured
- ✅ HTTPS connection to production server
- ✅ Session/cookie support
- ✅ Form submissions
- ✅ File uploads (camera, gallery)
- ✅ Location access (for maps)
- ✅ Back button handling
- ✅ External link handling
- ✅ Splash screen with CampusFind branding
- ✅ Status/navigation bar theming
- ✅ Deep linking (campusfind-1-yrgg.onrender.com)

### Permissions
- INTERNET
- ACCESS_NETWORK_STATE
- CAMERA
- READ_EXTERNAL_STORAGE
- WRITE_EXTERNAL_STORAGE
- READ_MEDIA_IMAGES
- ACCESS_FINE_LOCATION
- ACCESS_COARSE_LOCATION

## Building the App

### Option 1: Using Android Studio (Recommended)

1. **Open the project in Android Studio**
   ```bash
   # From the mobile directory
   android
   ```
   Or open Android Studio → File → Open → Select `mobile/android` folder

2. **Sync Gradle**
   - Android Studio will automatically sync Gradle
   - Wait for dependencies to download

3. **Build Debug APK**
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - APK will be in: `android/app/build/outputs/apk/debug/app-debug.apk`

4. **Run on Physical Device**
   - Enable USB Debugging on your phone
   - Connect phone via USB
   - Click Run button in Android Studio or use:
   ```bash
   cd android
   gradlew.bat installDebug
   ```

### Option 2: Using Command Line

1. **Open terminal in mobile/android directory**
   ```bash
   cd mobile/android
   ```

2. **Build Debug APK**
   ```bash
   gradlew.bat assembleDebug
   ```

3. **Install on connected device**
   ```bash
   gradlew.bat installDebug
   ```

### Option 3: Using Capacitor CLI

```bash
cd mobile
npm run build
npx cap sync android
npx cap open android
```

## Generating Signed AAB for Google Play

### Step 1: Generate Keystore

```bash
keytool -genkey -v -keystore campusfind-release.keystore -alias campusfind -keyalg RSA -keysize 2048 -validity 10000
```

Store the keystore file securely. **DO NOT commit it to Git.**

### Step 2: Configure Signing in build.gradle

Edit `android/app/build.gradle`:

```gradle
android {
    signingConfigs {
        release {
            storeFile file('campusfind-release.keystore')
            storePassword 'YOUR_STORE_PASSWORD'
            keyAlias 'campusfind'
            keyPassword 'YOUR_KEY_PASSWORD'
        }
    }
    buildTypes {
        release {
            signingConfig signingConfigs.release
            minifyEnabled true
            proguardFiles getDefaultProguardFile('proguard-android.txt'), 'proguard-rules.pro'
        }
    }
}
```

### Step 3: Build Release Bundle

```bash
cd android
gradlew.bat bundleRelease
```

The AAB file will be in: `android/app/build/outputs/bundle/release/app-release.aab`

### Step 4: Upload to Google Play Console

1. Go to https://play.google.com/console
2. Create new app or select existing
3. Upload the AAB file
4. Complete store listing
5. Submit for review

## Testing Checklist

Before deploying to Google Play, test:

- [ ] App launches successfully
- [ ] Production website loads correctly
- [ ] Login works
- [ ] Registration works
- [ ] Dashboard loads
- [ ] Report lost/found forms work
- [ ] Camera upload works
- [ ] Gallery upload works
- [ ] Map displays correctly
- [ ] Back button navigates correctly
- [ ] External links open in browser
- [ ] Internal links stay in app
- [ ] Session persists across app restarts
- [ ] Notifications work (if implemented)

## Troubleshooting

### JAVA_HOME not set
```bash
# Set JAVA_HOME temporarily (PowerShell)
$env:JAVA_HOME="C:\Program Files\Eclipse Adoptium\jdk-21.x.x-hotspot"
$env:PATH="$env:JAVA_HOME\bin;$env:PATH"
```

### Gradle sync fails
- Check internet connection
- Verify Android SDK is installed
- Update Android SDK in Android Studio SDK Manager

### Build fails with SDK errors
- Install required SDK platforms in Android Studio
- Update build tools to latest version

### App crashes on launch
- Check capacitor.config.json URL
- Verify production server is accessible
- Check Android logcat for errors

## Files Created/Modified

### Created Files
- `mobile/index.html` - Web entry point
- `mobile/package.json` - Node dependencies
- `mobile/capacitor.config.json` - Capacitor configuration
- `mobile/android/` - Entire Android project (by Capacitor)
- `mobile/android/app/src/main/res/drawable/splash.xml` - Splash screen drawable
- `mobile/ANDROID_SETUP.md` - This file

### Modified Files
- `mobile/android/app/src/main/AndroidManifest.xml` - Added permissions and deep linking
- `mobile/android/app/src/main/java/com/campusfind/app/MainActivity.java` - Added back button handling
- `mobile/android/variables.gradle` - Updated SDK versions to API 36
- `mobile/android/app/src/main/res/values/colors.xml` - Added CampusFind colors
- `mobile/android/app/src/main/res/values/styles.xml` - Added CampusFind theming

## Next Steps

1. Install Java JDK and set JAVA_HOME
2. Install Android Studio
3. Open project in Android Studio
4. Build and test debug APK
5. Generate release keystore
6. Build release AAB
7. Upload to Google Play Console
8. Complete store listing and submit for review

## Notes

- The Flask backend remains unchanged and continues running on Render
- No API keys are stored in the Android app
- The app uses the production URL directly
- All authentication happens server-side
- Database operations are handled by the Flask backend
