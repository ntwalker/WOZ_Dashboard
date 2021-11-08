# WOZ_Dashboard

This repository contains code for a dashboard to collect dialogue data in a Wizard-of-Oz (WOZ) setup. The first version of this dashboard is in two apps (woz_app.py and user_app.py), but the current (and better) app is run from the shared_app.py. I will likely remove the separate apps and rename the shared app to merely "app.py". The app is run using [Dash Devices](https://pypi.org/project/dash-devices/) so that the app is run as a shared resource.

## Usage
1. pip install requirements.txt

2. python shared_app.py

3. Open the app on the localhost and designated port.

4. When the app opens, you'll see the user screen. The user can click the "Record Message" button at the center of the screen to record a message to be displayed to the wizard.

5. To switch to wizard mode, type "wizard" into the text box at the top right and click the "admin" button.

6. In the wizard screen, there is a dropdown to select a response template. Once selected, any entities (e.g. \_Person\_, \_Time\_) in a template can be filled in by selecting entities from a table below. 

7. To display a table, select a Person, Group, or Room from the three dropdowns at the bottom and the calendar for that Person, Group or Room will be displayed. You can then click on entries in the table to add them to the list of entities to be filled in.

8. When you click entities to be filled in, they'll be added to a list shown below the Template dropdown. Hit the "compose" button to fill them into the template (added in the order selected without regard to type) and the composed response will display above the  "Send" button in the center.

9. Click the "Send" button to send (display) the response to the user.