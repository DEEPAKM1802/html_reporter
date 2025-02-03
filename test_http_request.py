import os
import time
import asyncio
import hashlib
from playwright.async_api import async_playwright

# Configuration
MAX_TABS = 50  # Number of persistent tabs
TIMEOUT = 10000  # Timeout for page loads (in milliseconds)
OUTPUT_DIR = "screenshots"

# Create output directory
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def fetch_page_info(page, url):
    """Fetch response status, console errors, network errors, and take a screenshot."""
    response_status = None
    console_errors = []
    network_errors = []
    screenshot_path = None

    try:
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: network_errors.append(f"Failed {req.url}: {req.failure}"))

        response = await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
        response_status = response.status if response else "No Response"

        # Optimized screenshot path
        screenshot_path = os.path.join(OUTPUT_DIR, f"{hashlib.md5(url.encode()).hexdigest()}.webp")
        await page.screenshot(path=screenshot_path, type="webp", quality=80, full_page=True)

    except Exception as e:
        network_errors.append(f"Error navigating {url}: {e}")

    return {
        "url": url,
        "status": response_status,
        "console_errors": console_errors,
        "network_errors": network_errors,
        "screenshot": screenshot_path
    }


async def worker(queue, page):
    """Worker function to process URLs using a persistent page."""
    while True:
        try:
            url = queue.get_nowait()
        except asyncio.QueueEmpty:
            break  # Exit if no more tasks

        result = await fetch_page_info(page, url)
        print(result)
        queue.task_done()


async def process_urls(url_list):
    """Efficiently manage multiple Playwright pages asynchronously."""
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=False,
            args=["--disable-background-timer-throttling", "--disable-backgrounding-occluded-windows",
                  "--disable-dev-shm-usage", "--no-sandbox", "--disable-gpu"]
        )
        context = await browser.new_context(no_viewport=True)

        queue = asyncio.Queue()
        for url in url_list:
            await queue.put(url)

        # Create 50 persistent pages
        pages = [await context.new_page() for _ in range(min(MAX_TABS, len(url_list)))]

        # Assign workers to pages
        await asyncio.gather(*(worker(queue, page) for page in pages))

        # Close all pages
        await asyncio.gather(*(page.close() for page in pages))

        await browser.close()

    end_time = time.time()
    print(f"\nTotal Execution Time: {end_time - start_time:.2f} seconds")
    print(f"{round(len(url_list) / (end_time - start_time), 2)} requests/sec")


if __name__ == "__main__":
    url_list = [f"https://example.com/page{i}" for i in range(1000)]
    asyncio.run(process_urls(url_list))
###########################################################################################################################################
import os
import time
import asyncio
from collections import deque
from playwright.async_api import async_playwright

# Configuration
MAX_TABS = 50
TIMEOUT = 10000
OUTPUT_DIR = "screenshots"
BATCH_SIZE = 50
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def fetch_page_info(page, url):
    """Fetch response status, console errors, network errors, and take a screenshot."""
    response_status = None
    console_errors = deque(maxlen=10)
    network_errors = deque(maxlen=10)
    screenshot_path = None

    try:
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: network_errors.append(f"Failed {req.url}: {req.failure}"))

        response = await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
        response_status = response.status if response else "No Response"

        screenshot_path = os.path.join(OUTPUT_DIR, f"{abs(hash(url))}.webp")
        # screenshot_path = os.path.join(OUTPUT_DIR, f"{hashlib.md5(url.encode()).hexdigest()}.webp")
        await page.screenshot(path=screenshot_path, type="webp", quality=80, full_page=True)

    except asyncio.TimeoutError:
        network_errors.append(f"Timeout navigating {url}")
    except Exception as e:
        network_errors.append(f"Unexpected error: {str(e)}")

    print({
        "url": url,
        "status": response_status,
        "console_errors": list(console_errors),
        "network_errors": list(network_errors),
        "screenshot": screenshot_path
    })

    return {
        "url": url,
        "status": response_status,
        "console_errors": list(console_errors),
        "network_errors": list(network_errors),
        "screenshot": screenshot_path
    }


async def batch_worker(queue, page):
    """Process URLs in batches to reduce network latency."""
    while not queue.empty():
        batch = [await queue.get() for _ in range(min(queue.qsize(), BATCH_SIZE))]
        await asyncio.gather(*(fetch_page_info(page, url) for url in batch))
        for _ in batch:
            queue.task_done()


