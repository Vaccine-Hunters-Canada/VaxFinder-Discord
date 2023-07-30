**VaxFinder - Discord Bot**

Discord bot which uses the VaxFinder API to display appointments via slash commands.

Setup:

* `pip install requirements.txt`
* In any Python environment: `keyring.set_password("VaxFinderDiscord", "BotToken", [your Discord bot token here])`
* `python3 bot.py`

This bot uses the **Vaccine Ontario** database for vaccination appointments in Ontario, and the **Find Your Immunization** database for all other provinces.

## Usage
The `/find [postal] [dose]` command will display the single best appointment based on the first 3 digits of the postal code given, which has the dose number specified available. `/findall [postal] [dose]` will send a *direct message* with a list of curated vaccination appointments.

## Screenshots

![image](https://github.com/Vaccine-Hunters-Canada/VaxFinder-Discord/assets/14363662/b1d64c01-664e-4952-a5e8-ca03acd6d40b)
![image](https://github.com/Vaccine-Hunters-Canada/VaxFinder-Discord/assets/14363662/a5da021f-dcbb-4b80-a755-de0fde7a8990)
