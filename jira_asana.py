import requests
import getpass
import os
import json
import asana
from six import print_

"""
	Resources:
	https://docs.atlassian.com/jira-software/REST/cloud/#agile/1.0/board-getAllBoards
	https://github.com/Asana/python-asana/
	https://asana.readthedocs.io/en/latest/
"""

BASE_JIRA_URL = os.environ.get('BASE_JIRA_URL')
PROJECT_KEY = os.environ.get('JIRA_PROJECT_KEY')
JIRA_USERNAME = os.environ.get('JIRA_USERNAME')
JIRA_PASSWORD = os.environ.get('JIRA_PASSWORD')
JIRA_BOARD = False
ASANA_ACCESS_TOKEN = os.environ.get('ASANA_ACCESS_TOKEN')
ASANA_WORKSPACE = False
ASANA_PROJECT = False
JIRA_SPRINT = False
JIRA_TRANSITION_ID = False

# If set, JIRA_Task_USERNAME will get appended as asignee in this JQL
JQL = 'issuetype in (standardIssueTypes(), Epic, "New Feature", Story) AND status in (Open, "In Progress", Reopened, "To Do", "In Review")'


class JiraAsanaManager():
	def __init__(self):
		self.base_jira_url = BASE_JIRA_URL if BASE_JIRA_URL else raw_input("What is the URL you use to access JIRA (please include http/https and your port  i.e. http://jira.company.com:8080)  ")
		self.jira_username = JIRA_USERNAME if JIRA_USERNAME else raw_input("What is your JIRA username?")
		self.jira_password = JIRA_PASSWORD if JIRA_PASSWORD else getpass.getpass(prompt="What is your JIRA password?  ")
		self.asana_access_token = ASANA_ACCESS_TOKEN if ASANA_ACCESS_TOKEN else getpass.getpass(prompt="What is your Asana access token?  ")

		self.asana_client = asana.Client.access_token(self.asana_access_token)

		# These settings don't need to exist now - we'll ask the user for them later
		self.jira_project = PROJECT_KEY
		self.jira_board = JIRA_BOARD
		self.asana_project = ASANA_PROJECT
		self.asana_workspace = ASANA_WORKSPACE
		self.jira_sprint = JIRA_SPRINT
		self.jira_transition_id = JIRA_TRANSITION_ID
		self.jql = "%s AND assignee='%s'" % (JQL, self.jira_username)
		print self.jql

	def do_jira_request(self, url, data = "", request_type="get"):
		"""
			A helper method to do a JIRA GET or POST request
			Basically just attaches our Auth header to the request

			For POST, data should be a json-serializable obj
			For GET, data will be passed as URL params
		"""
		auth = (self.jira_username, self.jira_password)
		if request_type == "get":
			req = requests.get(url, auth=auth, params=data)
		elif request_type == "post":
			req = requests.post(url, auth=auth, json=data)

		if req.status_code == 200:
			return json.loads(req.text)
		elif req.status_code == 204:
			return True
		return False

	def user_select_option(self, message, options):
		"""
			Helper method that asks the user to choose from a list of options
			@param message: Text prompt for the user
			@param options: List of option dictionaries. Each option must have 'name' property
				One option will be returned
		"""
		option_lst = list(options)
		print_(message)
		for i, val in enumerate(option_lst):
			print_(i, ': ' + val['name'])
		index = int(input("Enter choice (default 0): ") or 0)
		return option_lst[index]

	def sync_jira_issues(self):
		"""
			This is where we actually sync JIRA issues and Asana tasks. Basically works like this:
			1) Gather all of our Asana tasks and JIRA issues
			2) For each Jira issue:
				- If it's completed and there's a matching JIRA issue, transition JIRA issue
				- If it's not completed and there's a matching JIRA issue, do nothing
			3) Delete the asana tasks that either don't have a matching JIRA issue or match a completed JIRA issue
		"""
		if not self.jira_board:
			self.get_jira_boards()
		if not self.jira_sprint:
			self.get_jira_sprints()
		if not self.asana_project:
			self.get_asana_projects()

		asana_tasks = [x for x in self.asana_client.tasks.find_all({ 'project': self.asana_project }, page_size=100, fields="completed,name,external")]
		get_issues_url = self.base_jira_url + "/rest/agile/latest/board/%s/sprint/%s/issue" % (self.jira_board, self.jira_sprint)
		response = self.do_jira_request(get_issues_url, data = { "jql": self.jql, "fields": "summary" })
		issues = [x for x in response['issues']]

		# Need to get transition ID if we don't already have it
		if not self.jira_transition_id:
			self.get_jira_transition_id(issues[0]['key'])

		keys = [task['name'].split()[0] for task in asana_tasks]
		filtered_tasks = {}
		for x, key in enumerate(keys):
			filtered_tasks[key] = {
				'id': asana_tasks[x]['id'],
				'name': asana_tasks[x]['name'],
				'completed': asana_tasks[x]['completed'],
				'matching_task': False
			}

		# Now we create an assana task for each JIRA issue. If task already exists, then we just set matching
		# task prop to true
		for issue in issues:
			key = issue['key']
			task_name = "%s %s" % (key, issue['fields']['summary'])
			task_link = "%s/browse/%s" % (self.base_jira_url, key)
			print "Task: %s" % (task_name)
			if key in filtered_tasks:
				asana_task = filtered_tasks[key]
				if asana_task['completed']:
					print "COMPLETING"
					# We need to finish this JIRA issue since it was finished in Asana
					# We will end up deleting this asana task, since we don't need it anymore
					transition_url = "%s/rest/api/2/issue/%s/transitions/" % (self.base_jira_url, key)
					data = {
						"transition": {
							"id": str(self.jira_transition_id)
						}
					}
					self.do_jira_request(transition_url, data=data, request_type="post")
				else:
					filtered_tasks[key]['matching_task'] = True
			else:
				# There is no asana task for this issue, let's create one
				self.asana_client.tasks.create_in_workspace(self.asana_workspace, {
					'name': task_name,
					'notes': task_link,
					'projects': [self.asana_project],
					'external': {"asana_id": key}
				})

		# We delete all the Asana tasks that don't match JIRA tasks
		for key, value in filtered_tasks.iteritems():
			if not value['matching_task']:
				print "Deleting Task %s" % (value['name'])
				self.asana_client.tasks.delete(value['id'])

	def get_jira_transition_id(self, example_issue_key):
		"""
			Let's the user choose what their "Done" transition is
			@param example_issue_key should be the key of an issue in the sprint we're syncing
		"""
		transitions_url = "%s/rest/api/latest/issue/%s/transitions" % (self.base_jira_url, example_issue_key)
		response_transitions = self.do_jira_request(transitions_url)
		self.jira_transition_id = self.user_select_option("What JIRA transition should we use for 'Done' issues?", response_transitions['transitions'])['id']
		return self.jira_transition_id

	def get_jira_boards(self):
		"""
			Returns a list of the JIRA boards in the current project
		"""
		get_boards_url = self.base_jira_url + "/rest/agile/latest/board/"
		response = self.do_jira_request(get_boards_url)
		boards = [x for x in response['values']]
		self.jira_board = self.user_select_option("Please select a JIRA Board", boards)['id']

	def get_jira_sprints(self):
		# Get active sprints for this board
		get_sprints_url = self.base_jira_url + "/rest/agile/latest/board/%s/sprint" % (self.jira_board)
		response = self.do_jira_request(get_sprints_url, data = { "state": "active", "fields": "summary"})
		sprints = [x for x in response['values']]
		if len(sprints) > 1:
			self.jira_sprint = self.user_select_option("Please select a JIRA sprint", sprints)['id']
		elif sprints:
			self.jira_sprint = sprints[0]['id']
		else:
			print "No Active JIRA Sprints"
		return self.jira_sprint

	def get_asana_projects(self):
		if not self.asana_workspace:
			workspaces = self.asana_client.workspaces.find_all()
			self.asana_workspace = self.user_select_option("Please choose an Asana workspace", workspaces)['id']
		if not self.asana_project:
			projects = self.asana_client.projects.find_all({'workspace': self.asana_workspace})
			self.asana_project = self.user_select_option("Please choose a project", projects)['id']
		return True

	def start(self):
		self.sync_jira_issues()

manager = JiraAsanaManager()
manager.start()