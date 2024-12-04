from __future__ import print_function
import requests
from pprint import pprint
import pandas as pd
import json
from datetime import datetime
from treelib import Tree
import pygraphviz as pgv

### Credits ###
"""
This SysML v2 API Scripts library aims to faciliate the creation and/or modification of models using the API services. 
Fundamentally, it wraps the API calls with simple function calls, whcih are methods for initialized Projects (from Project class below).
For more information, please refer to the project report. 

Author: Eliezer Zavala Gonzalez
Email: ezavala19@gatech.edu
Date: December 3rd, 2024
""" 

'''
Things to Note:
1. There are some edge cases that are not accounted for. For example, a requirement can only be assigned 1 owner, or tied to 1 part, at a time. 
2. When updating elements (parts, atts, or reqs), UPDATING does not ACCOUNT for duplicates. That is, if you have more than 1 part with the same name,
it will most likely update the first one it finds. The option of specifying (very likely with the element id or current owner name) needs to be implemented
'''


########################################## Initialize the API ##################################################

#host = "<specify protocol://host:port of the server that is a provider of the SysML v2 REST/HTTP API"
host = "http://localhost:9000/" 

# Change Host - changes the host location to 
def change_host(new_host):
    if type(new_host) is not str:
        raise ValueError("New host name needs to be a string in format: 'http://localhost:9000/'")
    else:
        global host
        host = new_host

# View Host - print the current host name
def view_host():
    print(host)

#Get Projects - returns a dataFrame of all projects within the host
def projects_list():
    projects_url = f"{host}/projects" 
    projects_response = requests.get(projects_url)

    if projects_response.status_code == 200:
        projects = projects_response.json()
        projects_data = list(map(lambda b: {'Project Name':b['name'], 'Project ID':b['@id']}, projects))
        df_projects = pd.DataFrame.from_records(projects_data)
        # return df_projects
        if len(projects_data) > 0:
            return df_projects.sort_values(by='Project Name')
        else:
            return df_projects
    else:
        raise ValueError("Problem in fetching projects")
    

#Get Projects - returns a dataFrame of all projects within the host
def projects_names_list():
    projects_url = f"{host}/projects" 
    projects_response = requests.get(projects_url)

    if projects_response.status_code == 200:
        projects = projects_response.json()
        projects_data = list(map(lambda b: {'Project Name':b['name'], 'Project ID':b['@id']}, projects))
        df_projects = pd.DataFrame.from_records(projects_data)
        # return df_projects
        if len(projects_data) > 0:
            return df_projects.sort_values(by='Project Name')["Project Name"]
        else:
            return df_projects["Project Name"]
    else:
        raise ValueError("Problem in fetching projects")
    

#Get Projects - returns a dataFrame of all projects within the host
def projects_IDs_list():
    projects_url = f"{host}/projects" 
    projects_response = requests.get(projects_url)

    if projects_response.status_code == 200:
        projects = projects_response.json()
        projects_data = list(map(lambda b: {'Project Name':b['name'], 'Project ID':b['@id']}, projects))
        df_projects = pd.DataFrame.from_records(projects_data)
        # return df_projects
        if len(projects_data) > 0:
            return df_projects.sort_values(by='Project Name')["Project ID"]
        else:
            return df_projects["Project ID"]
    else:
        raise ValueError("Problem in fetching projects")


