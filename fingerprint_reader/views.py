from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from utils.response import APIResponse

from .services import hardware


class FingerprintEnrollStartView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not hardware.is_serial_connected():
            return APIResponse.error(
                "Fingerprint reader is not connected (USB serial).",
                error={},
                status_code=503,
            )
        student_id = request.data.get("student_id")
        if not student_id:
            return APIResponse.bad_request(
                "student_id is required.",
                error={"student_id": ["This field is required."]},
            )
        ok, payload = hardware.try_start_enroll(str(student_id))
        if not ok:
            msg = payload.get("message", "Could not start enrollment.")
            code = 409 if "progress" in msg.lower() else 400
            return APIResponse.error(msg, error={}, status_code=code)
        return APIResponse.success(
            payload.get("message", "Started."),
            data={
                "capture_id": payload["capture_id"],
                "template_slot": payload["template_slot"],
            },
        )


class FingerprintEnrollStatusView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        capture_id = request.query_params.get("capture_id")
        if not capture_id:
            return APIResponse.bad_request(
                "capture_id query parameter is required.",
                error={"capture_id": ["This field is required."]},
            )
        status = hardware.get_enroll_status(capture_id)
        if status is None:
            return APIResponse.not_found("Enrollment session not found or expired.")
        return APIResponse.success("OK", data=status)


class FingerprintEnrollCancelView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        capture_id = request.data.get("capture_id")
        hardware.cancel_enroll(capture_id)
        return APIResponse.success("Cancelled.", data={})


class FingerprintScanLatestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        scan = hardware.get_last_scan()
        connected = hardware.is_serial_connected()
        return APIResponse.success(
            "OK",
            data={
                "serial_connected": connected,
                "event_id": scan.get("event_id", 0),
                "template_slot": scan.get("template_slot"),
                "student": scan.get("student"),
                "at": scan.get("at", 0.0),
            },
        )
