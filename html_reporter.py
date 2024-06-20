import json
import datetime
import platform
from selenium import webdriver

# Read JSON files
# with open('environment.json', 'r') as f:
#     environment_data = json.load(f)

with open('comparison.json', 'r') as f:
    comparison_data = json.load(f)

with open('details.json', 'r') as f:
     details_data = json.load(f)


# CSS styles
css_styles = '''
body {
  font-family: Helvetica, Arial, sans-serif;
  font-size: 12px;
  min-width: 800px;
  color: #999;
}

h1 {
  font-size: 24px;
  color: black;
}

h2 {
  font-size: 16px;
  color: black;
}

p {
  color: black;
}

a {
  color: #999;
}

table {
  border-collapse: collapse;
  width: 100%;
}

.metric-card {
  display: inline-block;
  border-radius: 8px;
  padding: 20px;
  margin: 10px;
  text-align: center;
  width: 200px;
  cursor: pointer;
  color: white;
}

.metric-card.passed {
  background-color: #4caf50;
}

.metric-card.failed {
  background-color: #f44336;
}

.metric-card.error {
  background-color: #ff9800;
}

.metric-card.existing {
  background-color: #2196f3;
}

#results-table {
  border: 1px solid #e6e6e6;
  color: #999;
  font-size: 12px;
  width: 100%;
}

#results-table th,
#results-table td {
  padding: 5px;
  border: 1px solid #e6e6e6;
  text-align: left;
}

#results-table th {
  font-weight: bold;
}

.collapsible:hover {
  cursor: pointer;
  color: #007bff;
}

.collapsible {
  color: black;
}

.collapsible::after {
  content: " \\25BC";
}

.collapsible.expanded::after {
  content: " \\25B2";
}

.extras-row.hidden {
  display: none;
}

.media-container {
  display: flex;
  align-items: center;
}

.media-container__nav--left, .media-container__nav--right {
  cursor: pointer;
  padding: 0 10px;
  user-select: none;
}

.media-container__viewport {
  flex-grow: 1;
  text-align: center;
}

.media-container__viewport img, .media-container__viewport video {
  max-width: 100%;
  max-height: 300px;
}
'''



# HTML template with placeholders for environment and result table
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>QA Automation Report</title>
    <style>
        {css_styles}
    </style>
    <script>
        function toggleDetails(id) {{
            var row = document.getElementById(id);
            if (row.classList.contains('hidden')) {{
                row.classList.remove('hidden');
            }} else {{
                row.classList.add('hidden');
            }}
        }}

        function filterResults(status) {{
            var rows = document.getElementsByClassName('results-table-row');
            for (var i = 0; i < rows.length; i++) {{
                if (status === 'all' || rows[i].classList.contains(status)) {{
                    rows[i].style.display = '';
                }} else {{
                    rows[i].style.display = 'none';
                }}
            }}
        }}
    </script>
