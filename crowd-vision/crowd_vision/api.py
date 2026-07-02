from __future__ import annotations

import threading
from typing import Any, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from .pipeline import CrowdVisionPipeline, PipelineConfig

app = FastAPI(title="Crowd Vision API")

pipeline: Optional[CrowdVisionPipeline] = None
_pipeline_lock = threading.Lock()
_current_source: Optional[str] = None


class StartRequest(BaseModel):
    source: str


class IngestRequest(BaseModel):
    source: str
    frame_index: int
    timestamp: Optional[float] = None
    result: dict[str, Any]


_latest_ingest: Optional[IngestRequest] = None


@app.on_event("startup")
def startup() -> None:
    global pipeline
    pipeline = CrowdVisionPipeline(PipelineConfig())


@app.post("/process/single")
def process_single(req: StartRequest) -> dict:
    global _current_source

    import cv2

    cap = cv2.VideoCapture(req.source)
    try:
        ret, frame = cap.read()
        if not ret:
            raise HTTPException(status_code=400, detail="Unable to read frame from source")
        with _pipeline_lock:
            if pipeline is None:
                raise HTTPException(status_code=500, detail="Pipeline not initialized")
            if _current_source != req.source:
                pipeline.prev_frame = None
                pipeline.trajectories.clear()
                pipeline.smoothed_history.clear()
                if hasattr(pipeline.model, "predictor") and pipeline.model.predictor is not None:
                    pipeline.model.predictor = None
                _current_source = req.source
            return pipeline.process_frame(frame)
    finally:
        cap.release()


@app.post("/ingest")
def ingest_result(req: IngestRequest) -> dict:
    global _latest_ingest
    _latest_ingest = req
    return {"ok": True}


@app.get("/ingest/latest")
def latest_ingest() -> dict:
    if _latest_ingest is None:
        return {"ok": True, "data": None}
    return {"ok": True, "data": _latest_ingest.model_dump()}
