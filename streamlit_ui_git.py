import datetime
import json
import streamlit as st
from pathlib import Path
import pandas as pd
from qa_db import DBManager
import base64
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Define the path to the siteconfig folder
SITE_CONFIG_PATH = Path('.\\SiteConfig')

dbm = DBManager()

# Ensure the siteconfig directory exists
if not SITE_CONFIG_PATH.exists():
    SITE_CONFIG_PATH.mkdir(parents=True)


# Function to get existing .toml files
def get_toml_files():
    return [f.stem for f in SITE_CONFIG_PATH.glob('*.toml')]


def display_ag_grid(df):
    # Function to encode image to base64
    def encode_image_to_base64(image_path):
        if os.path.exists(image_path):
            with open(image_path, "rb") as img_file:
                return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
        return None

    # Convert image paths to base64 and store filenames
    for idx, row in df.iterrows():
        if isinstance(row['Proof_Path'], list) and row['Proof_Path']:
            base64_images = [encode_image_to_base64(path) for path in row['Proof_Path']]
            filenames = [os.path.basename(path) for path in row['Proof_Path']]
            df.at[idx, 'Proof_Path'] = [{"src": b64, "name": fname} for b64, fname in zip(base64_images, filenames)]

    # JavaScript for thumbnail with zoom on hover and modal with navigation
    show_image = JsCode("""
        class ThumbnailRenderer {
            init(params) {
                this.eGui = document.createElement('div');
                this.eGui.style.display = 'flex';
                this.eGui.style.justifyContent = 'center';
                this.eGui.style.alignItems = 'center';

                const images = params.value;
                if (!images || !images.length) return;

                const img = document.createElement('img');
                img.setAttribute('src', images[0].src);
                img.setAttribute('width', '200');
                img.style.cursor = 'pointer';
                img.style.transition = 'transform 0.3s ease';  // Smooth zoom transition

                img.addEventListener('mouseover', () => {
                    img.style.transform = 'scale(1.1)';  // Zoom in on hover
                });

                img.addEventListener('mouseout', () => {
                    img.style.transform = 'scale(1)';  // Reset zoom on mouse out
                });

                img.addEventListener('click', () => {
                    const modal = document.createElement('div');
                    modal.style.position = 'fixed';
                    modal.style.top = '0';
                    modal.style.left = '0';
                    modal.style.width = '100vw';
                    modal.style.height = '100vh';
                    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                    modal.style.display = 'flex';
                    modal.style.justifyContent = 'center';
                    modal.style.alignItems = 'center';
                    modal.style.flexDirection = 'column';
                    modal.style.zIndex = '99999';
                    modal.style.overflow = 'auto';

                    const imageName = document.createElement('div');
                    imageName.style.position = 'absolute';
                    imageName.style.top = '10px';
                    imageName.style.left = '10px';
                    imageName.style.color = 'white';
                    imageName.style.fontSize = '1.2rem';
                    imageName.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                    imageName.style.padding = '8px';
                    imageName.style.borderRadius = '5px';
                    imageName.innerText = images[0].name;
                    modal.appendChild(imageName);

                    const enlargedImg = document.createElement('img');
                    enlargedImg.setAttribute('src', images[0].src);
                    enlargedImg.style.maxWidth = '80vw';
                    enlargedImg.style.maxHeight = '80vh';
                    enlargedImg.style.objectFit = 'contain';
                    modal.appendChild(enlargedImg);

                    let currentIndex = 0;

                    const navContainer = document.createElement('div');
                    navContainer.style.display = 'flex';
                    navContainer.style.justifyContent = 'space-between';
                    navContainer.style.alignItems = 'center';
                    navContainer.style.width = '100%';
                    navContainer.style.position = 'absolute';
                    navContainer.style.top = '50%';

                    const leftArrow = document.createElement('button');
                    leftArrow.innerHTML = '&#9664;';
                    leftArrow.style.fontSize = '2rem';
                    leftArrow.style.background = 'none';
                    leftArrow.style.color = 'white';
                    leftArrow.style.border = 'none';
                    leftArrow.style.cursor = 'pointer';
                    leftArrow.style.padding = '20px';

                    const rightArrow = document.createElement('button');
                    rightArrow.innerHTML = '&#9654;';
                    rightArrow.style.fontSize = '2rem';
                    rightArrow.style.background = 'none';
                    rightArrow.style.color = 'white';
                    rightArrow.style.border = 'none';
                    rightArrow.style.cursor = 'pointer';
                    rightArrow.style.padding = '20px';

                    navContainer.appendChild(leftArrow);
                    navContainer.appendChild(rightArrow);
                    modal.appendChild(navContainer);

                    const showImage = (index) => {
                        enlargedImg.setAttribute('src', images[index].src);
                        imageName.innerText = images[index].name;
                    };

                    rightArrow.addEventListener('click', () => {
                        currentIndex = (currentIndex + 1) % images.length;
                        showImage(currentIndex);
                    });

                    leftArrow.addEventListener('click', () => {
                        currentIndex = (currentIndex - 1 + images.length) % images.length;
                        showImage(currentIndex);
                    });

                    modal.addEventListener('keydown', (event) => {
                        if (event.key === 'ArrowRight') {
                            currentIndex = (currentIndex + 1) % images.length;
                            showImage(currentIndex);
                        } else if (event.key === 'ArrowLeft') {
                            currentIndex = (currentIndex - 1 + images.length) % images.length;
                            showImage(currentIndex);
                        } else if (event.key === 'Escape') {
                            modal.remove();
                        }
                    });

                    modal.addEventListener('click', (event) => {
                        if (event.target === modal) {
                            modal.remove();
                        }
                    });

                    document.body.appendChild(modal);
                    modal.tabIndex = -1;
                    modal.focus();
                });

                this.eGui.appendChild(img);
            }

            getGui() {
                return this.eGui;
            }
        }
    """)

    # Configure columns and value formatting
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column(
        "Proof_Path",
        cellRenderer=show_image,
        valueFormatter=JsCode("""
            function(params) {
                return params.value && params.value.length ? params.value[0].name : '';
            }
        """),
        editable=False
    )

    # Enable inline editing for the 'Status' column with dropdown selection
    status_options = ['Passed', 'Failed', 'Error']
    gb.configure_column(
        'Status',
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': status_options},
        cellRenderer=JsCode("""
               class StatusRenderer {
                   init(params) {
                       this.eGui = document.createElement('span');
                       let color;
                       if (params.value === 'Passed') {
                           color = 'green';
                       } else if (params.value === 'Failed') {
                           color = 'red';
                       } else if (params.value === 'Error') {
                           color = 'orange';
                       }
                       this.eGui.innerText = params.value;
                       this.eGui.style.backgroundColor = color;
                       this.eGui.style.color = 'white';
                       this.eGui.style.fontWeight = 'bold';
                       this.eGui.style.padding = '5px 10px';
                       this.eGui.style.borderRadius = '5px';
                       this.eGui.style.display = 'flex';  // Use flexbox for alignment
                       this.eGui.style.justifyContent = 'center';  // Center horizontally
                       this.eGui.style.alignItems = 'center';  // Center vertically
                       this.eGui.style.width = '80%';  // Set width to 80% of the cell
                       this.eGui.style.height = '40%';  // Ensure full height usage for vertical alignment
                       this.eGui.style.margin = 'auto';  // Center align horizontally and vertically
                   }
                   getGui() {
                       return this.eGui;
                   }
               }
           """),
        cellStyle={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
        width=150
    )

    # Grid Options with grouping and filtering
    gb.configure_grid_options(
        groupDisplayType='multipleColumns',
        rowGroupPanelShow='always',
        enableGroupEdit=True,
        groupDefaultExpanded=-1,  # Expand all groups by default
        rowSelection={
            "mode": "multiRow",
            "checkboxes": True,
            "headerCheckbox": True,
            "selectAll": "filtered"
        },
        alwaysShowHorizontalScroll=True,
        cellSelection=True,
        pagination=True,
        paginationPageSize=10,
        paginationPageSizeSelector=[10, 20, 50, 100],
        rowHeight=100,
        domLayout='autoHeight'
    )

    gb.configure_default_column(editable=True, filter=True, groupable=True)

    vgo = gb.build()
    AgGrid(df, gridOptions=vgo, theme='streamlit', allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

    # Inject CSS to ensure AG-Grid allows modal overflow and zoom on hover
    st.markdown("""
        <style>
        .ag-root-wrapper, .streamlit-expander, .block-container {
            overflow: visible !important;
            position: static !important;
        }

        .modal {
            z-index: 99999 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    st.set_page_config(page_title="Test My URL", page_icon=":ladybug:", layout="wide", initial_sidebar_state="auto",
                       menu_items=None)

    input_ui = {
        'name': None,
        'dev': None,
        'stage': None,
        'prod': None
    }

    env_details = {
        "Subscription": "Paid",
        "Execution Date and Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
        "Prod_Url": "http://example.com/prod",
        "Drupal/PHP ver": "10.4/8.3",
        "Status": "QA Approved",
        "Total_Execution_Time": "00:10:00",
        "Browser": "Chrome",
        "Browser ver": "v25.02"
    }

    # Streamlit app setup
    st.title("Test my URL :ladybug:")

    # Get list of existing files
    existing_files = get_toml_files()

    with st.expander("Test Execution", expanded=True):
        config_file_selected = st.selectbox(label='Subscriptions', options=existing_files, index=None,
                                            placeholder="Select or Add Configuration Files",
                                            disabled=False, label_visibility="visible")
        leftl, middlel, rightl = st.columns([0.3, 0.5, 0.2], vertical_alignment="center")
        with leftl:
            options = ["Development", "Stage", "Production"]
            if config_file_selected:
                selection = st.pills("Environments", options, selection_mode="multi", disabled=False)
            else:
                selection = []
                selection = st.pills("Environments", options, selection_mode="multi", disabled=True)
        with middlel:

            if config_file_selected:
                file_path = st.file_uploader("Choose a file", type=['xlsx'], disabled=True, )
            else:
                file_path = st.file_uploader("Choose a file", type=['xlsx'], disabled=False)

        with rightl:
            st.download_button("Download Excel", data=".\InputFiles\data1.xlsx", file_name="data1.xlsx",
                               use_container_width=True)

            # Every form must have a submit button.
            if config_file_selected or file_path:
                submitted = st.button("Run 	:arrow_forward:", use_container_width=True, disabled=False)
                if submitted:

                    input_ui['name'] = config_file_selected
                    if 'Prduction' in selection:
                        input_ui['prod'] = 1
                    if 'Stage' in selection:
                        input_ui['stage'] = 1
                    if 'Development' in selection:
                        input_ui['dev'] = 1
                    st.write(input_ui)
                df = pd.DataFrame(input_ui, index=[1])
            else:
                st.button("Run 	:arrow_forward:", use_container_width=True, disabled=True)

    leftde, rightde = st.columns([0.5, 0.5], vertical_alignment="center")
    site_details = {}
    env_details_ui = {}

    site_details['Subscription'] = env_details["Subscription"]
    site_details['Prod_Url'] = env_details["Prod_Url"]
    site_details['Drupal/PHP ver'] = env_details["Drupal/PHP ver"]
    site_details['Status'] = env_details["Status"]

    env_details_ui["Execution Date and Time"] = env_details["Execution Date and Time"]
    env_details_ui["Total_Execution_Time"] = env_details["Total_Execution_Time"]
    env_details_ui["Browser"] = env_details["Browser"]
    env_details_ui["Browser ver"] = env_details["Browser ver"]

    with leftde:
        st.data_editor(site_details, use_container_width=True)
    with rightde:
        st.data_editor(env_details_ui, use_container_width=True)

    col0, col1, col2, col3, col4, col5, col6 = st.columns([0.02, 0.15, 0.15, 0.15, 0.15, 0.15, 0.02])
    col1.metric("Temperature", "70 °F", "1.2 °F")
    col2.metric("Wind", "9 mph", "-8%")
    col3.metric("Humidity", "86%", "4%")
    col4.metric("Turbulence", "86%", "-4%")
    col5.metric("AQI", "86%", "130")

    with open("Result/cardio/05_02_2025_08_27_23/dev/cardio_dev_results.json", 'r') as file:
        data = json.load(file)
    df = pd.json_normalize(data)
    display_ag_grid(df)


if __name__ == "__main__":
    main()
############################################################################################################################################################################################################################

import datetime
import json
import streamlit as st
from pathlib import Path
import pandas as pd
from qa_db import DBManager
import base64
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Constants
SITE_CONFIG_PATH = Path('./SiteConfig')
JSON_FILE_PATH = Path("Result/cardio/05_02_2025_08_27_23/dev/cardio_dev_results.json")

# Initialize Database Manager
dbm = DBManager()

# Ensure the siteconfig directory exists
SITE_CONFIG_PATH.mkdir(parents=True, exist_ok=True)


def get_toml_files():
    """Retrieve all .toml files from SITE_CONFIG_PATH."""
    return [f.stem for f in SITE_CONFIG_PATH.glob('*.toml')]


def encode_image_to_base64(image_path):
    """Encode an image to base64."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return None


def display_ag_grid(df):
    """Display DataFrame in an AG Grid with editable Status column and image thumbnails."""

    # Convert image paths to base64 and store filenames
    for idx, row in df.iterrows():
        if isinstance(row['Proof_Path'], list) and row['Proof_Path']:
            base64_images = [encode_image_to_base64(path) for path in row['Proof_Path']]
            filenames = [os.path.basename(path) for path in row['Proof_Path']]
            df.at[idx, 'Proof_Path'] = [{"src": b64, "name": fname} for b64, fname in zip(base64_images, filenames)]

    # JavaScript for thumbnail with zoom and modal navigation
    show_image = JsCode("""
        class ThumbnailRenderer {
            init(params) {
                this.eGui = document.createElement('div');
                this.eGui.style.display = 'flex';
                this.eGui.style.justifyContent = 'center';
                this.eGui.style.alignItems = 'center';

                const images = params.value;
                if (!images || !images.length) return;

                const img = document.createElement('img');
                img.setAttribute('src', images[0].src);
                img.setAttribute('width', '200');
                img.style.cursor = 'pointer';
                img.style.transition = 'transform 0.3s ease';

                img.addEventListener('mouseover', () => img.style.transform = 'scale(1.1)');
                img.addEventListener('mouseout', () => img.style.transform = 'scale(1)');

                img.addEventListener('click', () => this.openModal(images));
                this.eGui.appendChild(img);
            }

            openModal(images) {
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100vw';
                modal.style.height = '100vh';
                modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                modal.style.display = 'flex';
                modal.style.justifyContent = 'center';
                modal.style.alignItems = 'center';
                modal.style.flexDirection = 'column';
                modal.style.zIndex = '99999';
                modal.style.overflow = 'auto';

                const imageName = document.createElement('div');
                imageName.style.position = 'absolute';
                imageName.style.top = '10px';
                imageName.style.left = '10px';
                imageName.style.color = 'white';
                imageName.style.fontSize = '1.2rem';
                imageName.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                imageName.style.padding = '8px';
                imageName.style.borderRadius = '5px';
                imageName.innerText = images[0].name;
                modal.appendChild(imageName);

                const enlargedImg = document.createElement('img');
                enlargedImg.setAttribute('src', images[0].src);
                enlargedImg.style.maxWidth = '80vw';
                enlargedImg.style.maxHeight = '80vh';
                enlargedImg.style.objectFit = 'contain';
                modal.appendChild(enlargedImg);

                let currentIndex = 0;
                this.addNavigation(modal, images, enlargedImg, imageName, currentIndex);

                document.body.appendChild(modal);
                modal.tabIndex = -1;
                modal.focus();
            }

            addNavigation(modal, images, enlargedImg, imageName, currentIndex) {
                const navContainer = document.createElement('div');
                navContainer.style.display = 'flex';
                navContainer.style.justifyContent = 'space-between';
                navContainer.style.alignItems = 'center';
                navContainer.style.width = '100%';
                navContainer.style.position = 'absolute';
                navContainer.style.top = '50%';

                const leftArrow = this.createArrow('&#9664;', () => {
                    currentIndex = (currentIndex - 1 + images.length) % images.length;
                    enlargedImg.setAttribute('src', images[currentIndex].src);
                    imageName.innerText = images[currentIndex].name;
                });

                const rightArrow = this.createArrow('&#9654;', () => {
                    currentIndex = (currentIndex + 1) % images.length;
                    enlargedImg.setAttribute('src', images[currentIndex].src);
                    imageName.innerText = images[currentIndex].name;
                });

                navContainer.appendChild(leftArrow);
                navContainer.appendChild(rightArrow);
                modal.appendChild(navContainer);

                modal.addEventListener('keydown', (event) => {
                    if (event.key === 'ArrowRight') rightArrow.click();
                    else if (event.key === 'ArrowLeft') leftArrow.click();
                    else if (event.key === 'Escape') modal.remove();
                });

                modal.addEventListener('click', (event) => {
                    if (event.target === modal) modal.remove();
                });
            }

            createArrow(symbol, onClick) {
                const arrow = document.createElement('button');
                arrow.innerHTML = symbol;
                arrow.style.fontSize = '2rem';
                arrow.style.background = 'none';
                arrow.style.color = 'white';
                arrow.style.border = 'none';
                arrow.style.cursor = 'pointer';
                arrow.style.padding = '20px';
                arrow.addEventListener('click', onClick);
                return arrow;
            }

            getGui() {
                return this.eGui;
            }
        }
    """)

    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column(
        "Proof_Path",
        cellRenderer=show_image,
        valueFormatter=JsCode("""
            function(params) {
                return params.value && params.value.length ? params.value[0].name : '';
            }
        """),
        editable=False
    )

    # Configure editable Status column
    status_options = ['Passed', 'Failed', 'Error']
    gb.configure_column(
        'Status',
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': status_options},
        cellStyle={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
        width=150
    )

    # Grid Options
    gb.configure_grid_options(
        groupDisplayType='multipleColumns',
        rowGroupPanelShow='always',
        enableGroupEdit=True,
        groupDefaultExpanded=-1,
        rowSelection={
            "mode": "multiRow",
            "checkboxes": True,
            "headerCheckbox": True,
            "selectAll": "filtered"
        },
        alwaysShowHorizontalScroll=True,
        cellSelection=True,
        pagination=True,
        paginationPageSize=10,
        paginationPageSizeSelector=[10, 20, 50, 100],
        rowHeight=100,
        domLayout='autoHeight'
    )

    gb.configure_default_column(editable=True, filter=True, groupable=True)
    vgo = gb.build()
    grid_response = AgGrid(df, gridOptions=vgo, theme='streamlit', allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

    # Save changes button
    if st.button("Save Changes"):

        updated_df = pd.DataFrame(grid_response['data']).reset_index(drop=True)
        if 'Status' not in updated_df.columns:
            st.error("'Status' column not found in the updated data!")
            return

        # Load original data
        with open(JSON_FILE_PATH, 'r') as file:
            original_data = json.load(file)

        # Update only the Status column
        for i, record in enumerate(original_data):
            record['Status'] = updated_df.at[i, 'Status']

        # Save updated data back to JSON
        with open(JSON_FILE_PATH, 'w') as f:
            json.dump(original_data, f, indent=4)

        st.success("Status updated successfully!")

    # Inject CSS for modal overflow
    st.markdown("""
        <style>
        .ag-root-wrapper, .streamlit-expander, .block-container {
            overflow: visible !important;
            position: static !important;
        }

        .modal {
            z-index: 99999 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Test My URL", page_icon=":ladybug:", layout="wide")
    st.title("Test my URL :ladybug:")

    # Load JSON data
    if JSON_FILE_PATH.exists():
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
        df = pd.json_normalize(data)
    else:
        st.error("JSON file not found!")
        return

    display_ag_grid(df)


if __name__ == "__main__":
    main()
########################################################################################################################################################################################################################
import datetime
import json
import streamlit as st
from pathlib import Path
import pandas as pd
from qa_db import DBManager
import base64
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode

# Constants
SITE_CONFIG_PATH = Path('./SiteConfig')
RESULTS_PATH = Path('./Result')

# Initialize Database Manager
dbm = DBManager()

# Ensure the siteconfig directory exists
SITE_CONFIG_PATH.mkdir(parents=True, exist_ok=True)

# Ensure the Results directory exists
RESULTS_PATH.mkdir(parents=True, exist_ok=True)


def get_toml_files():
    """Retrieve all .toml files from SITE_CONFIG_PATH."""
    return [f.stem for f in SITE_CONFIG_PATH.glob('*.toml')]


def encode_image_to_base64(image_path):
    """Encode an image to base64."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return None


def display_ag_grid(df, json_file_path):
    """Display DataFrame in an AG Grid with editable Status column and image thumbnails."""

    # Convert image paths to base64 and store filenames
    for idx, row in df.iterrows():
        if isinstance(row['Proof_Path'], list) and row['Proof_Path']:
            base64_images = [encode_image_to_base64(path) for path in row['Proof_Path']]
            filenames = [os.path.basename(path) for path in row['Proof_Path']]
            df.at[idx, 'Proof_Path'] = [{"src": b64, "name": fname} for b64, fname in zip(base64_images, filenames)]

    # JavaScript for thumbnail with zoom and modal navigation
    show_image = JsCode("""
        class ThumbnailRenderer {
            init(params) {
                this.eGui = document.createElement('div');
                this.eGui.style.display = 'flex';
                this.eGui.style.justifyContent = 'center';
                this.eGui.style.alignItems = 'center';

                const images = params.value;
                if (!images || !images.length) return;

                const img = document.createElement('img');
                img.setAttribute('src', images[0].src);
                img.setAttribute('width', '200');
                img.style.cursor = 'pointer';
                img.style.transition = 'transform 0.3s ease';

                img.addEventListener('mouseover', () => img.style.transform = 'scale(1.1)');
                img.addEventListener('mouseout', () => img.style.transform = 'scale(1)');

                img.addEventListener('click', () => this.openModal(images));
                this.eGui.appendChild(img);
            }

            openModal(images) {
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100vw';
                modal.style.height = '100vh';
                modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                modal.style.display = 'flex';
                modal.style.justifyContent = 'center';
                modal.style.alignItems = 'center';
                modal.style.flexDirection = 'column';
                modal.style.zIndex = '99999';
                modal.style.overflow = 'auto';

                const imageName = document.createElement('div');
                imageName.style.position = 'absolute';
                imageName.style.top = '10px';
                imageName.style.left = '10px';
                imageName.style.color = 'white';
                imageName.style.fontSize = '1.2rem';
                imageName.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                imageName.style.padding = '8px';
                imageName.style.borderRadius = '5px';
                imageName.innerText = images[0].name;
                modal.appendChild(imageName);

                const enlargedImg = document.createElement('img');
                enlargedImg.setAttribute('src', images[0].src);
                enlargedImg.style.maxWidth = '80vw';
                enlargedImg.style.maxHeight = '80vh';
                enlargedImg.style.objectFit = 'contain';
                modal.appendChild(enlargedImg);

                let currentIndex = 0;
                this.addNavigation(modal, images, enlargedImg, imageName, currentIndex);

                document.body.appendChild(modal);
                modal.tabIndex = -1;
                modal.focus();
            }

            addNavigation(modal, images, enlargedImg, imageName, currentIndex) {
                const navContainer = document.createElement('div');
                navContainer.style.display = 'flex';
                navContainer.style.justifyContent = 'space-between';
                navContainer.style.alignItems = 'center';
                navContainer.style.width = '100%';
                navContainer.style.position = 'absolute';
                navContainer.style.top = '50%';

                const leftArrow = this.createArrow('&#9664;', () => {
                    currentIndex = (currentIndex - 1 + images.length) % images.length;
                    enlargedImg.setAttribute('src', images[currentIndex].src);
                    imageName.innerText = images[currentIndex].name;
                });

                const rightArrow = this.createArrow('&#9654;', () => {
                    currentIndex = (currentIndex + 1) % images.length;
                    enlargedImg.setAttribute('src', images[currentIndex].src);
                    imageName.innerText = images[currentIndex].name;
                });

                navContainer.appendChild(leftArrow);
                navContainer.appendChild(rightArrow);
                modal.appendChild(navContainer);

                modal.addEventListener('keydown', (event) => {
                    if (event.key === 'ArrowRight') rightArrow.click();
                    else if (event.key === 'ArrowLeft') leftArrow.click();
                    else if (event.key === 'Escape') modal.remove();
                });

                modal.addEventListener('click', (event) => {
                    if (event.target === modal) modal.remove();
                });
            }

            createArrow(symbol, onClick) {
                const arrow = document.createElement('button');
                arrow.innerHTML = symbol;
                arrow.style.fontSize = '2rem';
                arrow.style.background = 'none';
                arrow.style.color = 'white';
                arrow.style.border = 'none';
                arrow.style.cursor = 'pointer';
                arrow.style.padding = '20px';
                arrow.addEventListener('click', onClick);
                return arrow;
            }

            getGui() {
                return this.eGui;
            }
        }
    """)

    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df)
    gb.configure_column(
        "Proof_Path",
        cellRenderer=show_image,
        valueFormatter=JsCode("""
            function(params) {
                return params.value && params.value.length ? params.value[0].name : '';
            }
        """),
        editable=False
    )

    # Configure editable Status column
    status_options = ['Passed', 'Failed', 'Error']
    gb.configure_column(
        'Status',
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': status_options},
        cellStyle={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
        width=150
    )

    # Grid Options
    gb.configure_grid_options(
        groupDisplayType='multipleColumns',
        rowGroupPanelShow='always',
        enableGroupEdit=True,
        groupDefaultExpanded=-1,
        rowSelection='single',  # Allow selecting a single row
        alwaysShowHorizontalScroll=True,
        cellSelection=True,
        pagination=True,
        paginationPageSize=10,
        paginationPageSizeSelector=[10, 20, 50, 100],
        rowHeight=100,
        domLayout='autoHeight'
    )

    gb.configure_default_column(editable=True, filter=True, groupable=True)
    vgo = gb.build()
    grid_response = AgGrid(df, gridOptions=vgo, theme='streamlit', allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

    # Save changes button
    if st.button("Save Changes"):
        updated_df = pd.DataFrame(grid_response['data']).reset_index(drop=True)

        # Load original data
        with open(json_file_path, 'r') as file:
            original_data = json.load(file)

        # Update only the Status column
        for i, record in enumerate(original_data):
            record['Status'] = updated_df.at[i, 'Status']

        # Save updated data back to JSON
        with open(json_file_path, 'w') as f:
            json.dump(original_data, f, indent=4)

        st.success("Status updated successfully!")

    # Inject CSS for modal overflow
    st.markdown("""
        <style>
        .ag-root-wrapper, .streamlit-expander, .block-container {
            overflow: visible !important;
            position: static !important;
        }

        .modal {
            z-index: 99999 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def list_json_files():
    """Recursively list all JSON files from the Results directory."""
    data = []
    if RESULTS_PATH.exists():
        for json_file in RESULTS_PATH.rglob('*.json'):
            parts = json_file.parts
            if len(parts) >= 4:
                subscription = parts[-4]
                date_time = parts[-3]
                env = parts[-2]
                data.append({
                    "Subscription": subscription,
                    "Env": env,
                    "DateTime": date_time,
                    "FilePath": str(json_file),
                    "View": "View"
                })
    return pd.DataFrame(data)


def main():
    """Main Streamlit application."""
    st.set_page_config(page_title="Test My URL", page_icon=":ladybug:", layout="wide")
    st.title("Test my URL :ladybug:")

    df_files = list_json_files()
    if not df_files.empty:
        gb = GridOptionsBuilder.from_dataframe(df_files)
        gb.configure_column("FilePath", hide=True)  # Hide FilePath column
        gb.configure_selection('single')  # Enable single row selection
        gb.configure_column("View", header_name="View", cellRenderer=JsCode("""
            class ViewRenderer {
                init(params) {
                    this.eGui = document.createElement('span');
                    this.eGui.innerText = 'View';
                    this.eGui.style.color = 'blue';
                    this.eGui.style.cursor = 'pointer';
                    this.eGui.addEventListener('click', () => {
                        params.api.deselectAll();
                        params.node.setSelected(true);
                    });
                }
                getGui() {
                    return this.eGui;
                }
            }
        """))
        grid_options = gb.build()

        grid_response = AgGrid(df_files, gridOptions=grid_options, theme='streamlit', allow_unsafe_jscode=True, fit_columns_on_grid_load=True)

        selected_row = grid_response.get('selected_rows', [])
        if len(selected_row) > 0:
            selected_file = selected_row[0].get('FilePath')
            with open(selected_file, 'r') as file:
                data = json.load(file)
                df = pd.json_normalize(data)
                display_ag_grid(df, selected_file)

    else:
        st.write("No JSON files found in the Results directory.")


if __name__ == "__main__":
    main()






































##############################################################################################################################################################################################################
import streamlit as st
import pandas as pd
from pathlib import Path
import json
from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode

# Mock display_aggrid function (replace with your actual AG Grid display logic)
def display_aggrid(data):
    st.subheader("JSON Data")
    AgGrid(data, height=300)

# Path to the Results folder
RESULTS_FOLDER = Path('./Result')

# Function to scan the Results directory and gather JSON file information
def get_json_files_info(results_folder):
    file_info_list = []

    # Iterate over each subscription folder
    for subscription_folder in results_folder.iterdir():
        if subscription_folder.is_dir():
            subscription_name = subscription_folder.name

            # Iterate over each datetime folder inside the subscription folder
            for datetime_folder in subscription_folder.iterdir():
                if datetime_folder.is_dir():
                    datetime_value = datetime_folder.name

                    # Check for environment folders (dev, prod, stage)
                    for env_folder in datetime_folder.iterdir():
                        if env_folder.is_dir() and env_folder.name in ['dev', 'prod', 'stage']:
                            environment = env_folder.name

                            # Look for JSON files in the environment folder
                            for json_file in env_folder.glob('*.json'):
                                file_info_list.append({
                                    'Subscription': subscription_name,
                                    'Environment': environment,
                                    'DateTime': datetime_value,
                                    'File Path': str(json_file.relative_to(results_folder)),
                                    'View': 'Click to View'
                                })

    return pd.DataFrame(file_info_list)

# Get JSON file information
json_files_df = get_json_files_info(RESULTS_FOLDER)

# Configure AG Grid
gb = GridOptionsBuilder.from_dataframe(json_files_df)
gb.configure_pagination(paginationAutoPageSize=True)  # Enable pagination
gb.configure_side_bar()  # Enable sidebar for filters
gb.configure_default_column(editable=False, groupable=True)

# Configure the "View" column to be clickable without custom JS
gb.configure_column(
    "View",
    header_name="View",
    cellRenderer='agGroupCellRenderer',  # Use AG Grid's built-in group cell renderer
    pinned='right'  # Pin the View column to the right for easy access
)

# Enable single-row selection (clicking the "View" text will select the row)
gb.configure_selection(selection_mode="single", use_checkbox=False)

grid_options = gb.build()

# Display AG Grid
st.title("Results Viewer")
grid_response = AgGrid(
    json_files_df,
    gridOptions=grid_options,
    update_mode=GridUpdateMode.SELECTION_CHANGED,  # Detect selection changes
    height=400,
    fit_columns_on_grid_load=True,
)

# Handle row selection (when "View" is clicked)
selected_rows = grid_response['selected_rows']
st.write(selected_rows)  # Debug: Show the selected rows

# Check if selection is not empty
if selected_rows is not None and len(selected_rows) > 0:
    # Access the first selected row (Pandas DataFrame requires iloc)
    selected_row = selected_rows.iloc[0]  # Correct way to access first row
    st.write(selected_row)  # Debug: Show the first selected row

    # Get file path from the selected row
    selected_file_path = RESULTS_FOLDER / selected_row['File Path']
    st.write(f"Selected File Path: {selected_file_path}")
    st.success(f"Loading file: {selected_file_path.name}")

    # Load and display JSON data
    with open(selected_file_path, 'r') as file:
        json_data = json.load(file)

    display_aggrid(pd.json_normalize(json_data))
else:
    st.write("No file selected.")


#########################################################################################################################################################################################
import datetime
import json

import pytest
import streamlit as st
from pathlib import Path
import pandas as pd
from qa_db import DBManager
import base64
import os
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode, StAggridTheme

# Constants
SITE_CONFIG_PATH = Path('./SiteConfig')
JSON_FILE_PATH = Path("Result/cardio/05_02_2025_08_27_23/dev/cardio_dev_results.json")
input_ui = {'name': None, 'dev': None, 'stage': None, 'prod': None}
env_details = {
    "Subscription": "Paid",
    "Execution Date and Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    "Prod_Url": "http://example.com/prod",
    "Drupal/PHP ver": "10.4/8.3",
    "Status": "QA Approved",
    "Total_Execution_Time": "00:10:00",
    "Browser": "Chrome",
    "Browser ver": "v25.02"}
options = ["Development", "Stage", "Production"]
site_details = {}
env_details_ui = {}

site_details['Subscription'] = env_details["Subscription"]
site_details['Prod_Url'] = env_details["Prod_Url"]
site_details['Drupal/PHP ver'] = env_details["Drupal/PHP ver"]
site_details['Status'] = env_details["Status"]

env_details_ui["Execution Date and Time"] = env_details["Execution Date and Time"]
env_details_ui["Total_Execution_Time"] = env_details["Total_Execution_Time"]
env_details_ui["Browser"] = env_details["Browser"]
env_details_ui["Browser ver"] = env_details["Browser ver"]

# Initialize Database Manager
dbm = DBManager()

# Ensure the siteconfig directory exists
SITE_CONFIG_PATH.mkdir(parents=True, exist_ok=True)


def get_toml_files():
    """Retrieve all .toml files from SITE_CONFIG_PATH."""
    return [f.stem for f in SITE_CONFIG_PATH.glob('*.toml')]


def encode_image_to_base64(image_path):
    """Encode an image to base64."""
    if os.path.exists(image_path):
        with open(image_path, "rb") as img_file:
            return f"data:image/png;base64,{base64.b64encode(img_file.read()).decode()}"
    return None


def display_ag_grid(df):
    """Display DataFrame in an AG Grid with editable Status column and image thumbnails."""

    # Convert image paths to base64 and store filenames
    for idx, row in df.iterrows():
        if isinstance(row['Proof_Path'], list) and row['Proof_Path']:
            base64_images = [encode_image_to_base64(path) for path in row['Proof_Path']]
            filenames = [os.path.basename(path) for path in row['Proof_Path']]
            df.at[idx, 'Proof_Path'] = [{"src": b64, "name": fname} for b64, fname in zip(base64_images, filenames)]

    # Configure AG Grid
    gb = GridOptionsBuilder.from_dataframe(df)

    # JavaScript for thumbnail with zoom and modal navigation
    show_image = JsCode("""
            class ThumbnailRenderer {
                init(params) {
                    this.eGui = document.createElement('div');
                    this.eGui.style.display = 'flex';
                    this.eGui.style.justifyContent = 'center';
                    this.eGui.style.alignItems = 'center';

                    const images = params.value;
                    if (!images || !images.length) return;

                    const img = document.createElement('img');
                    img.setAttribute('src', images[0].src);
                    img.setAttribute('width', '200');
                    img.style.cursor = 'pointer';
                    img.style.transition = 'transform 0.3s ease';

                    img.addEventListener('mouseover', () => img.style.transform = 'scale(1.1)');
                    img.addEventListener('mouseout', () => img.style.transform = 'scale(1)');

                    img.addEventListener('click', () => this.openModal(images));
                    this.eGui.appendChild(img);
                }

                openModal(images) {
                    const modal = document.createElement('div');
                    modal.style.position = 'fixed';
                    modal.style.top = '0';
                    modal.style.left = '0';
                    modal.style.width = '100vw';
                    modal.style.height = '100vh';
                    modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                    modal.style.display = 'flex';
                    modal.style.justifyContent = 'center';
                    modal.style.alignItems = 'center';
                    modal.style.flexDirection = 'column';
                    modal.style.zIndex = '99999';
                    modal.style.overflow = 'auto';

                    const imageName = document.createElement('div');
                    imageName.style.position = 'absolute';
                    imageName.style.top = '10px';
                    imageName.style.left = '10px';
                    imageName.style.color = 'white';
                    imageName.style.fontSize = '1.2rem';
                    imageName.style.backgroundColor = 'rgba(0, 0, 0, 0.5)';
                    imageName.style.padding = '8px';
                    imageName.style.borderRadius = '5px';
                    imageName.innerText = images[0].name;
                    modal.appendChild(imageName);

                    const enlargedImg = document.createElement('img');
                    enlargedImg.setAttribute('src', images[0].src);
                    enlargedImg.style.maxWidth = '80vw';
                    enlargedImg.style.maxHeight = '80vh';
                    enlargedImg.style.objectFit = 'contain';
                    modal.appendChild(enlargedImg);

                    let currentIndex = 0;
                    this.addNavigation(modal, images, enlargedImg, imageName, currentIndex);

                    document.body.appendChild(modal);
                    modal.tabIndex = -1;
                    modal.focus();
                }

                addNavigation(modal, images, enlargedImg, imageName, currentIndex) {
                    const navContainer = document.createElement('div');
                    navContainer.style.display = 'flex';
                    navContainer.style.justifyContent = 'space-between';
                    navContainer.style.alignItems = 'center';
                    navContainer.style.width = '100%';
                    navContainer.style.position = 'absolute';
                    navContainer.style.top = '50%';

                    const leftArrow = this.createArrow('&#9664;', () => {
                        currentIndex = (currentIndex - 1 + images.length) % images.length;
                        enlargedImg.setAttribute('src', images[currentIndex].src);
                        imageName.innerText = images[currentIndex].name;
                    });

                    const rightArrow = this.createArrow('&#9654;', () => {
                        currentIndex = (currentIndex + 1) % images.length;
                        enlargedImg.setAttribute('src', images[currentIndex].src);
                        imageName.innerText = images[currentIndex].name;
                    });

                    navContainer.appendChild(leftArrow);
                    navContainer.appendChild(rightArrow);
                    modal.appendChild(navContainer);

                    modal.addEventListener('keydown', (event) => {
                        if (event.key === 'ArrowRight') rightArrow.click();
                        else if (event.key === 'ArrowLeft') leftArrow.click();
                        else if (event.key === 'Escape') modal.remove();
                    });

                    modal.addEventListener('click', (event) => {
                        if (event.target === modal) modal.remove();
                    });
                }

                createArrow(symbol, onClick) {
                    const arrow = document.createElement('button');
                    arrow.innerHTML = symbol;
                    arrow.style.fontSize = '2rem';
                    arrow.style.background = 'none';
                    arrow.style.color = 'white';
                    arrow.style.border = 'none';
                    arrow.style.cursor = 'pointer';
                    arrow.style.padding = '20px';
                    arrow.addEventListener('click', onClick);
                    return arrow;
                }

                getGui() {
                    return this.eGui;
                }
            }
        """)
    gb.configure_column(
        "Proof_Path",
        cellRenderer=show_image,
        valueFormatter=JsCode("""
            function(params) {
                return params.value && params.value.length ? params.value[0].name : '';
            }
        """),
        editable=False
    )

    # Configure editable Status column
    status_options = ['Passed', 'Failed', 'Error']
    gb.configure_column(
        'Status',
        editable=True,
        cellEditor='agSelectCellEditor',
        cellEditorParams={'values': status_options},
        cellStyle={'textAlign': 'center', 'display': 'flex', 'alignItems': 'center', 'justifyContent': 'center'},
        width=150
    )

    # gb.configure_column(
    #     "Actual_Result",
    #     cellEditor="agLargeTextCellEditor",
    #     cellEditorParams={"values": ["a", "b", "c"]},
    #     cellEditorPopup=True,
    # )

    show_data_modal = JsCode("""
        class DataCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.style.cursor = 'pointer';
                this.eGui.style.color = 'blue';
                this.eGui.style.textDecoration = 'underline';
                this.eGui.innerText = 'View Data';
                this.eGui.addEventListener('click', () => this.openModal(params.value));
            }

            openModal(data) {
                const modal = document.createElement('div');
                modal.style.position = 'fixed';
                modal.style.top = '0';
                modal.style.left = '0';
                modal.style.width = '100vw';
                modal.style.height = '100vh';
                modal.style.backgroundColor = 'rgba(0, 0, 0, 0.8)';
                modal.style.display = 'flex';
                modal.style.justifyContent = 'center';
                modal.style.alignItems = 'center';
                modal.style.flexDirection = 'column';
                modal.style.zIndex = '99999';
                modal.style.overflow = 'auto';

                // Create content box after modal is created
                const contentBox = document.createElement('div');
                contentBox.style.background = 'white';
                contentBox.style.color = 'black';
                contentBox.style.padding = '20px';
                contentBox.style.borderRadius = '8px';
                contentBox.style.maxWidth = '80vw';
                contentBox.style.maxHeight = '80vh';
                contentBox.style.overflow = 'auto';
                contentBox.style.whiteSpace = 'pre-wrap';
                contentBox.style.wordBreak = 'break-word';
                contentBox.style.fontFamily = 'monospace';

                // Function to render data with line numbers
                const renderData = (data) => {
                    if (typeof data === 'string') {
                        return this.addLineNumbers(data);
                    }
                    try {
                        let parsedData = JSON.stringify(data, null, 4);
                        return this.addLineNumbers(parsedData);
                    } catch (error) {
                        return this.addLineNumbers(JSON.stringify(data, null, 4));
                    }
                };

                // Set innerHTML of contentBox
                contentBox.innerHTML = `<pre style="font-size: 14px;">${renderData(data)}</pre>`;

                // Create Close button
                const closeButton = document.createElement('button');
                closeButton.innerText = 'Close';
                closeButton.style.marginTop = '10px';
                closeButton.style.padding = '8px 16px';
                closeButton.style.background = 'red';
                closeButton.style.color = 'white';
                closeButton.style.border = 'none';
                closeButton.style.cursor = 'pointer';
                closeButton.style.borderRadius = '5px';
                closeButton.addEventListener('click', () => modal.remove());

                // Append elements to modal
                modal.appendChild(contentBox);
                modal.appendChild(closeButton);
                document.body.appendChild(modal);
            }

            // Function to add line numbers to the content
            addLineNumbers(code) {
                const lines = code.split('\\n');
                return lines.map((line, index) => 
                    `<span style="color: grey;">${index + 1}</span>  ${line}`
                ).join('\\n');
            }

            getGui() {
                return this.eGui;
            }
        }
    """)

    gb.configure_column(
        "Actual_Result",
        cellRenderer=show_data_modal,
        editable=False
    )

    # Grid Options
    gb.configure_grid_options(
        groupDisplayType='multipleColumns',
        rowGroupPanelShow='always',
        enableGroupEdit=True,
        groupDefaultExpanded=-1,
        rowSelection={
            "mode": "multiRow",
            "checkboxes": True,
            "headerCheckbox": True,
            "selectAll": "filtered"
        },
        alwaysShowHorizontalScroll=True,
        cellSelection=True,
        pagination=True,
        paginationPageSize=10,
        paginationPageSizeSelector=[10, 20, 50, 100],
        rowHeight=100,
        domLayout='autoHeight'
    )

    # gb.configure_default_column(editable=True, filter=True, groupable=True)
    gb.configure_default_column(
        groupable=True, value=True, enableRowGroup=True, editable=True, filter=True,
    )
    vgo = gb.build()

    jsfncbtn = """
        class BtnCellRenderer {
            init(params) {
                this.params = params;
                this.eGui = document.createElement('div');
                this.eGui.innerHTML = `
                 <span>
                    <button id='click-button' 
                        class='btn-simple' 
                        style='color: ${this.params.color}; background-color: ${this.params.background_color}'>View Result</button>
                 </span>
                `;
                this.eButton = this.eGui.querySelector('#click-button');
                this.btnClickedHandler = this.btnClickedHandler.bind(this);
                this.eButton.addEventListener('click', this.btnClickedHandler);
            }

            getGui() {
                return this.eGui;
            }

            refresh() {
                return true;
            }

            destroy() {
                if (this.eButton) {
                    this.eGui.removeEventListener('click', this.btnClickedHandler);
                }
            }

            btnClickedHandler(event) {
                if (confirm('Are you sure?') == true) {
                    if(this.params.getValue() == 'clicked') {
                        this.refreshTable('');
                    } else {
                        this.refreshTable('clicked');
                    }
                        console.log(this.params);
                        console.log(this.params.getValue());
                    }
                }

            refreshTable(value) {
                this.params.setValue(value);
            }
        };
        """
    BtnCellRenderer = JsCode(jsfncbtn)
    vgo["columnDefs"].append(
        {
            "field": "View",
            "headerName": "View",
            "cellRenderer": BtnCellRenderer,
            "cellRendererParams": {
                "color": "black",
                "background_color": "white",
                "text-align": "center",
            },
        }
    )

    # custom_theme = (
    #     StAggridTheme.withParams(
    #     {
    #     'backgroundColor': '#FFE8E0',
    #     'foregroundColor': '#361008CC',
    #     'browserColorScheme': 'light',
    #     }
    #
    # ).withParams(
    #     {
    #         'backgroundColor': '#201008',
    #         'foregroundColor': '#FFFFFFCC',
    #         'browserColorScheme': 'dark',
    #     },
    #     'dark-red'))

    # custom_theme = (
    #     StAggridTheme(base="quartz")
    #     .withParams(
    #     )
    #     .withParts({
    #         'backgroundColor': '#201008',
    #         'foregroundColor': '#FFFFFFCC',
    #         'browserColorScheme': 'dark',
    #     },
    #         'dark-red'))
    if "View" not in df.columns:
        df["View"] = ""  # Initialize as empty column

    grid_response = AgGrid(df, gridOptions=vgo,  allow_unsafe_jscode=True,
                           fit_columns_on_grid_load=True)
    if "View" in grid_response.data.columns:
        st.write(grid_response.data[grid_response.data["View"] == "clicked"])
    else:
        st.warning("No 'View' column found in the data.")

    # Save changes button
    if st.button("Save Changes"):

        updated_df = pd.DataFrame(grid_response['data']).reset_index(drop=True)
        if 'Status' not in updated_df.columns:
            st.error("'Status' column not found in the updated data!")
            return

        # Load original data
        with open(JSON_FILE_PATH, 'r') as file:
            original_data = json.load(file)

        # Update only the Status column
        for i, record in enumerate(original_data):
            record['Status'] = updated_df.at[i, 'Status']

        # Save updated data back to JSON
        with open(JSON_FILE_PATH, 'w') as f:
            json.dump(original_data, f, indent=4)

        st.success("Status updated successfully!")

    # Inject CSS for modal overflow
    st.markdown("""
        <style>
        .ag-root-wrapper, .streamlit-expander, .block-container {
            overflow: visible !important;
            position: static !important;
        }

        .modal {
            z-index: 99999 !important;
        }
        </style>
    """, unsafe_allow_html=True)


def test_run():
    # Get list of existing files
    existing_files = get_toml_files()

    sub, env = st.columns([0.6, 0.4], vertical_alignment="bottom")
    with sub:
        # with st.expander("Test Execution", expanded=True):
        config_file_selected = st.selectbox(label='Subscriptions', options=existing_files, index=None,
                                            placeholder="Select or Add Configuration Files",
                                            disabled=False, label_visibility="visible")
    with env:
        if config_file_selected:
            selection = st.pills("Environments", options, selection_mode="multi", disabled=False)
        else:
            selection = []
            selection = st.pills("Environments", options, selection_mode="multi", disabled=True)
    file_path_sel, run_btn = st.columns([0.6, 0.4], vertical_alignment="bottom")
    # with leftl:
    #
    #     if config_file_selected:
    #         selection = st.pills("Environments", options, selection_mode="multi", disabled=False)
    #     else:
    #         selection = []
    #         selection = st.pills("Environments", options, selection_mode="multi", disabled=True)
    with file_path_sel:

        if config_file_selected:
            file_path = st.file_uploader("Choose a file", type=['xlsx'], disabled=True, )
        else:
            file_path = st.file_uploader("Choose a file", type=['xlsx'], disabled=False)

    with run_btn:
        st.download_button("Download Excel", data=".\InputFiles\data1.xlsx", file_name="data1.xlsx",
                           use_container_width=True)

        # Every form must have a submit button.
        if config_file_selected or file_path:
            submitted = st.button("Run 	:arrow_forward:", use_container_width=True, disabled=False)
            if submitted:

                input_ui['name'] = config_file_selected
                if 'Prduction' in selection:
                    input_ui['prod'] = 1
                if 'Stage' in selection:
                    input_ui['stage'] = 1
                if 'Development' in selection:
                    input_ui['dev'] = 1
                st.write(input_ui)
                pytest.main(['.\\test_run.py', '--input_file=.\\InputFile\\data1.xlsx'])
            df = pd.DataFrame(input_ui, index=[1])
        else:
            st.button("Run 	:arrow_forward:", use_container_width=True, disabled=True)


def main():
    st.set_page_config(page_title="Test My URL", page_icon=":ladybug:", layout="wide", initial_sidebar_state="auto",
                       menu_items=None)

    # Streamlit app setup
    st.title("Test my URL :ladybug:")

    @st.dialog("Cast your vote", width="large")
    def vote():
        st.write(f"Please select a subscription")
        test_run()
        # if st.button("Submit"):
        #     st.rerun()

    if "run" not in st.session_state:
        if st.button("Run Script"):
            vote()
    else:
        f"You voted for {st.session_state.vote['item']} because {st.session_state.vote['reason']}"

    leftde, rightde = st.columns([0.5, 0.5], vertical_alignment="center")

    with leftde:
        st.data_editor(site_details, use_container_width=True)
    with rightde:
        st.data_editor(env_details_ui, use_container_width=True)

    col0, col1, col2, col3, col4, col5, col6 = st.columns([0.02, 0.15, 0.15, 0.15, 0.15, 0.15, 0.02])
    col1.metric("Temperature", "70 °F", "1.2 °F")
    col2.metric("Wind", "9 mph", "-8%")
    col3.metric("Humidity", "86%", "4%")
    col4.metric("Turbulence", "86%", "-4%")
    col5.metric("AQI", "86%", "130")

    # Load JSON data
    if JSON_FILE_PATH.exists():
        with open(JSON_FILE_PATH, 'r') as file:
            data = json.load(file)
        df = pd.json_normalize(data)
    else:
        st.error("JSON file not found!")
        return

    display_ag_grid(df)


if __name__ == "__main__":
    main()
