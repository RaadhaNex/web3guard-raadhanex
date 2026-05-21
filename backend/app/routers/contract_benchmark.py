from fastapi import APIRouter

from app.services.contract_benchmark import BENCHMARK_CASES, run_contract_benchmark
from app.services.scan_contract import available_contract_rules

router = APIRouter(prefix="/contract-benchmark", tags=["contract-benchmark"])


@router.get("/status")
def status():
    return {
        "ok": True,
        "engine": "professional_scanner_phase_b",
        "case_count": len(BENCHMARK_CASES),
        "available_contract_rules": len(available_contract_rules()),
        "disclaimer": "Synthetic benchmark only. Not a certified audit accuracy claim.",
    }


@router.get("/run")
def run():
    return run_contract_benchmark()
