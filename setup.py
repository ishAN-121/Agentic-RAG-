import subprocess
import threading

# Define server commands
SERVER_COMMANDS = [
    "python -m rag.bm25_server",
    "python -m rag.splade_server",
    "python -m rag.vector_server",
    "python -m logger_server",
    "python -m query_server",
    "python -m CA_agent.CA_server",
]

# Keep track of processes
processes = []


def run_server(command):
    """Run a server command."""
    process = subprocess.Popen(command, shell=True)
    processes.append(process)
    process.wait()


def terminate_servers():
    """Terminate all running servers."""
    print("\nTerminating all servers...")
    for process in processes:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
    print("All servers terminated.")


def main():
    """Main function to spawn servers and handle termination."""
    threads = []

    try:
        for command in SERVER_COMMANDS:
            thread = threading.Thread(target=run_server, args=(command,))
            threads.append(thread)
            thread.start()

        # Wait for threads to complete (will run indefinitely)
        for thread in threads:
            thread.join()

    except KeyboardInterrupt:
        # Graceful shutdown on Ctrl+C
        terminate_servers()


if __name__ == "__main__":
    main()
