"""Temporary Windows idle-sleep request, automatically released after delivery."""
from pathlib import Path
import ctypes,time,json
OUT=Path(__file__).resolve().parents[1]/'outputs/modeling/four_expert_combinations/v1'
def main():
    state=ctypes.windll.kernel32.SetThreadExecutionState
    previous=state(0x80000001)
    (OUT/'audit/temporary_awake.json').write_text(json.dumps(dict(system_idle_sleep_request=bool(previous),display_request=False,permanent_power_plan_change=False)))
    print('Temporary idle-sleep request active; no display request or power-plan change.',flush=True)
    try:
        while not (OUT/'finalizer_complete.json').exists():time.sleep(30)
    finally:
        state(0x80000000)
        (OUT/'audit/temporary_awake_restored.json').write_text(json.dumps(dict(restored=True)))
if __name__=='__main__':main()
