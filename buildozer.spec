[app]
title = Typing Challenge
package.name = typingchallenge
package.domain = com.itzzdave20
source.dir = .
source.include_exts = py,png,jpg,jpeg,kv,json,mp3,wav,ogg
version = 1.0.0
requirements = python3,kivy
orientation = portrait
fullscreen = 0
ios.kivy_ios_url = https://github.com/kivy/kivy-ios
ios.kivy_ios_branch = master
ios.codesign.allowed = false

# Android values are kept only for Buildozer compatibility.
android.permissions =

# iOS builds still require macOS + Xcode + kivy-ios.
# After creating the Xcode project, set Signing Team, icons, screenshots,
# privacy details, then Archive. Bundle ID: com.itzzdave20.typingchallenge