</head>
<body>
    <div class="container">
        <h1>QA Automation Report</h1>
        <div id="environment">
            <h2>Environment</h2>
            <table>
                <tr>
                    <td>
                        <table>
                            <tr><td>Site</td><td>{Site}</td></tr>
                            <tr><td>Subscription</td><td>{Subscription}</td></tr>
                            <tr><td>Prod Url</td><td>{Prod_Url}</td></tr>
                            <tr><td>Stage Url</td><td>{Stage_Url}</td></tr>
                            <tr><td>Dev Url</td><td>{Dev_Url}</td></tr>
                        </table>
                    </td>
                    <td>
                        <table>
                            <tr><td>Environment</td><td>{Platform}</td></tr>
                            <tr><td>Execution Date and Time</td><td>{Execution_Date_and_Time}</td></tr>
                            <tr><td>Total Execution Time</td><td>{Total_Execution_Time}</td></tr>
                            <tr><td>Browser</td><td>{Browser}</td></tr>
                            <tr><td>Browser + ver.</td><td>{Browser_ver}</td></tr>
                        </table>
                    </td>
                </tr>
            </table>
        </div>
        <div class="summary">
            <h2>Summary</h2>
            <div class="metric-card passed" onclick="filterResults('passed')">
                <h3>Passed</h3>
                <p>{passed}</p>
            </div>
            <div class="metric-card failed" onclick="filterResults('failed')">
                <h3>Failed</h3>
                <p>{failed}</p>
            </div>
            <div class="metric-card existing" onclick="filterResults('existing')">
                <h3>Existing Issues</h3>
                <p>{xfailed}</p>
            </div>
            <div class="metric-card error" onclick="filterResults('error')">
                <h3>Error</h3>
                <p>{skipped}</p>
            </div>
        </div>
        <div class="results">
            <h2>Results</h2>
            <table id="results-table">
                <thead id="results-table-head">
                    <tr>
                        <th class="sortable asc" data-column-type="result">Result</th>
                        <th class="sortable" data-column-type="testId">Test</th>
                        <!-- Additional columns for environments based on details.json -->
                        {env_columns}
                        <th>Links</th>
                    </tr>
                </thead>
                <tbody>
                    {result_rows}
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
'''




# Environment details
env_details = {
    "Site": "Example Site",
    "Subscription": "Paid",
    "Execution Date and Time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    "Prod_Url": "https://prod.example.com",
    "Stage_Url": "https://stage.example.com",
    "Dev_Url": "https://dev.example.com",
    "Browser": "Chrome",
    "Browser_ver.": f"Chrome {webdriver.Chrome().capabilities['browserVersion']}",
    "Platform": platform.system(),
    "Total_Execution_Time": f"1 seconds"
}

# Generate environment columns in the HTML template
env_columns = ''
for env_name in details_data.get(env_details["Site"], {}).get('test_name', {}).keys():
    env_columns += f'<th>{env_name}</th>'

# Generate result rows
result_rows = ''
for site_name, tests in comparison_data.items():
    for test_name, test_info in tests.items():
        # Start row for this test
        result_rows += f'''
        <tbody class="results-table-row {test_info['status'].lower()}" id="{test_name}">
            <tr class="collapsible" data-id="{test_name}" onclick="toggleDetails('{test_name}-details')">
                <td class="col-result collapsed">{test_info['status']}</td>
                <td class="col-testId">{test_name}</td>
                <!-- Add columns for environments based on details.json -->
                {env_details.get(site_name, {}).get(test_name, {}).get('env_1', {}).get('name', '')}
                {env_details.get(site_name, {}).get(test_name, {}).get('env_2', {}).get('name', '')}
                {env_details.get(site_name, {}).get(test_name, {}).get('env_3', {}).get('name', '')}
                <td class="col-links"></td>
            </tr>
            <tr class="extras-row hidden" id="{test_name}-details">
                <td class="extra" colspan="4">
                    <div class="extraHTML"></div>
                    <div class="media hidden">
                        <div class="media-container">
                            <div class="media-container__nav--left">&lt;</div>
                            <div class="media-container__viewport">
                                <img src="">
                                <video controls="">
                                    <source src="" type="video/mp4">
                                </video>
                            </div>
                            <div class="media-container__nav--right">&gt;</div>
                        </div>
                        <div class="media__name"></div>
                        <div class="media__counter"></div>
                    </div>
                    <div class="logwrapper">
                        <div class="logexpander"></div>
                        <div class="log">{env_details.get(site_name, {}).get(test_name, {}).get('env_1', {}).get('Discription', '')}</div>
                    </div>
                </td>
            </tr>
        </tbody>
        '''





# Fill the template with data
html_content = html_template.format(
    css_styles=css_styles,
    Site=env_details["Site"],
    Subscription=env_details["Subscription"],
    Execution_Date_and_Time="1234",
    Prod_Url=env_details["Prod_Url"],
    Stage_Url=env_details["Stage_Url"],
    Dev_Url=env_details["Dev_Url"],
    Platform=env_details["Platform"],
    Total_Execution_Time=env_details["Total_Execution_Time"],
    Browser=env_details["Browser"],
    Browser_ver="12.23",
    passed="1",
    failed="2",
    xfailed="3",
    skipped="4",
    env_columns=env_columns,
    result_rows=result_rows
)





# Write the HTML content to a file
with open('report6.html', 'w') as f:
    f.write(html_content)

print("Report generated successfully!")
