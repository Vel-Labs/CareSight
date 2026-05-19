# Apple Automation Reference

## Role in CareSight

Apple platform automation provides familiar caregiver workflows:

- Shortcuts for alerts/journals
- FaceTime URL handoff
- Apple Notes/shared journal
- launchd startup behavior

## CareSight use

- Use Shortcuts as adapters, not core data storage.
- Use FaceTime as a handoff, not guaranteed emergency dispatch.
- Use launchd to make the base unit appliance-like.
- Use SQLite as source of truth.

## Sources

- [Apple Shortcuts CLI](https://support.apple.com/guide/shortcuts-mac/run-shortcuts-from-the-command-line-apd455c82f02/mac)
- [Apple FaceTime URL Scheme](https://developer.apple.com/library/archive/featuredarticles/iPhoneURLScheme_Reference/FacetimeLinks/FacetimeLinks.html)
- [Apple launchd Overview](https://support.apple.com/guide/terminal/script-management-with-launchd-apdc6c1077b-5d5d-4d35-9c19-60f2397b2369/mac)
- [Apple FaceTime Camera Selection](https://support.apple.com/guide/facetime/choose-a-camera-or-microphone-fctm26739220/mac)
