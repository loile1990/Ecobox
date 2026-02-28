Android UDP Client Application

This application sends the phone’s state to a server via the UDP protocol.

To use the application:

Enable Developer Mode:
    - Go to Settings > About phone, then tap “OS Version” 7 times.

In Developer Options:
    - Enable USB debugging.
    - Enable installation via USB (if available).

Connect the phone to Ecobox:
    - Disable private MAC addressing.
    - Use the phone’s real MAC address.
    - Set the phone’s MAC address as static in the file networkutils.kt.

Connect to the PC and Android Studio:
    - Connect the phone to the computer via USB.
    - Open Android Studio and load the application project.
    - The phone should be detected automatically.
    - Open an integrated terminal in Android Studio (bottom left of the screen).

Application installation:
    - Clear ADB logs:
        adb logcat -c

    - Rebuild the project:
        ./gradlew clean assembleDebug

    - Install the application with the necessary permissions:
        adb install -g app/build/outputs/apk/debug/app-debug.apk

    - Disable battery optimization for this application and others:
        adb shell dumpsys deviceidle whitelist +fr.lip.hownet.networkmonitor
        adb shell cmd appops set fr.lip.hownet.networkmonitor RUN_IN_BACKGROUND allow
        adb shell cmd appops set fr.lip.hownet.networkmonitor RUN_ANY_IN_BACKGROUND allow
        adb shell cmd appops set fr.lip.hownet.networkmonitor START_FOREGROUND allow
        adb shell cmd appops set fr.lip.hownet.networkmonitor SYSTEM_ALERT_WINDOW allow

    - Start the application service:
        adb shell am start-foreground-service -n fr.lip.hownet.networkmonitor/.services.ExperimentService

    - Check that the service is running:
        adb logcat -s ExperimentService

      You should also see a persistent notification on the phone indicating that the service is active.

    - Monitor the application’s behavior from the system side (useful for troubleshooting):
        adb logcat -d | grep fr.lip.hownet.networkmonitor

Some phones do not allow applications to run automatically after a restart. To ensure proper operation:
    - Allow NetworkMonitor to run in the background and at startup.
    - This option is usually found in:
        Settings → Battery → Auto-launch / Power management
        or Settings → Apps → [NetworkMonitor] → Auto-launch / Background usage

    It is essential to enable these options; otherwise, the application will not restart after reboot. On some models, this happens automatically, but not on all.

Testing after reboot:
    - Restart the phone.
    - Unlock it.
    - Wait 4 to 5 minutes.
    - If the notification appears or the following command shows logs:
        adb logcat -s ExperimentService

      Then the application is working correctly ✅

If the application does not work after reboot:
    - Uninstall it: adb uninstall fr.lip.hownet.networkmonitor
    - Repeat the installation from the beginning.

-----------------------------------------------------------------
Note: During the day, Android may automatically close the application for optimization reasons.
In this case, a simple phone restart is usually enough to restart the service.
Remember to check from time to time that everything is working properly!
