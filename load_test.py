import time
import threading
import requests

API_URL = "http://127.0.0.1:8000/api/v1/screener?min_roe=15"
NUM_REQUESTS = 10
results = []

def make_request():
    start_time = time.time()
    try:
        response = requests.get(API_URL)
        elapsed = time.time() - start_time
        results.append({"status": response.status_code, "time": elapsed})
    except Exception as e:
        results.append({"status": "Error", "error": str(e)})

print(f"🚀 Launching {NUM_REQUESTS} concurrent requests to the Screener API...")

threads = []
overall_start = time.time()

for _ in range(NUM_REQUESTS):
    t = threading.Thread(target=make_request)
    threads.append(t)
    t.start()

for t in threads:
    t.join()
    
overall_time = time.time() - overall_start

print("\n📊 Load Test Results:")
for i, r in enumerate(results):
    print(f"Request {i+1}: Status {r.get('status')} - {r.get('time', 0):.4f} seconds")
    
print(f"\n✅ All 10 requests completed in {overall_time:.4f} seconds.")
if overall_time < 10.0:
    print("🎯 PERFORMANCE TARGET MET (Under 10 seconds).")
else:
    print("⚠️ PERFORMANCE TARGET FAILED (Over 10 seconds).")