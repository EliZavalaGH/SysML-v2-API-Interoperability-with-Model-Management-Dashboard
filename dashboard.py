import streamlit as st
import API_scripts as api

def main():
    ### Set the page configuration ###
    st.set_page_config(
        page_title="SysML v2 Model Dashboard",
        page_icon="⚙️",
        layout="wide")

    st.title("SysML v2 Model Dashboard")

    ### Page Layout ###

    st.sidebar.markdown("### Select a Project")

    existing_and_new_project = api.projects_names_list()

    selected_proj_name = st.sidebar.selectbox("Select a Project",
                                existing_and_new_project,
                                index=0)

    # NOTE: For stacked buttons (clicking a button opens a window that shows another button), you will see the st.session_state appear. This stores and
    # preserves information between script reruns. The way that I undestood this was that if you click the button inside the button, the second button
    # will run with the next state rather than the first, hence NOT preserving the information from the first button. If you require more information on 
    # how this works, dont hesitate to give it a quick google search. 

    # Check if the state variable is initialized
    if "create_new_project_clicked" not in st.session_state:
        st.session_state.create_new_project_clicked = False

    if st.sidebar.button("Create New Project", use_container_width=True):
        st.session_state.create_new_project_clicked = True

    if st.session_state.create_new_project_clicked:
        
        # with st.sidebar.form("create new project"):
        name = st.sidebar.text_input("New Project Name")
        desc = st.sidebar.text_input("Project Description", value='')

        # submit_create_element = st.sidebar.form_submit_button("Submit")
        submit_create_element = st.sidebar.button("Submit")

        if submit_create_element:
            api.new_project(name, desc)
            st.session_state.create_new_project_clicked = False
            selected_proj_name = f"{name}"


    if selected_proj_name: # if a project is selected...
        
        project = api.Project(selected_proj_name)

        st.sidebar.divider()

        st.sidebar.markdown(f"### Project View")
        
        if st.sidebar.toggle("View All Elements Table"):
            st.sidebar.write(project.all_elements)

        if st.sidebar.toggle("View All Parts Table"):
            st.sidebar.write(project.all_elements[project.all_elements["type"]=="PartUsage"])

        if st.sidebar.toggle("View All Attributes Table"):
            st.sidebar.write(project.all_elements[project.all_elements["type"]=="AttributeUsage"])

        if st.sidebar.toggle("View All Requirements Table"):
            st.sidebar.write(project.all_elements[project.all_elements["type"]=="RequirementUsage"])
        

        ### Main Page ###

        tree_image = st.empty()
        tree_image.image("tree.png")

        st.divider()

        st.markdown(f"### Element Manipulation")

        radio_em = st.radio("Choose Element Type", ["Parts", "Attributes", "Requirements"], horizontal=True)

        if radio_em == "Parts":

            sel_part = st.selectbox("Select Part", project.all_elements[project.all_elements["type"]=="PartUsage"])

            c1, c2, c3, c4 = st.columns(4, gap="small")

            with c1:
                # Check if the state variable is initialized
                if "create_element_clicked" not in st.session_state:
                    st.session_state.create_element_clicked = False

                if st.button("Create Element", use_container_width=True):
                    st.session_state.create_element_clicked = True

                if st.session_state.create_element_clicked:
                    
                    with st.form("create element"):
                        name = st.text_input("New Element Name")
                        owner = st.text_input("Owner Name", value=f"{sel_part}")
                        # id = st.text_input("Owner ID (Optional)", value='')
                        is_repeat = st.checkbox("Repeat Element?")

                        submit_create_element = st.form_submit_button("Submit")

                        if submit_create_element:
                            project.create_element(name, owner, repeat=is_repeat)
                            tree_image.image("tree.png")
                            st.session_state.create_element_clicked = False


            with c2:
                # Check if the state variable is initialized
                if "update_element_clicked" not in st.session_state:
                    st.session_state.update_element_clicked = False

                if st.button("Update Element", use_container_width=True):
                    st.session_state.update_element_clicked = True

                if st.session_state.update_element_clicked:
                    
                    with st.form("update element"):
                        name = st.text_input("Element to Update", value=f"{sel_part}")
                        new_name = st.text_input("Updated Name (Optional)", value=None)
                        new_owner = st.text_input("Updated Owner (Optional)", value=None)
                        # new_owner_id = st.text_input("Owner ID (Optional)", value='') # not implemented in backend code

                        submit_update_element = st.form_submit_button("Submit")

                        if submit_update_element:
                            # project.update_element(name, owner, repeat=is_repeat)
                            project.update_element(name, new_name, new_owner)
                            tree_image.image("tree.png")
                            st.session_state.update_element_clicked = False

            with c3:
                # Check if the state variable is initialized
                if "delete_element_clicked" not in st.session_state:
                    st.session_state.delete_element_clicked = False

                if st.button("Delete Element", use_container_width=True):
                    st.session_state.delete_element_clicked = True

                if st.session_state.delete_element_clicked:
                    
                    with st.form("delete element"):
                        name = st.text_input("Element to Delete", value=f"{sel_part}")
                        id = st.text_input("Element ID (Optional)")
                        st.markdown("**:red[WARNING]**: Deleting this element deletes all children too. **Continue?**")

                        submit_delete_element = st.form_submit_button("Submit")

                        if submit_delete_element:
                            project.delete_element(name, id)
                            tree_image.image("tree.png")
                            st.session_state.delete_element_clicked = False

            with c4:
                if st.button("Extract Element", use_container_width=True):
                    st.success("Extracting Info Coming Soon!")

            if st.button("Extract All Elements", use_container_width=True):
                st.success("Extracting Info Coming Soon!")



        elif radio_em == "Attributes":

            COL1, COL2 = st.columns(2)

            with COL1:
                sel_part = st.selectbox("Select Part", project.all_elements[project.all_elements["type"]=="PartUsage"])
            
            with COL2:
                sel_att = st.selectbox("Select Attribute", project.all_elements[project.all_elements["type"]=="AttributeUsage"])
                # TODO: Be able to see just those owned by the selected part

            c1, c2, c3, c4 = st.columns(4, gap="small")

            with c1:
                # Check if the state variable is initialized
                if "create_attribute_clicked" not in st.session_state:
                    st.session_state.create_attribute_clicked = False

                if st.button("Create Attribute", use_container_width=True):
                    st.session_state.create_attribute_clicked = True

                if st.session_state.create_attribute_clicked:
                    
                    with st.form("create attribute"):
                        name = st.text_input("New Attribute Name")
                        value = st.text_input("Attribute Value")
                        owner = st.text_input("Owner Name", value=f"{sel_part}")

                        submit_create_attribute = st.form_submit_button("Submit")

                        if submit_create_attribute:
                            project.add_attribute(name, value, owner)
                            tree_image.image("tree.png")
                            st.session_state.create_attribute_clicked = False

            with c2:
                # Check if the state variable is initialized
                if "update_attribute_clicked" not in st.session_state:
                    st.session_state.update_attribute_clicked = False

                if st.button("Update Attribute", use_container_width=True):
                    st.session_state.update_attribute_clicked = True

                if st.session_state.update_attribute_clicked:
                    
                    with st.form("update attribute"):
                        name = st.text_input("Attribute to Update", value=f"{sel_att}")
                        new_val = st.text_input("Updated Value", value=None)

                        submit_update_attribute = st.form_submit_button("Submit")

                        if submit_update_attribute:
                            project.update_attribute(name, new_val)
                            tree_image.image("tree.png")
                            st.session_state.update_attribute_clicked = False

            with c3:
                # Check if the state variable is initialized
                if "delete_attribute_clicked" not in st.session_state:
                    st.session_state.delete_attribute_clicked = False

                if st.button("Delete Attribute", use_container_width=True):
                    st.session_state.delete_attribute_clicked = True

                if st.session_state.delete_attribute_clicked:
                    
                    with st.form("delete attribute"):
                        name = st.text_input("Attribute to Delete", value=f"{sel_att}")
                        id = st.text_input("Attribute ID (Optional)", value='')
                        st.markdown("**:red[WARNING]**: Are you sure you want to delete this attribute?")

                        submit_delete_attribute = st.form_submit_button("Submit")

                        if submit_delete_attribute:
                            project.remove_attribute(name, id)
                            tree_image.image("tree.png")
                            st.session_state.delete_attribute_clicked = False

            with c4:
                if st.button("Extract Attribute", use_container_width=True):
                    st.success("Extracting Info Coming Soon!")


            if st.button("Extract All Attributes", use_container_width=True):
                st.success("Extracting Info Coming Soon!")



        elif radio_em == "Requirements":

            COL1, COL2 = st.columns(2)

            with COL1:
                sel_part = st.selectbox("Select Part", project.all_elements[project.all_elements["type"]=="PartUsage"])
            
            with COL2:
                sel_req = st.selectbox("Select Requirement", project.all_elements[project.all_elements["type"]=="RequirementUsage"])
                # TODO: Be able to see just those owned by the selected part

            c1, c2, c3, c4 = st.columns(4, gap="small")

            with c1:
                # Check if the state variable is initialized
                if "create_requirement_clicked" not in st.session_state:
                    st.session_state.create_requirement_clicked = False

                if st.button("Create Requirement", use_container_width=True):
                    st.session_state.create_requirement_clicked = True

                if st.session_state.create_requirement_clicked:
                    
                    with st.form("create requirement"):
                        name = st.text_input("New Requirement Name")
                        desc = st.text_input("Requirement Description")
                        owner = st.text_input("Owner Name", value=f"{sel_part}")
                        is_repeat = st.checkbox("Repeat Requirement?")

                        submit_create_requirement = st.form_submit_button("Submit")

                        if submit_create_requirement:
                            project.create_requirement(name, desc, owner, is_repeat)
                            tree_image.image("tree.png")
                            st.session_state.create_requirement_clicked = False

            with c2:
                # Check if the state variable is initialized
                if "update_requirement_clicked" not in st.session_state:
                    st.session_state.update_requirement_clicked = False

                if st.button("Update Requirement", use_container_width=True):
                    st.session_state.update_requirement_clicked = True

                if st.session_state.update_requirement_clicked:
                    
                    with st.form("update requirement"):
                        name = st.text_input("Requirement to Update", value=f"{sel_req}")
                        new_name = st.text_input("Updated Name (Optional)", value=None)
                        new_desc = st.text_input("Updated Description (Optional)", value=None)

                        submit_update_requirement = st.form_submit_button("Submit")

                        if submit_update_requirement:
                            project.update_requirement(name, new_name, new_desc)
                            tree_image.image("tree.png")
                            st.session_state.update_requirement_clicked = False

            with c3:
                # Check if the state variable is initialized
                if "delete_requirement_clicked" not in st.session_state:
                    st.session_state.delete_requirement_clicked = False

                if st.button("Delete Requirement", use_container_width=True):
                    st.session_state.delete_requirement_clicked = True

                if st.session_state.delete_requirement_clicked:
                    
                    with st.form("delete requirement"):
                        name = st.text_input("Requirement to Delete", value=f"{sel_req}")
                        id = st.text_input("Requirement ID (Optional)", value='')
                        st.markdown("**:red[WARNING]**: Are you sure you want to delete this requirement?")

                        submit_delete_requirement = st.form_submit_button("Submit")

                        if submit_delete_requirement:
                            project.delete_requirement(name, id)
                            tree_image.image("tree.png")
                            st.session_state.delete_requirement_clicked = False

            with c4:
                if st.button("Extract Requirement", use_container_width=True):
                    st.success("Extracting Info Coming Soon!")


            if st.button("Extract All Requirements", use_container_width=True):
                st.success("Extracting Info Coming Soon!")




if __name__ == "__main__":
    main()