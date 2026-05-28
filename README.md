# Typing Challenge - iOS-ready Kivy package

Typing Challenge is a Python/Kivy typing game prepared as an iOS source package.
It is ready to push to GitHub and build on macOS with `kivy-ios`.

## Web app

The browser version lives in `web/` and deploys through GitHub Pages:

https://itzzdave20.github.io/Typing-Challenge/

## What is included

- Main app entry file: `main.py`
- Web app entry file: `web/index.html`
- App name: **Typing Challenge**
- iOS/mobile keyboard behavior: `Window.softinput_mode = "below_target"`
- Local account and leaderboard data save to the app sandbox via `user_data_dir`
- iOS icon assets in `ios_assets/`
- `buildozer.spec` metadata with Bundle ID `com.itzzdave20.typingchallenge`
- GitHub Actions syntax check in `.github/workflows/python-check.yml`
- GitHub Pages deploy workflow in `.github/workflows/pages.yml`
- Build notes and App Store checklist

## Run locally

```bash
python -m pip install -r requirements.txt
python main.py
```

## iOS build

This repository cannot produce a final App Store `.ipa` on Windows. Apple
publishing requires a Mac or cloud Mac, Xcode, app signing, and an Apple
Developer account.

1. Use this folder on a Mac.
2. Build the Kivy iOS project using `kivy-ios`.
3. Open the generated Xcode project.
4. Add the icon set from `ios_assets/AppIcon.appiconset`.
5. Configure signing with Bundle ID `com.itzzdave20.typingchallenge`.
6. Archive in Xcode.
7. Upload to App Store Connect.
8. Test with TestFlight.
9. Submit for App Review.

See `IOS_BUILD_STEPS.md` for the full command list.

## GitHub

After pushing to GitHub, the included workflow checks that `main.py` compiles.
The web app deploys to GitHub Pages automatically after pushes to `main`.
The iOS archive/upload step still needs Xcode signing credentials on macOS.
