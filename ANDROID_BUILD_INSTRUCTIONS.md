# RingRing - Local APK Build Guide

## Prerequisites
- Android Studio installed
- Java JDK 17+
- Node.js 18+
- Your machine (Windows/Mac/Linux with proper architecture)

## Step-by-Step Build Instructions

### 1. Download Project
Download the `ringring-complete-project.tar.gz` and extract it.

### 2. Install Dependencies
```bash
cd ringring/frontend
yarn install
```

### 3. Build Frontend
```bash
yarn build
```

### 4. Sync with Capacitor
```bash
npx cap sync android
```

### 5. Open in Android Studio
```bash
npx cap open android
```

### 6. Build Signed APK

**In Android Studio:**

1. **Generate Keystore** (first time only):
   - Build → Generate Signed Bundle/APK
   - Create new keystore
   - **IMPORTANT**: Save keystore credentials securely!

2. **Build Signed APK**:
   - Build → Generate Signed Bundle/APK
   - Select APK
   - Choose your keystore
   - Select "release" build variant
   - Click Finish

3. **APK Location**:
   - `frontend/android/app/release/app-release.apk`

### 7. Test APK
```bash
adb install app-release.apk
```

## Alternative: GitHub Actions (Automated)

Create `.github/workflows/android-build.yml`:

```yaml
name: Build Android APK

on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node
      uses: actions/setup-node@v3
      with:
        node-version: 18
    
    - name: Setup Java
      uses: actions/setup-java@v3
      with:
        distribution: 'zulu'
        java-version: '17'
    
    - name: Install dependencies
      run: cd frontend && yarn install
    
    - name: Build frontend
      run: cd frontend && yarn build
    
    - name: Sync Capacitor
      run: cd frontend && npx cap sync android
    
    - name: Build APK
      run: cd frontend/android && ./gradlew assembleRelease
    
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-release
        path: frontend/android/app/build/outputs/apk/release/app-release.apk
```

This will build APK automatically on every push!

## Troubleshooting

### Issue: Gradle build fails
**Solution**: Update `android/build.gradle`:
```gradle
buildscript {
    dependencies {
        classpath 'com.android.tools.build:gradle:8.0.0'
    }
}
```

### Issue: SDK not found
**Solution**: Install Android SDK via Android Studio

### Issue: Build takes forever
**Solution**: Enable Gradle daemon in `gradle.properties`:
```
org.gradle.daemon=true
org.gradle.parallel=true
```
