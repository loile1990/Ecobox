Windows UDP Client

This file contains a script to create a UDP client on Windows, with periodic checks of the user’s screen state.

Follow the instructions below to use it:

- Install Python, making sure to check the "Add Python to PATH" option at the end of the installation, or manually add the Python path to your environment variables.

- Install pywin32 with:
pip install pywin32

- Press Windows + R

- Type shell:startup and press Enter

- Place the script windows_udpclient.pyw in the folder that opens, making sure to keep the .pyw extension.

- Restart your computer.

----------------------------------------------------------------------------------------------------------------------------------------------------
This script generates a log file in the same folder. This file is useful to verify if the script runs correctly at startup.
