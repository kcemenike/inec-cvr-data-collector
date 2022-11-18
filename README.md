# Pull INEC data

This repo uses Selenium to get Voter information from [INEC's publicly available database](https://cvr.inecnigeria.org/voters_register/index). Tested to run at a speed of 8k-10k records per hour

## Required

- Python (3.8) at least
- [NordVPN](https://go.nordvpn.net/SH36L) (you'll find out why if you look at the code 😉)

## What to do

- Fork this git (obviously), then clone to your local computer
- Install [NordVPN](https://go.nordvpn.net/SH36L)
- Add the following information to your OS environment

  - EMAIL=anEmailYouRegisteredWithOnINECWebsite (the password should be secure@123)
  - STATE=TheStateYouWantToDump. This state MUST match the exact (including spacing and caps) on the INEC website
  - dbFile=TheSQLiteFileToWriteTo

  Example:

  - `EMAIL=a@b.com`
  - `STATE="CROSS RIVER"`
  - `dbFile=crossriver.db`

- Install requirements from requirements.txt
- Login to NordVPN on your computer
- Run the script

# Result

While the script is running, you should have intermittent network disconnections, blame it on the script 😂 there is nothing to worry about.  
You should get a huge DB file in your computer when the script finishes execution - a dump of voter information for your state of choice.

See second image for a snippet and a matching first screenshot from the portal

![UI snapshot](ui.png 'UI')
![Corresponding data](dt.png 'Data Dump')

# Bugs / Enhancements needed / Notes

- Looks like ward population column does not compute accurately. This is not a deal-breaker however, but may require improvement
- There is no logging (to improve performance, as the test machine was not a heavy duty rig, lol)
- There is a [compose file](docker-compose.yml) and a [Dockerfile](Dockerfile) if you want to dockerize the app, but you have to also add $NORD_USERNAME and $NORD_PASSWORD to env
