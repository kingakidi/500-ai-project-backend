from __future__ import annotations

import logging
import threading
import time
import uuid
from typing import Any

logger = logging.getLogger(__name__)

_serial_io_lock = threading.Lock()
_enroll_lock = threading.Lock()
_reader_thread: threading.Thread | None = None
_reader_started = False
_serial: Any = None

_active_enroll: dict[str, Any] | None = None
_scan_event_id = 0
_last_scan: dict[str, Any] = {
    "event_id": 0,
    "template_slot": None,
    "student": None,
    "at": 0.0,
}
_serial_connected = False


def is_serial_connected() -> bool:
    with _serial_io_lock:
        return bool(
            _serial_connected
            and _serial is not None
            and getattr(_serial, "is_open", False)
        )


def _open_serial():
    import serial
    from django.conf import settings

    forced = (getattr(settings, "ARDUINO_PORT", None) or "").strip()
    if forced:
        return serial.Serial(
            forced,
            9600,
            timeout=1,
            write_timeout=2,
            dsrdtr=False,
            rtscts=False,
        )

    import serial.tools.list_ports

    ports = list(serial.tools.list_ports.comports())

    def port_key(p):
        desc = (p.description or "").lower()
        score = 0
        for key in (
            "arduino",
            "ch340",
            "cp210",
            "usb-serial",
            "usb serial",
            "silabs",
            "silicon labs",
        ):
            if key in desc:
                score += 10
        return (-score, p.device)

    for port in sorted(ports, key=port_key):
        try:
            return serial.Serial(
                port.device,
                9600,
                timeout=1,
                write_timeout=None,
                dsrdtr=False,
                rtscts=False,
            )
        except OSError as e:
            logger.warning("Serial open failed %s: %s", port.device, e)
    return None


def _append_session_message(msg: str) -> None:
    global _active_enroll
    if not _active_enroll:
        return
    lines: list[str] = _active_enroll.setdefault("messages", [])
    lines.append(msg)
    if len(lines) > 40:
        del lines[: len(lines) - 40]


def _handle_enrolled() -> None:
    global _active_enroll
    from django.db import close_old_connections

    with _enroll_lock:
        sess = dict(_active_enroll) if _active_enroll else None
    if not sess or sess.get("status") not in ("started", "waiting"):
        return
    student_id = sess.get("student_id")
    slot = sess.get("template_slot")
    if not student_id or slot is None:
        return
    close_old_connections()
    try:
        from students.models import Student

        updated = Student.objects.filter(pk=student_id).update(
            fingerprint_template_slot=slot
        )
        with _enroll_lock:
            if _active_enroll and _active_enroll.get("capture_id") == sess.get("capture_id"):
                if updated:
                    _active_enroll["status"] = "success"
                    _active_enroll["message"] = "Fingerprint enrolled on sensor."
                else:
                    _active_enroll["status"] = "failed"
                    _active_enroll["message"] = "Student record not found."
    except Exception as exc:  # noqa: BLE001
        logger.exception("Failed to save template slot: %s", exc)
        with _enroll_lock:
            if _active_enroll and _active_enroll.get("capture_id") == sess.get("capture_id"):
                _active_enroll["status"] = "failed"
                _active_enroll["message"] = str(exc)
    finally:
        close_old_connections()


def _handle_line(line: str) -> None:
    global _active_enroll, _scan_event_id, _last_scan

    low = line.lower()
    with _enroll_lock:
        if _active_enroll and _active_enroll.get("status") in ("started", "waiting"):
            _append_session_message(line)
            if low.startswith("place finger"):
                _active_enroll["status"] = "waiting"
                _active_enroll["phase"] = "place_first"
            elif low.startswith("remove finger"):
                _active_enroll["phase"] = "remove"
            elif low.startswith("place again"):
                _active_enroll["phase"] = "place_second"

    if line == "ENROLLED":
        _handle_enrolled()
    elif line == "ENROLL FAILED":
        with _enroll_lock:
            if _active_enroll and _active_enroll.get("status") in ("started", "waiting"):
                _active_enroll["status"] = "failed"
                _active_enroll["message"] = "Sensor reported enroll failure."

    if line.startswith("ID:"):
        try:
            slot = int(line[3:].strip())
        except ValueError:
            return
        from django.db import close_old_connections

        close_old_connections()
        try:
            from students.models import Student
            from students.serializers import StudentSerializer

            student = (
                Student.objects.filter(fingerprint_template_slot=slot)
                .select_related("department", "department__faculty")
                .first()
            )
            payload = StudentSerializer(student).data if student else None
        finally:
            close_old_connections()

        with _enroll_lock:
            _scan_event_id += 1
            _last_scan = {
                "event_id": _scan_event_id,
                "template_slot": slot,
                "student": payload,
                "at": time.time(),
            }


