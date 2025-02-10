import json
import base64
import datetime
import platform
from pathlib import Path
from PIL import Image
from io import BytesIO


def compress_and_encode_image(image_path, max_size=(200, 200), full_quality=False, quality=50, format='WEBP'):
    try:
        img = Image.open(image_path)
        if not full_quality:
            img.thumbnail(max_size)
        buffer = BytesIO()
        img.save(buffer, format="WEBP", quality=quality if not full_quality else 90)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return ""


def generate_html_report(json_file, env_details, output_file):
    """Generate a self-contained HTML report."""
    with open(json_file, 'r') as file:
        test_results = json.load(file)

    summary = {"Passed": 0, "Failed": 0, "Error": 0, "Existing_Issues": 0, 'NA': 0}
    for test in test_results:
        if test["Status"] in summary:
            summary[test["Status"]] += 1

    html_content = f"""<!DOCTYPE html>
    <html lang='en'>
    <head>
        <meta charset='UTF-8'>
        <meta name='viewport' content='width=device-width, initial-scale=1.0'>
        <title>QA Automation Report</title>
        <style>
            body {{ font-family: Arial, sans-serif; font-size: 14px; }}
            h1 {{font-size: 24px; color: black; text-align: center;}}
            h2 {{font-size: 16px; color: black; text-align: center;}}
            .container {{ width: 90%; margin: auto; position: relative; font-family: sans-serif; color: white; }}
            .container::before, .container::after {{ content: ""; background-color: #fab5704c; position: absolute; }}
            .container::before {{ border-radius: 50%; width: 6rem; height: 6rem; top: 30%; right: 7%; }}
            .container::after {{ height: 3rem; top: 8%; right: 5%; border: 1px solid; }}
            .box {{ width: 11.875em; height: 15.875em; padding: 1rem; background-color: rgba(255, 255, 255, 0.074); border: 1px solid rgba(255, 255, 255, 0.222); backdrop-filter: blur(20px); border-radius: 0.7rem; transition: all ease 0.3s; }}
            .box:hover {{ box-shadow: 0px 0px 20px 1px #ffbb763f; border: 1px solid rgba(255, 255, 255, 0.454); }}
            .env-table, .results-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .env-table th, .env-table td, .results-table th, .results-table td {{ border: 1px solid #ddd; padding: 8px; text-align: center; color: #000000;}}
            .env-table th, .results-table th {{ background-color: #444; color: white; }}
            .env-table td, {{border-bottom: 1px solid #ddd; hover {{background-color: coral;}} cursor: pointer;}}
            .summary {{ width: 100%; }}
            .metric-card {{ display: inline-block; padding: 25px; margin: 50px; width: 200px; text-align: center; color: white; border-radius: 25px; cursor: pointer; }}
            .status-badge {{ padding: 10px 20px; border-radius: 5px; color: white; border: none; display: inline-block; text-align: center; width: 70%; font-size: 15px;}}
            .Passed {{ background-color: #4CAF50; text-align: center;}}
            .Failed {{ background-color: #F44336; }}
            .Error {{ background-color: #FF9800; }}
            .NA {{ background-color: #A9A9A9; }}
            .Existing_Issues {{ background-color: #FFEB3B; color: black; }}

            .proof-img {{ width: 50px; height: auto; cursor: pointer; text-align: center;}}
            .modal {{ display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.8); color: white; text-align: center; }}
            .modal-content {{ position: relative; top: 5%; max-width: 90%; max-height: 90%; }}
            .modal-header {{ display: flex; justify-content: space-between; align-items: center; padding: 5px; }}
            .modal img {{ max-width: 90%; max-height: 75%; margin-top: 2%; }}
            .nav-arrow {{ position: absolute; top: 50%; transform: translateY(-50%); font-size: 50px; cursor: pointer; }}
            .left-arrow {{ left: 10px; }}
            .right-arrow {{ right: 10px; }}
            .close-icon {{ font-size: 50px; }}
            .dwn-btn {{ position: absolute; top: 2.5%; transform: translateY(-10%); font-size: 15px; cursor: pointer; right: 50px; }}
            .modal-buttons {{ position: absolute; top: 50%; }}
            .modal-buttons button {{ font-size: 20px; }}

        </style>
        <script>
            let currentImages = [];
            let currentIndex = 0;
            let currentFilenames = []; // Default filename
            function showModal(images, filenames, index) {{
                currentImages = images;
                currentIndex = index;
                currentFilenames = filenames; // Store filename
                updateModalImage();
                document.getElementById('modal-img').src = images[index];
                document.getElementById('image-filename').textContent = filenames[index]; // Display filename
                document.getElementById('image-modal').style.display = 'block';
            }}
            function updateModalImage() {{
                document.getElementById('modal-img').src = currentImages[currentIndex];
                document.getElementById('image-filename').textContent = currentFilenames[currentIndex];
            }}
            function closeModal() {{
                document.getElementById('image-modal').style.display = 'none';
            }}
            function navigate(direction) {{
                if (currentImages.length < 2) return;
                currentIndex = (currentIndex + direction + currentImages.length) % currentImages.length;
                document.getElementById('modal-img').src = currentImages[currentIndex];
                updateModalImage();
            }}
            function filterResults(status) {{
                let rows = document.querySelectorAll('.results-row');
                rows.forEach(row => {{
                    row.style.display = status === 'all' || row.classList.contains(status.toLowerCase()) ? '' : 'none';
                }});
            }}

            function toggleCard(cardClass) {{
                var card = document.querySelector('.' + cardClass);
                if (card.classList.contains('selected')) {{
                    card.classList.remove('selected');
                    filterResults('all');
                }} else {{
                    card.classList.add('selected');
                    filterResults(cardClass);
                }}
            }}
            function downloadImage() {{
                let imgElement = document.getElementById('modal-img');
                let imageUrl = imgElement.src;

                // Check if the image URL is cross-origin and handle accordingly
                if (imageUrl) {{
                    let link = document.createElement('a');
                    link.href = imageUrl;
                    link.download = currentFilenames[currentIndex];
                    document.body.appendChild(link);
                    link.click();
                    document.body.removeChild(link);
                }} else {{
                    console.error('Image URL not found')}}
            }}

        </script>
    </head>
    <body>
        <div>
            <h1>QA Automation Report</h1>


            <h2>Environment Details</h2>
            <table class='env-table'>
                <td >
                    <table class='env-table'>
                        <tr><th colspan="2">Site Details</th></tr>
                        <tr><td>Subscription</td><td>{env_details['Subscription']}</td></tr>
                        <tr><td>Prod Url</td><td>{env_details['Prod_Url']}</td></tr>
                        <tr><td>Stage Url</td><td>{env_details['Stage_Url']}</td></tr>
                        <tr><td>Dev Url</td><td>{env_details['Dev_Url']}</td></tr>
                    </table>
                </td>
                <td>
                    <table class='env-table'>
                        <tr><th colspan="2">Environment Details</th></tr>
                        <tr><td>Execution Date and Time</td><td>{env_details['Execution Date and Time']}</td></tr>
                        <tr><td>Total Execution Time</td><td>{env_details['Total_Execution_Time']}</td></tr>
                        <tr><td>Browser</td><td>{env_details['Browser']}</td></tr>
                        <tr><td>Browser + ver.</td><td>{env_details['Browser']}</td></tr>
                    </table>
                </td>
            </table>

            <h2>Summary</h2>

            <div class="summary">
                <div class="metric-card Passed" onclick="toggleCard('Passed')">
                    <h3>Passed</h3>
                    <p>{summary['Passed']}</p>
                </div>
                <div class="metric-card Failed" onclick="toggleCard('Failed')">
                    <h3>Failed</h3>
                    <p>{summary['Failed']}</p>
                </div>
                <div class="metric-card Existing_Issues" onclick="toggleCard('Existing_Issues')">
                    <h3>Existing Issues</h3>
                    <p>{summary['Existing_Issues']}</p>
                </div>
                <div class="metric-card Error" onclick="toggleCard('Error')">
                    <h3>Error</h3>
                    <p>{summary['Error']}</p>
                </div>
                <div class="metric-card NA" onclick="toggleCard('NA')">
                    <h3>NA</h3>
                    <p>{summary['NA']}</p>
                </div>
            </div>


            <h2>Results</h2>
            <table class='results-table' border='1'>
                <tr><th>Status</th><th>Testcase</th><th>Description</th><th>Data</th><th>Proof</th></tr>
                {''.join([
        f"""
                    <tr class='results-row {test['Status'].lower()}'>
                        <td><span class='status-badge {test['Status']}'>{test['Status']}</span></td>
                        <td>{test['Name']}</td>
                        <td>{test['Description']}</td>
                        <td>{test['Actual_Result']}</td>
                        <td>
                            <img src='data:image/webp;base64,{compress_and_encode_image(test["Proof_Path"][0])}'
                                 width='50'
                                 onclick='showModal(
                                     [{",".join([f"\"data:image/webp;base64,{compress_and_encode_image(img, full_quality=True)}\"" for img in test["Proof_Path"]])}],
                                     [{",".join([f"\"{Path(img).name}\"" for img in test["Proof_Path"]])}], 
                                     0)' />
                        </td>
                        </tr>
                """ for test in test_results])}
            </table>
        </div>
        <div id='image-modal' class='modal'>
            <div class='modal-header'>
                <h3 id="image-filename"></h3> <!-- Display the filename -->
                <button class='dwn-btn' onclick="downloadImage()" style='cursor:pointer;'>Download</button>
                <span class='close-icon' onclick='closeModal()' style='cursor:pointer;'>&#215</span>

            </div>
            <img id='modal-img' class='modal-content'>
            <div class='nav-arrow left-arrow' onclick='navigate(-1)'>&#8249;</div>
            <div class='nav-arrow right-arrow' onclick='navigate(1)'>&#8250;</div>
        </div>
    </body>
    </html>"""

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"Report saved as {output_file}")


# Example Usage
env_details = {
    "Subscription": "Paid",
    "Execution Date and Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    "Prod_Url": "http://example.com/prod",
    "Stage_Url": "http://example.com/stage",
    "Dev_Url": "http://example.com/dev",
    "Total_Execution_Time": "00:10:00",
    "Browser": "Chrome"
}

generate_html_report("./Result/cardio/05_02_2025_08_27_23/dev/cardio_dev_results.json", env_details, "report3.html")