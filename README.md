# AmpelSlackCosmology
Explore automatic candidate selection based on the Slack output



Requires widgets in the jupyter notebook. If this is run through environments parts of the installation has to go through base/root. Look at
https://ipywidgets.readthedocs.io/en/stable/user_install.htmlstable/user_install.html


Also requires a recent version of marshal tools. Is the public one synced?


# Daily SEDM inspector
- Go through SEDM data and make sure types are entered into the marshal



# Daily scanner routines

- After 15pm download both csv files sent to the ztf_cosmosn channel
- Sync the AmpelSlackCosmo git (since last day)
- Configure ztfcosmology_scanning script parameters and run
- Select well-behaved SN-like objects not suitable for RCF for saving
- Take action if any sne were not sent to scanning page or saved as expected
- Add your log to the git and push this (possibly together with new candids)


# Daily trigger routines

- To be run after scanner has uploaded data
- Scripts starts with downloading all untyped lightcurves and fit them.
  This takes a while.
- Inspect fits and select whether RCF should be alerted or we should trigger
- Follow links and trigger SEDM obs
- Push updated logs and sne_following for common use!

# SNIFS scheduler, day prior to SNIFS night
- Inspect sne_following for untyped objects. Create SNIFS schedule

# SNIFS inspector, day after each SNIFS night
- Inspect SNIFS results and update Marshal types

# LCO scheduler at 4th, 11th and 22th
- Inspect sne_following for untyped objects. Trigger LCO

# LCO inspector, looking at LCO repository
- Inspect LCO results and update Marshal types




# General comments:
- Further comments can always be added at the marshal page. Include the OctIa tag.