def _reader_loop() -> None:
    global _serial, _serial_connected
    while True:
        try:
            opened_fresh = False
            with _serial_io_lock:
                if _serial is None or not getattr(_serial, "is_open", False):
                    _serial_connected = False
                    if _serial is not None:
                        try:
                            _serial.close()
                        except OSError:
                            pass
                        _serial = None
                    _serial = _open_serial()
                    if _serial is not None:
                        opened_fresh = True

            if opened_fresh:
                time.sleep(2.5)
                with _serial_io_lock:
                    if _serial is not None and getattr(_serial, "is_open", False):
                        _serial_connected = True
                        logger.info("Fingerprint serial connected: %s", _serial.name)
                    else:
                        _serial_connected = False

            with _serial_io_lock:
                ser_ok = _serial is not None and getattr(_serial, "is_open", False)
            if not ser_ok:
                time.sleep(3)
                continue

            raw = b""
            with _serial_io_lock:
                if _serial is not None and getattr(_serial, "is_open", False):
                    if _serial.in_waiting:
                        raw = _serial.readline()

            if not raw:
                time.sleep(0.08)
                continue

            line = raw.decode("utf-8", errors="replace").strip()
            if line:
                logger.debug("Serial RX: %s", line)
                _handle_line(line)
        except Exception as exc:  # noqa: BLE001
            logger.exception("Serial reader error: %s", exc)
            with _serial_io_lock:
                _serial_connected = False
                if _serial is not None:
                    try:
                        _serial.close()
                    except OSError:
                        pass
                    _serial = None
            time.sleep(2)


def ensure_reader_running() -> None:
    global _reader_thread, _reader_started
    if _reader_started:
        return
    try:
        import serial  # noqa: F401
    except ImportError:
        logger.warning("pyserial not installed; fingerprint reader thread not started.")
        return
    _reader_started = True
    _reader_thread = threading.Thread(
        target=_reader_loop,
        name="fingerprint-serial-reader",
        daemon=True,
    )
    _reader_thread.start()


def write_command(text: str) -> bool:
    import serial as pyserial

    data = text if text.endswith("\n") else f"{text}\n"
    payload = data.encode("utf-8")
    try:
        with _serial_io_lock:
            if _serial is None or not getattr(_serial, "is_open", False):
                return False
            _serial.write(payload)
            _serial.flush()
        return True
    except pyserial.SerialException as e:
        logger.error("Serial write failed: %s", e)
        return False
    except OSError as e:
        logger.error("Serial write failed: %s", e)
        return False


def try_start_enroll(student_id) -> tuple[bool, dict[str, Any]]:
    global _active_enroll
    from django.db import close_old_connections

    close_old_connections()
    try:
        from students.models import Student

        student = Student.objects.filter(pk=student_id).first()
        if not student:
            return False, {"message": "Student not found."}

        used = set(
            Student.objects.exclude(fingerprint_template_slot__isnull=True)
            .exclude(pk=student.pk)
            .values_list("fingerprint_template_slot", flat=True)
        )
        if student.fingerprint_template_slot:
            slot = int(student.fingerprint_template_slot)
        else:
            slot = None
            for i in range(1, 128):
                if i not in used:
                    slot = i
                    break
            if slot is None:
                return False, {"message": "No free sensor template slots (1–127)."}
    finally:
        close_old_connections()

    capture_id = str(uuid.uuid4())
    with _enroll_lock:
        if _active_enroll and _active_enroll.get("status") in ("started", "waiting"):
            return False, {"message": "Another enrollment is already in progress."}
        if _active_enroll:
            _active_enroll = None
        _active_enroll = {
            "capture_id": capture_id,
            "student_id": str(student.pk),
            "template_slot": slot,
            "status": "started",
            "phase": "command_sent",
            "message": "Follow prompts on the sensor. Place finger when instructed.",
            "messages": [],
        }

    ok = write_command(f"ENROLL:{slot}")
    if not ok:
        with _enroll_lock:
            _active_enroll = None
        return False, {"message": "Serial not connected. Check USB and ARDUINO_PORT."}

    return True, {
        "capture_id": capture_id,
        "template_slot": slot,
        "message": "Enrollment started. Place finger when the sensor / logs indicate.",
    }


def get_enroll_status(capture_id: str) -> dict[str, Any] | None:
    with _enroll_lock:
        if not _active_enroll or _active_enroll.get("capture_id") != capture_id:
            return None
        return {
            "capture_id": _active_enroll["capture_id"],
            "status": _active_enroll["status"],
            "template_slot": _active_enroll.get("template_slot"),
            "phase": _active_enroll.get("phase"),
            "message": _active_enroll.get("message", ""),
            "messages": list(_active_enroll.get("messages", [])),
        }


def cancel_enroll(capture_id: str | None) -> bool:
    global _active_enroll
    with _enroll_lock:
        if not _active_enroll:
            return False
        if capture_id and _active_enroll.get("capture_id") != capture_id:
            return False
        _active_enroll = None
    return True


def get_last_scan() -> dict[str, Any]:
    with _enroll_lock:
        return dict(_last_scan)