async def process_urls(url_list):
    """Efficiently manage multiple Playwright pages asynchronously."""
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-background-timer-throttling",
                                                                "--disable-backgrounding-occluded-windows",
                                                                "--disable-dev-shm-usage", "--no-sandbox",
                                                                "--disable-gpu"])
        context = await browser.new_context(no_viewport=True)

        queue = asyncio.Queue()
        for url in url_list:
            await queue.put(url)

        pages = [await context.new_page() for _ in range(min(MAX_TABS, len(url_list)))]
        ft = time.time()
        await asyncio.gather(*(batch_worker(queue, page) for page in pages))
        fet = time.time()
        await asyncio.gather(*(page.close() for page in pages))

        await browser.close()

    end_time = time.time()
    print(f"\nTotal Fetch Time: {fet - ft:.2f} seconds")
    print(f"\nTotal Execution Time: {end_time - start_time:.2f} seconds")
    print(f"{round(len(url_list) / (fet - ft), 2)} requests/sec")


def run_playwright_in_parallel(url_chunk):
    """Runs Playwright in parallel for different URL chunks."""
    asyncio.run(process_urls(url_chunk))


if __name__ == "__main__":
    url_list = [f"https://example.com/page{i}" for i in range(5000)]
    num_cores = min(multiprocessing.cpu_count(), 1)  # Use up to 4 cores
    chunk_size = len(url_list) // num_cores
    chunks = [url_list[i:i + chunk_size] for i in range(0, len(url_list), chunk_size)]

    with multiprocessing.Pool(num_cores) as pool:
        pool.map(run_playwright_in_parallel, chunks)
#########################################################################################################################adaptive batch
import os
import time
import asyncio
from collections import deque
from playwright.async_api import async_playwright

# Configuration
MAX_TABS = 50
TIMEOUT = 10000
OUTPUT_DIR = "screenshots"
BATCH_SIZE = 50
os.makedirs(OUTPUT_DIR, exist_ok=True)


async def fetch_page_info(page, url):
    """Fetch response status, console errors, network errors, and take a screenshot."""
    response_status = None
    console_errors = deque(maxlen=10)
    network_errors = deque(maxlen=10)
    screenshot_path = None

    try:
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)
        page.on("requestfailed", lambda req: network_errors.append(f"Failed {req.url}: {req.failure}"))

        response = await page.goto(url, timeout=TIMEOUT, wait_until="domcontentloaded")
        response_status = response.status if response else "No Response"

        screenshot_path = os.path.join(OUTPUT_DIR, f"{abs(hash(url))}.webp")
        await page.screenshot(path=screenshot_path, type="webp", quality=80, full_page=True)

    except asyncio.TimeoutError:
        network_errors.append(f"Timeout navigating {url}")
    except Exception as e:
        network_errors.append(f"Unexpected error: {str(e)}")

    print({
        "url": url,
        "status": response_status,
        "console_errors": list(console_errors),
        "network_errors": list(network_errors),
        "screenshot": screenshot_path
    })

    return {
        "url": url,
        "status": response_status,
        "console_errors": list(console_errors),
        "network_errors": list(network_errors),
        "screenshot": screenshot_path
    }


async def adaptive_batch_worker(queue, page):
    """Process URLs in batches dynamically to reduce network latency and balance load."""
    while not queue.empty():
        batch = []
        for _ in range(min(queue.qsize(), BATCH_SIZE)):
            try:
                batch.append(await queue.get())
            except asyncio.QueueEmpty:
                break
        await asyncio.gather(*(fetch_page_info(page, url) for url in batch))
        for _ in batch:
            queue.task_done()


async def process_urls(url_list):
    """Efficiently manage multiple Playwright pages asynchronously with adaptive worker load balancing."""
    start_time = time.time()

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False, args=["--disable-background-timer-throttling",
                                                                "--disable-backgrounding-occluded-windows",
                                                                "--disable-dev-shm-usage", "--no-sandbox",
                                                                "--disable-gpu"])
        context = await browser.new_context(no_viewport=True)

        queue = asyncio.Queue()
        for url in url_list:
            await queue.put(url)

        pages = [await context.new_page() for _ in range(min(MAX_TABS, len(url_list)))]
        ft = time.time()
        await asyncio.gather(*(adaptive_batch_worker(queue, page) for page in pages))
        fet = time.time()
        await asyncio.gather(*(page.close() for page in pages))

        await browser.close()

    end_time = time.time()
    print(f"\nTotal Fetch Time: {fet - ft:.2f} seconds")
    print(f"\nTotal Execution Time: {end_time - start_time:.2f} seconds")
    print(f"{round(len(url_list) / (fet - ft), 2)} requests/sec")


if __name__ == "__main__":
    url_list = [f"https://example.com/page{i}" for i in range(5000)]
    asyncio.run(process_urls(url_list))

#############################################################################################################################