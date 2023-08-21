# RotMG-QuestInfographicMaker
The RotMG Quest Infographic Maker generates infographics from item IDs given in Realm of the Mad God.

# Requirements
An internet connection is required to update/download files.

Intended for Windows.

The infographic maker is case-sensitive.

# Updating
The maker downloads assets from https://assets.muledump.com/sheets/ . Turning Auto Update on will update sprites each time the app is opened. You can also update manually by simply pressing update. If you have are modifying custom xml and do not need to download all sheets, you can use the Build JSON Only button to generate a new master.json from the current xml.

# Config Options
config.json contains several options that the user can change including the upscale value for the render (should only be modified to avoid artifacts), the sizes for large and small icons (large icons are shown if there are only 2 or less items on one side of the quest), the size of items contained inside blueprints, and the quantity font size. Most style options have not been implemented yet. It is possible to add a frequency option in the config given that an icon for it exists (with the same filename, without whitespace). The app must be re-opened for config changes to take effect.

# Custom Items
Custom items can be added by using the custom files in the xml and sheets folders (the json file is an intermediate and generated from the xml file). Follow the format of the examples in custom.xml and paste your sprites into the appropriate png file.

# Quantity Numbers for Tokens
Any item ending with x followed by a number (with an optional space between) will have that number drawn onto its image. This is assuming that the token followed by x## exists in a dictionary

# Discord
Join if you have any feedback
https://discord.gg/mdnVtbhuhM
