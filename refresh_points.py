import asyncio
import aiohttp
from tqdm import tqdm

# API URLs
fetch_url = "https://api.xalyon.xyz/v2/phone"  # Replace with actual API URL
send_url = "https://api.xalyon.xyz/v2/refresh/"  # Replace with actual API URL

# Concurrency limit
MAX_CONCURRENT_REQUESTS = 20

# Counters
success_count = 0
fail_count = 0
error_log = []  # Store failed phone numbers

async def fetch_numbers():
    """Fetch phone numbers from API."""
    async with aiohttp.ClientSession() as session:
        async with session.get(fetch_url) as response:
            if response.status == 200:
                return await response.json()  # Assuming JSON list
            else:
                print(f"Failed to fetch numbers. Status: {response.status}")
                return []

async def send_request(session, phone, pbar, semaphore):
    """Send request once and update progress."""
    global success_count, fail_count

    async with semaphore:  # Limit concurrent requests
        try:
            async with session.get(f"{send_url}?phone={phone}") as response:
                if response.status == 200:
                    success_count += 1
                else:
                    fail_count += 1
                    error_log.append(phone)
        except Exception as e:
            print(f"Network error: {e} for {phone}")
            fail_count += 1
            error_log.append(phone)

        pbar.update(1)

async def main():
    global success_count, fail_count

    phone_numbers = await fetch_numbers()
    if not phone_numbers:
        print("No numbers to process.")
        return

    total_numbers = len(phone_numbers)
    print(f"Processing {total_numbers} numbers with {MAX_CONCURRENT_REQUESTS} concurrency...\n")

    semaphore = asyncio.Semaphore(MAX_CONCURRENT_REQUESTS)  # Limit concurrency

    with tqdm(total=total_numbers, desc="Processing", unit="req") as pbar:
        async with aiohttp.ClientSession() as session:
            tasks = [send_request(session, phone, pbar, semaphore) for phone in phone_numbers]
            await asyncio.gather(*tasks)  # Run all tasks concurrently

    # Final output
    print("\nProcessing Complete!")
    print(f"✅ Success: {success_count}")
    print(f"❌ Failed: {fail_count}")
    print(f"📊 Success Rate: {success_count / total_numbers * 100:.2f}%")

    # Save failed requests for retry
    if error_log:
        with open("failed_requests.txt", "w") as f:
            for phone in error_log:
                f.write(phone + "\n")
        print("⚠️ Failed requests saved to 'failed_requests.txt' for later retry.")

# Run the async event loop
asyncio.run(main())
