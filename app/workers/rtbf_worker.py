"""
RTBF (Right-to-be-Forgotten) background worker
"""
from celery import current_task
from sqlalchemy.orm import sessionmaker
from app.db import engine
from app.services.rtbf_service import RTBFService
from app.workers.celery_app import celery_app
from app.utils.audit import log_audit_event
import logging

# Create database session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, name="process_rtbf_request")
def process_rtbf_request(self, request_id: int):
    """
    Process a Right-to-be-Forgotten request
    
    Args:
        request_id: ID of the deletion request to process
        
    Returns:
        dict: Result of the processing operation
    """
    db = SessionLocal()
    try:
        logger.info(f"Starting RTBF processing for request {request_id}")
        
        # Update task status
        self.update_state(
            state="PROGRESS",
            meta={"request_id": request_id, "status": "processing"}
        )
        
        # Process the deletion request
        rtbf_service = RTBFService(db)
        success = rtbf_service.process_deletion_request(request_id, "rtbf_worker")
        
        if success:
            logger.info(f"Successfully processed RTBF request {request_id}")
            return {
                "request_id": request_id,
                "status": "completed",
                "message": "RTBF request processed successfully"
            }
        else:
            logger.error(f"Failed to process RTBF request {request_id}")
            return {
                "request_id": request_id,
                "status": "failed",
                "message": "Failed to process RTBF request"
            }
            
    except Exception as exc:
        logger.error(f"Error processing RTBF request {request_id}: {str(exc)}")
        
        # Log the error to audit log
        try:
            log_audit_event(
                db, "rtbf_worker", "rtbf_error", "deletion_request", request_id,
                {"error": str(exc), "task_id": self.request.id}
            )
        except Exception:
            pass  # Don't fail the task if audit logging fails
        
        # Update task state
        self.update_state(
            state="FAILURE",
            meta={"request_id": request_id, "error": str(exc)}
        )
        
        raise exc
        
    finally:
        db.close()


@celery_app.task(name="process_pending_rtbf_requests")
def process_pending_rtbf_requests():
    """
    Process all pending RTBF requests
    This task can be scheduled to run periodically
    """
    db = SessionLocal()
    try:
        logger.info("Processing pending RTBF requests")
        
        rtbf_service = RTBFService(db)
        pending_requests = rtbf_service.get_pending_requests()
        
        processed_count = 0
        failed_count = 0
        
        for request in pending_requests:
            try:
                # Process each request
                success = rtbf_service.process_deletion_request(request.id, "rtbf_worker")
                if success:
                    processed_count += 1
                else:
                    failed_count += 1
                    
            except Exception as e:
                logger.error(f"Error processing request {request.id}: {str(e)}")
                failed_count += 1
        
        logger.info(f"Processed {processed_count} requests, {failed_count} failed")
        
        return {
            "processed": processed_count,
            "failed": failed_count,
            "total": len(pending_requests)
        }
        
    except Exception as exc:
        logger.error(f"Error in process_pending_rtbf_requests: {str(exc)}")
        raise exc
        
    finally:
        db.close()
