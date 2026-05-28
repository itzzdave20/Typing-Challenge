# iOS build steps for Typing Challenge

## Requirements

- Mac or cloud Mac
- Xcode
- Apple Developer account
- App Store Connect access
- Python 3

## Build using kivy-ios

Open Terminal on macOS:

```bash
python3 -m pip install --upgrade pip
python3 -m pip install kivy-ios cython
toolchain build python3 kivy
toolchain create TypingChallenge /path/to/TypingChallenge
```

Then open the generated Xcode project:

```bash
open TypingChallenge-ios/TypingChallenge.xcodeproj
```

## Configure in Xcode

Set the following:

- Display Name: `Typing Challenge`
- Bundle Identifier: `com.itzzdave20.typingchallenge`
- Team: your Apple Developer team
- Version: `1.0.0`
- Build: `1`
- Deployment target: choose your target iOS version
- Orientation: Portrait
- App icon: use `ios_assets/AppIcon.appiconset`

## Upload

In Xcode:

```text
Product -> Archive -> Distribute App -> App Store Connect -> Upload
```

After Apple processes the build, test it through TestFlight before submitting
for App Review.

## GitHub deployment

Push this folder to `https://github.com/itzzdave20/Typing-Challenge.git`.
GitHub Actions will run a Python syntax check on every push. The App Store
upload still happens from Xcode because Apple requires signing credentials.
