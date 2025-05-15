import torch
import psutil
import time
import statistics

def monitor_cpu_memory():
    if not torch.cuda.is_available():
        print("No hay GPU disponible. Ejecutando solo con CPU.")
        return

    torch.cuda.init()
    print("Monitoreando CPU, RAM y GPU... Presiona Ctrl+C para detener.")

    cpu_usages = []
    ram_usages = []
    gpu_reserved = []
    gpu_allocated = []

    try:
        while True:
            cpu = psutil.cpu_percent()
            ram = psutil.virtual_memory().percent
            device = torch.device("cuda")

            total_mem = torch.cuda.get_device_properties(device).total_memory
            x = torch.randn(1000, 1000, device=device)
            reserved_mem = torch.cuda.memory_reserved(device)
            allocated_mem = torch.cuda.memory_allocated(device)

            cpu_usages.append(cpu)
            ram_usages.append(ram)
            gpu_reserved.append(reserved_mem)
            gpu_allocated.append(allocated_mem)

            print({
                "CPU Uso (%)": cpu,
                "RAM Uso (%)": ram,
                "GPU Memoria Total (GB)": round(total_mem / 1e9, 2),
                "GPU Memoria Reservada (GB)": round(reserved_mem / 1e9, 2),
                "GPU Memoria Usada (GB)": round(allocated_mem / 1e9, 2)
            })

            time.sleep(0.5)

    except KeyboardInterrupt:
        print("\nDetenido por el usuario. Calculando promedios...")

        avg_cpu = statistics.mean(cpu_usages)
        avg_ram = statistics.mean(ram_usages)
        avg_gpu_reserved = statistics.mean(gpu_reserved)
        avg_gpu_allocated = statistics.mean(gpu_allocated)

        print("\n**Resumen de uso promedio:**")
        print(f"-> CPU Promedio: {avg_cpu:.2f}%")
        print(f"-> RAM Promedio: {avg_ram:.2f}%")
        print(f"-> GPU Memoria Reservada Promedio: {avg_gpu_reserved / 1e9:.2f} GB")
        print(f"-> GPU Memoria Usada Promedio: {avg_gpu_allocated / 1e9:.2f} GB")
        print(":P Programa finalizado.")

def main():
    monitor_cpu_memory()

if __name__ == "__main__":
    main()