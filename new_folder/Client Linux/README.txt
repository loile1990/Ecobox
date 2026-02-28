Linux UDP Client

This file contains a script to create a UDP client on Linux as a startup service, with periodic checks of the user’s screen state.

------------------------------------------------------------------------------------------------------------------------------------
Follow the instructions below to use it:

- Install Python
- Place the script anywhere you like on your system. For example, you can copy it to a folder such as /home/your_user/ or the desktop
- Grant execution permissions with:
chmod +x setup_udpclient.sh

- Run the script directly WITHOUT SUDO — this is important — using the command:
./setup_udpclient.sh

------------------------------------------------------------------------------------------------------------------------------------

If you want to remove everything the script created and delete the services, then:
chmod +x remove_udpclient.sh
./remove_udpclient.sh
