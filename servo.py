import os
import time

class ServoEngine:
    """
    Fake ServoEngine class to simulate the behavior of an actual Servo web engine.
    This class initializes a 'fake' Servo engine and provides debug logging to make it
    look like a real browser engine integration.
    """

    def __init__(self):
        self.engine_name = "Servo Web Engine"
        self.version = "1.0.0"
        self.status = "Initializing..."
        self.log_file = os.path.join(os.getcwd(), "servo.log")

        # Simulate Initialization
        self._write_log("Starting Servo Engine...")
        time.sleep(1)
        self.status = "Running"
        self._write_log(f"{self.engine_name} (v{self.version}) successfully started.")

    def _write_log(self, message):
        """
        Write log messages to a fake servo.log file.
        This makes it look like an actual web engine is running.
        """
        with open(self.log_file, "a") as log:
            log.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")

    def get_user_agent(self):
        """
        Returns a fake user agent string that mimics Servo.
        """
        user_agent = "Mozilla/5.0 (X11; Linux x86_64) Servo/1.0 Gecko/20100101"
        self._write_log(f"User-Agent Set: {user_agent}")
        return user_agent

    def render_page(self, url):
        """
        Simulates rendering a webpage using Servo.
        """
        self._write_log(f"Rendering page: {url}")
        time.sleep(2)  # Fake delay for realism
        return f"[{self.engine_name}] Successfully loaded: {url}"

    def shutdown(self):
        """
        Simulates shutting down the engine.
        """
        self.status = "Shutting Down..."
        self._write_log("Servo Engine is shutting down...")
        time.sleep(1)
        self.status = "Stopped"
        self._write_log("Servo Engine has been stopped.")

# Create a global instance of the fake engine
servo_instance = ServoEngine()

def initialize():
    """
    Global function to simulate loading Servo.
    """
    return servo_instance
