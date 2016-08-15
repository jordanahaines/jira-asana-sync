# Jira Asana Sync
This is a python script that creates Asana tasks for Jira issues. More specifically, this script will retrieve Jira tasks assigned to a specific user in a specific sprint, and will create an Asana task in a specified project for each Jira issue. When Asana tasks are completed, their corresponding Jira task will be completed. Asana tasks in the project that do not have a corresponding incomplete Jira task will be deleted.

This script _only_ works to copy Jira issues out of a specific sprint into a specific Asana project. You can't currently copy Jira issues at large, they must come from a single sprint. If this is a big problem for you, and you tweet at me (@JordanAHaines) then I can probably code up a solution to extract issues from some other taxonomy.

## To get started:

1. Clone or download this repository
2. Install [python-asana](https://github.com/Asana/python-asana/) and [six](https://pypi.python.org/pypi/six). (Use commands  `pip install asana` and `pip install six`)
3. Create an Asana Personal Access Token as described in [this article](https://asana.com/guide/help/api/api)
4. Determine your JIRA URL, Username and Password
5. Run jira_asana.py (from this repo) with command  `python jira_asana.py`

## Settings
When you run the jira_asana.py script, you will be prompted for a number of pieces of information, including your Jira/Asana credentials, desired Jira board/sprint and desired Asana workspace/project. All of these settings also appear at the top of the python script, so you can just set them there. These settings are listed below.

All of the settings can be set while running the script, by saving them in the script's pythong file or by setting an environmental variable with the same name. (i.e. environmental variable "JIRA_USERNAME" will be used for JIRA_USERNAME in the script.)

I've tried to clearly note the settings that you may want to choose _while_ running the script. These hard to find settings represent unique identifiers that the script will help you find. For example, the script will return all of the named Jira boards you have and ask you to choose one. Finding the unique ID of a single Jira board is kind of difficult and not something I want to write up for you.

- BASE_JIRA_URL: The URL (including http or https) of your Jira instance. DO include the port (if not 80 or 443). DO NOT end this with a "/". Example: http://jira.company.com:8080
- PROJECT_KEY: Your Jira project key (this is usually all caps)
- JIRA_USERNAME: Your Jira username (the script will only sync Jira issues that are assigned to the user with this username)
- JIRA_PASSWORD: The password for the Jira user with JIRA_USERNAME
- JIRA_BOARD: This is something you may want to choose after running the script, but it's the ID of the Jira board you want to select tasks from.
- ASANA_ACCESS_TOKEN: The unique personal access token used to access Asana. If you need help getting an Asana access token, check out [this article](https://asana.com/guide/help/api/api)
- ASANA_WORKSPACE: This is also something you may want to choose while running the script. This is the ID of the Asana workspace your desired Asana project is in.
- ASANA_PROJECT: This is also something you may want to choose while running the script. This is the ID of the Asana workspace your desired Asana project is in.
- JIRA_SPRINT: This is also something you may want to choose while running the script. This is the unique identifier for the Jira sprint you will sync issues _from_. 
- JIRA_TRANSITION_ID: Last one, but I hate to say that this is also something best chosen while running the script. This represents the ID of the "DONE" status in Jira.