# Select Project - select and initialize a project you are trying to work with
# When you initialize the project, certain variables will be automatically defined. Please refer to the project report for more info.
class Project:
    
    # Initialize the project and allocate its defining variables. You have the option of providing one or more of the inputs, ideally in order of appearance.
    # To specifically initialize a project, use the project ID rather than name or index (e.g., have 2 projects with same name; differentiate by their ID)
    def __init__(self, name=None, id=None, index=None):
        self.index = index
        self.name = name
        self.id = id
        self.all_previous_commits = []
        
        #################### Initialize the Tree Specific to this Project Project initialization ########################

        self.tree = Tree()

        #################################################################################################################
        ################################################# __INIT__ SECTION ##############################################
        #################################################################################################################


        ######################################## __INIT__ PROJECT DEFINITION VARIABLES ##################################
           
        #region __INIT__ PROJECT DEFINITION VARIABLES
        
        if self.index != None: # given index of project in projects_list(), set self.name and self.id
            df_projects = projects_list()
            try:
                self.name = df_projects.iloc[self.index, 0]
                self.id = df_projects.iloc[self.index, 1]
            except:
                ValueError("Index does not exist or is out of range.")

        elif self.name != None: # given name of project in projects_list(), set self.index and self.id
            df_projects = projects_list()
            try:
                self.index = df_projects.index[df_projects["Project Name"] == self.name].to_list()[0]
                self.id = df_projects.loc[df_projects["Project Name"] == self.name, "Project ID"].values[0]
            except:
                raise ValueError("Project does not exist or name has typo.")

        elif self.id != None: # given id of project in projects_list(), set self.index and self.name
            df_projects = projects_list()
            try:
                self.index = df_projects.index[df_projects["Project ID"] == self.id].to_list()[0]
                self.name = df_projects.loc[df_projects["Project ID"] == self.id, "Project Name"].values[0]
            except:
                raise ValueError("Project ID does not exist or has typo.")       

        #endregion
        
        #################################################################################################################


        ############################################ __INIT__ COMMITS ##################################################

        #region __INIT__ COMMITS
        
        # Get All Commits and automatically select the latest commit as the current commit
        # Note: if new project or no commits have been done, this will error out because it will show as "[]"
        commits_url = f"{host}/projects/{self.id}/commits" 
        commits_response = requests.get(commits_url)

        if commits_response.status_code == 200:
            commits = commits_response.json()

            commits_data = list(map(lambda b: {'Commit ID':b['@id'], "Commit Created":b['created']}, commits))
        
            df_commits = pd.DataFrame.from_records(commits_data)

            df_commits['Commit Created'] = pd.to_datetime(df_commits['Commit Created'])  # Convert to datetime
            df_commits = df_commits.sort_values(by='Commit Created', ascending=False)    # Sort from newest to oldest

            # Reset the index if desired
            df_commits = df_commits.reset_index(drop=True)

            self.all_commits = df_commits
            try:
                self.latest_commit = df_commits.iloc[0]["Commit ID"]
                self.current_commit = self.latest_commit

            except:
                raise ValueError("No commits found in project.")

        else:
            pprint(f"Status Code: {commits_response.status_code}. Problem in fetching commits.")
            pprint(commits_response)

        #endregion

        #################################################################################################################


        ############################################ __INIT__ ELEMENTS ##################################################

        #region ELEMENTS

        # Get All Elements of selected project regardless if its a part, attribute, or requirement. Their respective "Type"s are PartUsage, AttributeUsage, and RequirementUsage 
        # Note: if new project or no commits have been done, this will error out because it will show as "[]"
        elements_url = f"{host}/projects/{self.id}/commits/{self.current_commit}/elements" 
        response = requests.get(elements_url)
        
        if response.status_code == 200:
            elements_data = response.json() #type is LIST
            #type(response.json()[0]) IS DICT!
            # elements_name_to_print = elements_data['name'] if elements_data['name'] else 'N/A'
            
            df_elements = pd.DataFrame([{"name": element["name"], "id": element["@id"], "type": element["@type"], "owner_id": element["ownedElement"]} for element in elements_data])
            
            try:
                self.all_elements = df_elements.sort_values("name").sort_values("type", ascending=False).reset_index(drop=True)
                self.elements_names = df_elements["name"]
                self.elements_ids = df_elements["id"]
                self.elements_types = df_elements["type"]
            except:
                raise ValueError("No elements found in current commit.")

        else:
            pprint(f"Problem in fetching branches of {self.name} {self.id}")
            pprint(commits_response)

        #endregion

        #################################################################################################################
        

        ############################################ __INIT__ ATTRIBUTES ################################################
        
        #region ATTRIBUTES

        # Gets all elements that are an attribute (AttributeUsage class)
        
        elements_url = f"{host}/projects/{self.id}/commits/{self.current_commit}/elements" 
        response = requests.get(elements_url)
        
        if response.status_code == 200:
            elements_data = response.json()
            
            try:
                df_attributes = pd.DataFrame([{"name": element["name"], "id": element["@id"], "owner_id": element["ownedElement"][0]["@id"]} for element in elements_data if element["@type"]=="AttributeUsage"])

                self.all_attributes = df_attributes

                # now for every attribute found, add it to the dictionary of the owner; create and add the dictionary to the list
                self.elements_attributes = {}

                for index, attribute in df_attributes.iterrows(): 

                    att_name, att_value = attribute["name"].split(":")
                    owner_name = df_elements.loc[df_elements["id"] == attribute["owner_id"], "name"].values[0]
                    if owner_name not in self.elements_attributes:
                        self.elements_attributes[owner_name] = {att_name: att_value}

                    else: # a owner dictionary already exists within the list, so add into the dict
                        self.elements_attributes[owner_name].update({att_name: att_value})

            except:
                print("No attributes found.")

        #endregion

        #################################################################################################################

        ############################################ __INIT__ REQUIREMENTS ##############################################

        #region REQUIREMENTS

        # Get All requirements in the initialized project (RequirementUsage class)
        # Note: if new project or no commits have been done, this will error out because it will show as "[]"
        elements_url = f"{host}/projects/{self.id}/commits/{self.current_commit}/elements" 
        response = requests.get(elements_url)
        
        if response.status_code == 200:
            elements_data = response.json() #type is LIST
            
            df_reqs = pd.DataFrame([{"name": element["name"], "desc": element["text"], "id": element["@id"], "type": element["@type"], "owner_id": element["ownedElement"]} for element in elements_data if element["@type"]=="RequirementUsage"])
            
            try:
                self.all_reqs = df_reqs.sort_values("name")
            except:
                print("No requirements found in current commit.")

        else:
            pprint(f"Problem in fetching branches of {self.name} {self.id}")
            pprint(commits_response)

        #endregion

        #################################################################################################################

        ############################################### __INIT__ TREE ###################################################

        #region TREE

        # Create a tree using the info in the API
        # create a for loop that looks at each element that is NOT a Comment and find the owner in the ownedElement field. Create a node for each.

        ### NOTE ###
        # Here is where you would delete all elements if the Project.delete_elements() function gives trouble. This is caused by the Tree finding more than
        # one "root" element. That is, an elememnt without a parent. Thus, the problem lied in the fact that if a parent element was deleted, all child elements
        # would still exist and thus convert to having no parent (orphans), i.e., a root element. Treelib can only have 1 root element, hence the error. This, however, should
        # be fixed. I did not have the time to test it. 

        # If the problem persist, comment the code which has the "UNCOMMENT" word above, initialize the project to delete the elements, and then uncomment
        # the code with the "UNCOMMENT" word above. This deletes those "orphans" in the model and thus Treelib will look at a corrected model when the code
        # is uncommented.
        
        # print(self.all_elements)
        # self.delete_element()
        # self.delete_requirement()
        # self.remove_attribute()

        ##########

        _df_elements_not_comment = df_elements[df_elements["type"]!="Comment"]

        ### UNCOMMENT ###
        for index, element in _df_elements_not_comment.iterrows():
            node_name = element["name"]
            node_id = element["id"]
            parent_name = None
            node_type = element["type"]
            # Extract parent_name from owner_id if available
            if element["owner_id"]:
                parent_id = element["owner_id"][0]["@id"]
                parent_row = _df_elements_not_comment[_df_elements_not_comment["id"] == parent_id]
                if not parent_row.empty:
                    parent_name = parent_row.iloc[0]["name"]
            # Add the node and its parents
            self.add_node_with_parents(self.tree, _df_elements_not_comment, node_name, node_id, parent_name, node_type)
        
        dot = self.generate_dot(self.tree)
        # Visualize with pygraphviz
        G = pgv.AGraph(string=dot)
        G.layout(prog='dot')
        G.draw('tree.png')  # Saves as tree.png

        #endregion

        #################################################################################################################

            

    #################################################################################################################
    ######################################### PROJECT CLASS METHODS SECTION #########################################
    #################################################################################################################

    ### ELEMENTS ###
    # Creates partUsage of the element you are trying to add.
    def create_element(self, name, owner_name=None, repeat=False): 
        if repeat == False:
            # we gotta check our elements to make sure there is no other one of the same name. If so, dont create the commit. 
            if name in self.elements_names.values:
                print("There is an existing element with the same name. If you want to create another, add the 'repeat=True' argument.")
                return


        if owner_name != None:
            # find the owner_name ID
            
            try:
                owner_id = self.all_elements.loc[self.all_elements["name"] == owner_name, "id"].values[0]
            except:
                raise ValueError(f"No owner element of name {owner_name} was found. Is there some typo?")

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "PartUsage",
                    "name": f"{name}",
                    "ownedElement": [
                        {"@id": f"{owner_id}"} # must be list of dictionaries {"@id": "id of owned element"}
                    ]
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        else:
            
            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "PartUsage",
                    "name": f"{name}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()
            self._update_tree()

            # ### Tree ###
            # if owner_name != None: # if it has an owner
            #     self.tree.create_node(f"{name}", f"{name}", owner_name)
            # else:
            #     self.tree.create_node(f"{name}", f"{name}")

        else:
            pprint(f"Problem in creating a new commit in this project.")
            pprint(commit_post_response)

    # Deletes the named part. Technically this can be used to delete any element (part, attribute, or requirement) 
    # because the commit body just removes the payload, but ideally use it only for parts. Dedicated attribute and requirement removal
    # functions were created to make then modyfiable into any specific thing the programmer may want. 
    def delete_element(self, name, id=''):
        if id != '': # gives id is very specific, but if they give only name, there may be more than 1 with the same name

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }
        else:
            if len(self.all_elements.loc[self.all_elements["name"] == name, "id"]) > 1:
                print(f"There is more than 1 element with the name {name}. Specify which to delete with the element ID.")
                return
            
            try:
                id = self.all_elements.loc[self.all_elements["name"] == name, "id"].values[0]
            except:
                raise ValueError(f"There is no element of name {name} to delete. Is there a typo?")

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit3_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()

            ### Tree ###

            # Deletes all successing elements
            # This little block is only found here because attributes nor requirements
            # have any children.

            ## UNCOMMENT ##
            successors = self.tree.children(name)

            for successor in successors:
                self.delete_element(successor.identifier)
            self.tree.remove_node(name)
            self._update_tree()

        else:
            pprint(f"Problem in deleting {name} element.")
            pprint(commit_post_response)

    # Update the part with a new name and/or a new owner
    def update_element(self, name, new_name, new_owner=None): 
        
        element_id = self.all_elements.loc[self.all_elements["name"] == name, "id"].values[0]
        
        if new_owner != None and new_name != None: #update both the name and the owner
            owner = new_owner
            # find the new_owner ID
            try:
                new_owner_id = self.all_elements.loc[self.all_elements["name"] == new_owner, "id"].values[0]
            except:
                raise ValueError(f"No owner element of name {new_owner} was found. Is there some typo?")

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "PartUsage",
                    "name": f"{new_name}",
                    "identifier": f"{element_id}",
                    "ownedElement": [{"@id": f"{new_owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                },
                "identity": {
                    "@id": f"{element_id}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        elif new_owner != None: #update only the owner to a new owner
            owner = new_owner
            # find the new_owner ID
            try:
                new_owner_id = self.all_elements.loc[self.all_elements["name"] == new_owner, "id"].values[0]
            except:
                raise ValueError(f"No owner element of name {new_owner} was found. Is there some typo?")

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "PartUsage",
                    "name": f"{name}",
                    "identifier": f"{element_id}",
                    "ownedElement": [{"@id": f"{new_owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                },
                "identity": {
                    "@id": f"{element_id}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        elif new_name != None: # only update the element name
            
            # find the new_owner ID
            try:
                owner_id = self.all_elements.loc[self.all_elements["name"] == name, "owner_id"].values[0][0]["@id"]

                commit_body = {
                "@type": "Commit",
                "change": [
                    {
                    "@type": "DataVersion",
                    "payload": {
                        "@type": "PartUsage",
                        "name": f"{new_name}",
                        "identifier": f"{element_id}",
                        "ownedElement": [{"@id": f"{owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                    },
                    "identity": {
                        "@id": f"{element_id}"
                    }
                    }
                ],
                "previousCommit": {
                    "@id": self.current_commit
                }
                }

            except: # didnt find an owner, so could be updating root node/part
                
                # raise ValueError(f"Problem in updating only the name of the element.")

                commit_body = {
                "@type": "Commit",
                "change": [
                    {
                    "@type": "DataVersion",
                    "payload": {
                        "@type": "PartUsage",
                        "name": f"{new_name}",
                        "identifier": f"{element_id}"
                    },
                    "identity": {
                        "@id": f"{element_id}"
                    }
                    }
                ],
                "previousCommit": {
                    "@id": self.current_commit
                }
                }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()

            self.tree.remove_node(name)
            self._update_tree()

        else:
            pprint(f"Problem in creating a new commit in this project. (updating element)")
            pprint(commit_post_response)


    ### ATTRIBUTES ###
    # Add an attribute to the model as an AttributeUsage class and ties it to the named element as its owner
    def add_attribute(self, attribute_name, value, element_name):
        
        owner_id = self.all_elements.loc[self.all_elements["name"] == element_name, "id"].values[0]

        commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "AttributeUsage",
                    "name": f"{attribute_name}: {value}",
                    "ownedElement": [{"@id": f"{owner_id}"}]
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }
        
        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()
            self._update_tree()
        else:
            pprint(f"Problem in adding attribute to project.")
            pprint(commit_post_response.text)

    # Removes the named attribute from the model and removes the tie to the owner
    def remove_attribute(self, attribute_name, id=''):
        if id != '': # gives id is very specific, but if they give only name, there may be more than 1 with the same name

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }
        else:
            if len(self.all_elements.loc[self.all_elements["name"] == attribute_name, "id"]) > 1:
                print(f"There is more than 1 element with the name {attribute_name}. Specify which to delete with the element ID.")
                return
            
            id = self.all_elements.loc[self.all_elements["name"] == attribute_name, "id"].values[0]

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit3_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()
            
            self.tree.remove_node(attribute_name)
            self._update_tree()
        else:
            pprint(f"Problem in deleting {attribute_name} attribute.")
            pprint(commit_post_response)

    # updates the named attribute with a new attribute value
    def update_attribute(self, attribute_name, new_atribute_value): 
        only_att_name, _ = attribute_name.split(":")
        element_id = self.all_elements.loc[self.all_elements["name"] == attribute_name, "id"].values[0]
        owner_id = self.all_elements.loc[self.all_elements["name"] == attribute_name, "owner_id"].values[0][0]["@id"]


        commit_body = {
        "@type": "Commit",
        "change": [
            {
            "@type": "DataVersion",
            "payload": {
                "@type": "AttributeUsage",
                "name": f"{only_att_name}: {new_atribute_value}",
                "identifier": f"{element_id}",
                "ownedElement": [{"@id": f"{owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
            },
            "identity": {
                "@id": f"{element_id}"
            }
            }
        ],
        "previousCommit": {
            "@id": self.current_commit
        }
        }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()

            self.tree.remove_node(attribute_name)
            self._update_tree()

        else:
            pprint(f"Problem in creating a new commit in this project. (updating element)")
            pprint(commit_post_response)


    ### REQUIREMENTS ###
    
    # Creates a new requirement (as RequirementUsage class) with specified requirement name, description, and owner
    def create_requirement(self, req_name, description, owner_name, repeat=False):
        if repeat == False:
            # we gotta check our elements to make sure there is no other one of the same name. If so, dont create the commit. 
            if req_name in self.elements_names.values:
                print("There is an existing requirement with the same name. If you want to create another, add the 'repeat=True' argument.")
                return

        # find the owner_name ID
        owner_id = self.all_elements.loc[self.all_elements["name"] == owner_name, "id"].values[0]

        commit_body = {
        "@type": "Commit",
        "change": [
            {
            "@type": "DataVersion",
            "payload": {
                "@type": "RequirementUsage",
                "name": f"{req_name}",
                "text": [f"{description}"],
                "ownedElement": [
                    {"@id": f"{owner_id}"} # must be list of dictionaries {"@id": "id of owned element"}
                ]
            }
            }
        ],
        "previousCommit": {
            "@id": self.current_commit
        }
        }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()
            self._update_tree()
        else:
            pprint(f"Problem in creating a new commit in this project.")
            pprint(commit_post_response)

    # Removes named requirement
    def delete_requirement(self, req_name, id=''):
        if id != '': # gives id is very specific, but if they give only name, there may be more than 1 with the same name

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }
        else:
            if len(self.all_elements.loc[self.all_elements["name"] == req_name, "id"]) > 1:
                print(f"There is more than 1 element with the name {req_name}. Specify which to delete with the element ID.")
                return
            
            id = self.all_elements.loc[self.all_elements["name"] == req_name, "id"].values[0]

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": None,
                "identity": {
                    "@id": id
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit3_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()

            self.tree.remove_node(req_name)
            self._update_tree()
        else:
            pprint(f"Problem in deleting {req_name} element.")
            pprint(commit_post_response)

    # Update the named requirement with a new requirement name and/or a new description
    def update_requirement(self, req_name, new_req_name=None, new_desc=None): # Can only update the name or description, NOT the owner
        
        element_id = self.all_elements.loc[self.all_elements["name"] == req_name, "id"].values[0]
        owner_id = self.all_elements.loc[self.all_elements["name"] == req_name, "owner_id"].values[0][0]["@id"]

        
        if new_req_name != None and new_desc != None: #update both the name and the description

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "RequirementUsage",
                    "name": f"{new_req_name}",
                    "text": [f"{new_desc}"],
                    "identifier": f"{element_id}",
                    "ownedElement": [{"@id": f"{owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                },
                "identity": {
                    "@id": f"{element_id}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        elif new_desc != None: #update only the owner to a new owner

            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "RequirementUsage",
                    "name": f"{req_name}",
                    "text": [f"{new_desc}"],
                    "identifier": f"{element_id}",
                    "ownedElement": [{"@id": f"{owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                },
                "identity": {
                    "@id": f"{element_id}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        elif new_req_name != None: # only update the element name
            
            desc = self.all_reqs.loc[self.all_reqs["name"] == req_name, "desc"].values[0][0]
            
            commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "RequirementUsage",
                    "name": f"{new_req_name}",
                    "text": [f"{desc}"],
                    "identifier": f"{element_id}",
                    "ownedElement": [{"@id": f"{owner_id}"}] # must be list of dictionaries {"@id": "id of owned element"}
                },
                "identity": {
                    "@id": f"{element_id}"
                }
                }
            ],
            "previousCommit": {
                "@id": self.current_commit
            }
            }

        commit_post_url = f"{host}/projects/{self.id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
            self.previous_commit = self.current_commit
            self.current_commit = commit_response_json['@id']
            self._update_commits_and_elements()

            self.tree.remove_node(req_name)
            self._update_tree()

        else:
            pprint(f"Problem in creating a new commit in this project. (updating element)")
            pprint(commit_post_response)




    #################################################################################################################
    ########################################### SUPPORTING FUNCTIONS SECTION ########################################
    #################################################################################################################

    ### UPDATING COMMITS AND ELEMENTS DATAFRAMES AFTER UPDATING MODEL; KEEPS EVERYTHING UP TO DATE AS LINES ARE RUNNING IN CODE CALLING THESE FUNCTIONS ###
    def _update_commits(self):
        commits_url = f"{host}/projects/{self.id}/commits" 
        commits_response = requests.get(commits_url)

        if commits_response.status_code == 200:
            commits = commits_response.json()

            commits_data = list(map(lambda b: {'Commit ID':b['@id'], "Commit Created":b['created']}, commits))
        
            df_commits = pd.DataFrame.from_records(commits_data)

            df_commits['Commit Created'] = pd.to_datetime(df_commits['Commit Created'])  # Convert to datetime
            df_commits = df_commits.sort_values(by='Commit Created', ascending=False)    # Sort from newest to oldest

            # Reset the index if desired
            df_commits = df_commits.reset_index(drop=True)

            self.all_commits = df_commits

    def _update_elements(self):
    # Create a function that updates the all_elements and related self. variables after creating or deleting an element, attribute, or requirement
        elements_url = f"{host}/projects/{self.id}/commits/{self.current_commit}/elements" 
        response = requests.get(elements_url)
        
        if response.status_code == 200:
            elements_data = response.json() #type is LIST
            #type(response.json()[0]) IS DICT!
            # elements_name_to_print = elements_data['name'] if elements_data['name'] else 'N/A'
            
            df_elements = pd.DataFrame([{"name": element["name"], "id": element["@id"], "type": element["@type"]} for element in elements_data]).sort_values("name")
            df_reqs = pd.DataFrame([{"name": element["name"], "desc": element["text"], "id": element["@id"], "type": element["@type"], "owner_id": element["ownedElement"]} for element in elements_data if element["@type"]=="RequirementUsage"])

            try:
                self.all_elements = df_elements.sort_values("type", ascending=False).reset_index(drop=True)
                self.elements_names = df_elements["name"]
                self.elements_ids = df_elements["id"]
                self.elements_types = df_elements["type"]
                if df_reqs.empty==False:
                    self.all_reqs = df_reqs.sort_values("name")
            except:
                raise ValueError("No elements found in current commit.")

        else:
            pprint(f"Status Code: {response.status_code}. Problem in fetching elements.")

    def _update_commits_and_elements(self):
        self._update_commits()
        self._update_elements()

    ### TREE ####

    def add_node_with_parents(self, tree, df, node_name, node_id, parent_name=None, type=None):
        """
        Recursively adds a node to the tree, ensuring its parent and ancestors are also added.
        """
        # If the node already exists, and you are not updating a current element, do nothing
        if node_name in self.tree.nodes:
            return

        # Determine the format of the text in tree. The identifier remains solely the element name. the tag is what changes.
        if type == "AttributeUsage":
            node_name_formatted = f"Attribute:\n {node_name}"
        elif type == "RequirementUsage":
            req_desc = self.all_reqs.loc[self.all_reqs["name"]==node_name, "desc"].values[0][0]

            node_name_formatted = f"Requirement:\n {node_name}\n {req_desc}"
        else:
            node_name_formatted = node_name

        # If the parent exists, create the node with the parent
        if parent_name is None or parent_name in self.tree.nodes:
            # print(f'{node_name}', f'{parent_name}')
            self.tree.create_node(tag=node_name_formatted, identifier=node_name, parent=parent_name)
        else:
            # Find the parent's information in the dataframe
            # parent_row = df[df["id"] == df[df["name"] == parent_name].iloc[0]["owner_id"][0]["@id"]]
            parent_row = df[df["name"] == parent_name]
            if not parent_row.empty:
                grandparent_name = None
                grandparent_id = None
                # Extract the parent's parent (grandparent) if it exists
                if parent_row.iloc[0]["owner_id"]:
                    grandparent_id = parent_row.iloc[0]["owner_id"][0]["@id"]
                    grandparent_row = df[df["id"] == grandparent_id]
                    if not grandparent_row.empty:
                        grandparent_name = grandparent_row.iloc[0]["name"]
                # Recursively ensure the parent exists
                self.add_node_with_parents(tree, df, parent_row.iloc[0]["name"], parent_row.iloc[0]["id"], grandparent_name)
            # Now that the parent is added, create the current node
            self.tree.create_node(tag=node_name_formatted, identifier=node_name, parent=parent_name)

    # This function is mainly used to generate a tree in dot format for PyGraphviz (visualization purposes)
    def generate_dot(self, tree):
        dot_string = "digraph G {\n"
        for node in tree.all_nodes():
            dot_string += f'    "{node.identifier}" [label="{node.tag}"];\n'
            if not node.is_root():
                parent = tree.parent(node.identifier).identifier
                # dot_string += f'    "{parent}" -> "{node.identifier} \n - more info here \n - attribute 2 here";\n'
                dot_string += f'    "{parent}" -> "{node.identifier}";\n'
        dot_string += "}"
        return dot_string

    # Updates the tree every time the model is modified, that is, an element (part, attribute, or requirement) is created, updated, or deleted.
    def _update_tree(self):
        elements_url = f"{host}/projects/{self.id}/commits/{self.current_commit}/elements" 
        response = requests.get(elements_url)
        
        if response.status_code == 200:
            elements_data = response.json() #type is LIST
            
            df_elements = pd.DataFrame([{"name": element["name"], "id": element["@id"], "type": element["@type"], "owner_id": element["ownedElement"]} for element in elements_data])

            self._df_elements_not_comment = df_elements[df_elements["type"]!="Comment"]

        for index, element in self._df_elements_not_comment.iterrows():
            node_name = element["name"]
            node_id = element["id"]
            parent_name = None
            node_type = element["type"]
            # Extract parent_name from owner_id if available
            if element["owner_id"]:
                parent_id = element["owner_id"][0]["@id"]
                parent_row = self._df_elements_not_comment[self._df_elements_not_comment["id"] == parent_id]
                if not parent_row.empty:
                    parent_name = parent_row.iloc[0]["name"]
            # Add the node and its parents
            self.add_node_with_parents(self.tree, self._df_elements_not_comment, node_name, node_id, parent_name, node_type)
        
        dot = self.generate_dot(self.tree)
        # Visualize with pygraphviz
        G = pgv.AGraph(string=dot)
        G.layout(prog='dot')
        G.draw('tree.png')  # Saves as tree.png

    ### COMMITS ###
    # Select using the commit index or id the commit you want to be working in
    def select_commit(self, index=None, id=None):
        if index != None: # given index of desired commit in self.all_commits, set the current commit
            try:
                self.current_commit = self.all_commits.iloc[index, 0]
            except:
                ValueError("Index does not exist or is out of range.")

        elif id != None: # given id of desired commit in self.all_commits, set the current commit
            self.current_commit = self.id

    # Select the most recent commit as your current commit
    def select_most_recent_commit(self):
        self.current_commit = self.latest_commit







########## OUTSIDE PROJECT CLASS ##########   

# #### NEW PROJECT ####
# # New projects have no commits, so created this so the code doesnt try to find them 
def new_project(project_name, project_description='', repeat=False): 
    
    # TODO: If a project with the same name already exists, ask for the repeat argument  

    project_name = f"{project_name}"
    project_data = {
    "@type":"Project",
    "name": project_name,
    "description": f"{project_description}"
    }

    project_post_url = f"{host}/projects" 

    project_post_response = requests.post(project_post_url, 
                                        headers={"Content-Type": "application/json"}, 
                                        data=json.dumps(project_data))

    project_id = ""

    if project_post_response.status_code == 200:
        
        timestamp = datetime.now()
        
        project_response_json = project_post_response.json()
        pprint(project_response_json)
        id = project_response_json['@id']
        name = project_response_json['name']

        ### Create a first commit by default with a comment stating the name, descrption, and when it was created ###
        commit_body = {
            "@type": "Commit",
            "change": [
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "Comment",
                    "name": f"Project Name: {name}"
                }
                },
                                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "Comment",
                    "name": f"Project Description: {project_description}"
                }
                },
                                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "Comment",
                    "name": f"Created: {timestamp}"
                }
                },
                {
                "@type": "DataVersion",
                "payload": {
                    "@type": "PartUsage",
                    "name": "Root Part",
                }
                }
            ]
            }

        commit_post_url = f"{host}/projects/{id}/commits" 

        commit_post_response = requests.post(commit_post_url, 
                                            headers={"Content-Type": "application/json"}, 
                                            data=json.dumps(commit_body))

        commit1_id = ""

        if commit_post_response.status_code == 200:
            commit_response_json = commit_post_response.json()
            pprint(commit_response_json)
        else:
            pprint(f"Problem in creating the commit behind intial comments.")
            pprint(commit_post_response)

    else:
        pprint(f"Problem in creating the new project.")
        pprint(project_post_response)
