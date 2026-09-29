import requests
import time
import pandas as pd
import warnings
from sklearn.ensemble import IsolationForest

# Faltu yellow warnings ko chupane ke liye
warnings.filterwarnings("ignore")

# Tumhare AWS Server (Prometheus) ka link
PROMETHEUS_URL = 'http://3.110.56.54:9090/api/v1/query'
CPU_QUERY = '100 - (avg by (instance) (rate(node_cpu_seconds_total{mode="idle"}[1m])) * 100)'

def fetch_cpu_data():
    try:
        response = requests.get(PROMETHEUS_URL, params={'query': CPU_QUERY})
        results = response.json()['data']['result']
        if results:
            return float(results[0]['value'][1])
    except Exception as e:
        print(f"Data fetch error: {e}")
    return None

def main():
    print("AI Monitoring Start ho rahi hai... Data collect kar rahe hain...")
    
    model = IsolationForest(contamination=0.1, random_state=42)
    cpu_data = []

    while True:
        current_cpu = fetch_cpu_data()
        
        if current_cpu is not None:
            print(f"Current CPU Usage: {current_cpu:.2f}%")

            # Shuru ke 10 data point bas collect karega
            if len(cpu_data) < 10:
                cpu_data.append([current_cpu])
            else:
                # Model ko purane 'Normal' data par train karo
                df = pd.DataFrame(cpu_data, columns=['cpu_usage'])
                model.fit(df)
                
                # Naye data ko check karo
                test_df = pd.DataFrame([[current_cpu]], columns=['cpu_usage'])
                prediction = model.predict(test_df)
                
                # SMART LOGIC: Agar anomaly hai aur CPU 15% se zyada hai
                if prediction[0] == -1 and current_cpu > 15.0:
                    print("🚨 ALERT: Abnormal CPU Spike Detected! (Anomaly)")
                    # DHYAN DO: Hum is kharab data ko list mein add NAHI kar rahe!
                else:
                    print("✅ Server Normal Chal Raha Hai.")
                    # Data normal hai toh usko list mein daal lo (List ki limit 50 rakhi hai)
                    cpu_data.append([current_cpu])
                    if len(cpu_data) > 50:
                        cpu_data.pop(0)
                        
        time.sleep(5)

if __name__ == '__main__':
    main()