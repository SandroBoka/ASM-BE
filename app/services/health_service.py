class HealthService:
    @staticmethod
    def get_health_status():
        return {
            "status": "ok",
            "service": "ASM Backend"
        }
