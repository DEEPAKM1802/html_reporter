# import json
# import base64
# import datetime
# import platform
# from pathlib import Path
# from PIL import Image
# from io import BytesIO
#
#
# def compress_and_encode_image(image_path, max_size=(200, 200), quality=50):
#     """Compress and encode an image to base64."""
#     try:
#         img = Image.open(image_path)
#         img.thumbnail(max_size)
#         buffer = BytesIO()
#         img.save(buffer, format="PNG", quality=quality)
#         return base64.b64encode(buffer.getvalue()).decode('utf-8')
#     except Exception as e:
#         print(f"Error processing image {image_path}: {e}")
#         return ""
#
#
# def generate_html_report(json_file, env_details, output_file):
#     """Generate a self-contained HTML report."""
#     with open(json_file, 'r') as file:
#         test_results = json.load(file)
#
#     # Count summary metrics
#     summary = {"Passed": 0, "Failed": 0, "Error": 0, "Existing Issues": 0}
#     for test in test_results:
#         if test["Status"] in summary:
#             summary[test["Status"]] += 1
#
#     html_content = f"""<!DOCTYPE html>
#     <html lang='en'>
#     <head>
#         <meta charset='UTF-8'>
#         <meta name='viewport' content='width=device-width, initial-scale=1.0'>
#         <title>QA Automation Report</title>
#         <style>
#             body {{ font-family: Arial, sans-serif; font-size: 14px; }}
#             .container {{ width: 90%; margin: auto; }}
#             .metric-card {{ display: inline-block; padding: 10px; margin: 5px; width: 150px; text-align: center; color: white; border-radius: 5px; }}
#             .passed {{ background-color: #4CAF50; }}
#             .failed {{ background-color: #F44336; }}
#             .error {{ background-color: #FF9800; }}
#             .existing {{ background-color: #FFEB3B; color: black; }}
#             table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
#             th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
#             .proof-img {{ width: 100px; cursor: pointer; }}
#             .modal {{ display: none; position: fixed; top: 50%; left: 50%; transform: translate(-50%, -50%); background: white; padding: 10px; border: 1px solid black; }}
#         </style>
#         <script>
#             function enlargeImage(src) {{
#                 var modal = document.getElementById('image-modal');
#                 var img = document.getElementById('modal-img');
#                 img.src = src;
#                 modal.style.display = 'block';
#             }}
#             function closeModal() {{
#                 document.getElementById('image-modal').style.display = 'none';
#             }}
#         </script>
#     </head>
#     <body>
#         <div class='container'>
#             <h1>QA Automation Report</h1>
#             <h2>Environment Details</h2>
#             <table>
#                 {''.join([f"<tr><td>{key}</td><td>{value}</td></tr>" for key, value in env_details.items()])}
#             </table>
#             <h2>Summary</h2>
#             <div class='metric-card passed'>Passed: {summary['Passed']}</div>
#             <div class='metric-card failed'>Failed: {summary['Failed']}</div>
#             <div class='metric-card error'>Error: {summary['Error']}</div>
#             <div class='metric-card existing'>Existing Issues: {summary['Existing Issues']}</div>
#             <h2>Results</h2>
#             <table>
#                 <tr><th>Check Name</th><th>Status</th><th>Description</th><th>Data</th><th>Proof</th></tr>
#                 {''.join([
#         f"""
#                     <tr>
#                         <td>{test['Name']}</td>
#                         <td class='{test['Status'].lower()}'>{test['Status']}</td>
#                         <td>{test['Description']}</td>
#                         <td>{test['Actual_Result']}</td>
#                         <td>{''.join([f"<img src='data:image/png;base64,{compress_and_encode_image(img)}' class='proof-img' onclick='enlargeImage(this.src)'/>" for img in test['Proof_Path']])}</td>
#                     </tr>
#                     """ for test in test_results])}
#             </table>
#             <div id='image-modal' class='modal'>
#                 <img id='modal-img' style='width: 100%; max-width: 600px;'>
#                 <button onclick='closeModal()'>Close</button>
#             </div>
#         </div>
#     </body>
#     </html>"""
#
#     with open(output_file, 'w', encoding='utf-8') as file:
#         file.write(html_content)
#     print(f"Report saved as {output_file}")
#
#
# # Example Usage
# env_details = {
#     "Site": "Example Site",
#     "Subscription": "Paid",
#     "Execution Date and Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
#     "Prod_Url": "http://example.com/prod",
#     "Stage_Url": "http://example.com/stage",
#     "Dev_Url": "http://example.com/dev",
#     "Platform": platform.system(),
#     "Total_Execution_Time": "00:10:00",
#     "Browser": "Chrome",
#     "Browser_ver.": "91.0"
# }
#
# generate_html_report(".\\Result\\cardio\\05_02_2025_08_27_23\\dev\\cardio_dev_results.json", env_details, "report1.html")


import json
import base64
import datetime
import platform
from pathlib import Path
from PIL import Image
from io import BytesIO


def compress_and_encode_image(image_path, max_size=(200, 200), quality=50):
    """Compress and encode an image to base64."""
    try:
        img = Image.open(image_path)
        img.thumbnail(max_size)
        buffer = BytesIO()
        img.save(buffer, format="PNG", quality=quality)
        return base64.b64encode(buffer.getvalue()).decode('utf-8')
    except Exception as e:
        print(f"Error processing image {image_path}: {e}")
        return ""


def generate_html_report(json_file, env_details, output_file):
    """Generate a self-contained HTML report."""
    with open(json_file, 'r') as file:
        test_results = json.load(file)

    # Count summary metrics
    summary = {"Passed": 0, "Failed": 0, "Error": 0, "Existing Issues": 0}
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
            .container {{ width: 90%; margin: auto; position: relative; font-family: sans-serif; color: white; }}
            .container::before, .container::after {{ content: ""; background-color: #fab5704c; position: absolute; }}
            .container::before {{ border-radius: 50%; width: 6rem; height: 6rem; top: 30%; right: 7%; }}
            .container::after {{ height: 3rem; top: 8%; right: 5%; border: 1px solid; }}
            .box {{ width: 11.875em; height: 15.875em; padding: 1rem; background-color: rgba(255, 255, 255, 0.074); border: 1px solid rgba(255, 255, 255, 0.222); backdrop-filter: blur(20px); border-radius: 0.7rem; transition: all ease 0.3s; }}
            .box:hover {{ box-shadow: 0px 0px 20px 1px #ffbb763f; border: 1px solid rgba(255, 255, 255, 0.454); }}
            .env-table, .results-table {{ width: 100%; border-collapse: collapse; margin-top: 10px; }}
            .env-table th, .env-table td, .results-table th, .results-table td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            .env-table th, .results-table th {{ background-color: #444; color: white; }}
            .metric-card {{ display: inline-block; padding: 10px; margin: 5px; width: 150px; text-align: center; color: white; border-radius: 5px; cursor: pointer; }}
            .status-badge {{ padding: 5px 10px; border-radius: 5px; color: white; border: none; display: inline-block; }}
            .passed {{ background-color: #4CAF50; }}
            .failed {{ background-color: #F44336; }}
            .error {{ background-color: #FF9800; }}
            .existing {{ background-color: #FFEB3B; color: black; }}
        </style>
        <script>
            function filterResults(status) {{
                let rows = document.querySelectorAll('.results-row');
                rows.forEach(row => {{
                    row.style.display = status === 'all' || row.classList.contains(status.toLowerCase()) ? '' : 'none';
                }});
            }}
        </script>
    </head>
    <body>
        <div class='container'>
            <h1>QA Automation Report</h1>
            <h2>Environment Details</h2>
            <table class='env-table'>
                <tr>
                    {''.join([f"<th>{key}</th>" for key in env_details.keys()])}
                </tr>
                <tr>
                    {''.join([f"<td>{value}</td>" for value in env_details.values()])}
                </tr>
            </table>
            <h2>Summary</h2>
            {''.join([f"<div class='metric-card {key.lower()}' onclick='filterResults('{key}')'>{key}: {value}</div>" for key, value in summary.items()])}
            <h2>Results</h2>
            <table class='results-table'>
                <tr><th>Check Name</th><th>Status</th><th>Description</th><th>Data</th><th>Proof</th></tr>
                {''.join([
        f"""
                    <tr class='results-row {test['Status'].lower()}'>
                        <td>{test['Name']}</td>
                        <td><span class='status-badge {test['Status'].lower()}'>{test['Status']}</span></td>
                        <td>{test['Description']}</td>
                        <td>{test['Actual_Result']}</td>
                        <td>{''.join([f"<img src='data:image/png;base64,{compress_and_encode_image(img)}' class='proof-img' onclick='enlargeImage(this.src)'/>" for img in test['Proof_Path']])}</td>
                    </tr>
                    """ for test in test_results])}
            </table>
        </div>
    </body>
    </html>"""

    with open(output_file, 'w', encoding='utf-8') as file:
        file.write(html_content)
    print(f"Report saved as {output_file}")


# Example Usage
env_details = {
    "Site": "Example Site",
    "Subscription": "Paid",
    "Execution Date and Time": datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"),
    "Prod_Url": "http://example.com/prod",
    "Stage_Url": "http://example.com/stage",
    "Dev_Url": "http://example.com/dev",
    "Platform": platform.system(),
    "Total_Execution_Time": "00:10:00",
    "Browser": "Chrome",
    "Browser_ver.": "91.0"
}

generate_html_report(".\\Result\\cardio\\05_02_2025_08_27_23\\dev\\cardio_dev_results.json", env_details, "report3.html")

