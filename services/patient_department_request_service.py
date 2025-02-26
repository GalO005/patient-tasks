from collections import defaultdict
from models.patient_task import PatientTask
from datetime import datetime
from uuid import uuid4
from models.patient_request import PatientRequest
from tinydb import where
from .abstract_patient_request_service import PatientRequestService
from typing import NewType, List, Dict
import db.db_tinydb as db

DepartmentToPatientTasks = NewType(
    'DepartmentToPatientTasks', dict[str, list[PatientTask]])

PatientToGroupedDepartmentTasks = dict[str, DepartmentToPatientTasks]


class DepartmentPatientRequestService(PatientRequestService):

    def get_open_patient_requests(self, patient_id) -> list[dict]:
        return db.patient_requests.search(
            (where('patient_id') == patient_id) & (where('status') == 'Open'))
    
    def process_department_tasks(self, patient_id: str, dept: str, 
                               dept_tasks: List[PatientTask], 
                               existing_req: dict | None = None) -> bool:
        """Process tasks for a specific department and update the database accordingly."""
        open_tasks = [t for t in dept_tasks if t.status == 'Open']
        
        if not open_tasks and existing_req:
            # Close the request if no open tasks and request exists
            closed_req = self.create_closed_request(patient_id, dept, existing_req)
            db.patient_requests.update(closed_req.model_dump(), where('id') == closed_req.id)
            return True

        if open_tasks:
            # Create or update request for open tasks
            pat_req = self.to_patient_request(patient_id, dept_tasks)
            if not existing_req:
                db.patient_requests.insert(pat_req.model_dump())
            else:
                pat_req.id = existing_req['id']
                db.patient_requests.update(pat_req.model_dump(), where('id') == pat_req.id)
            return True
            
        return False
    
    def create_closed_request(self, patient_id: str, department: str, 
                            existing_request: dict | None = None) -> PatientRequest:
        """Creates a closed request, using existing request data if available."""
        return PatientRequest(
            id=existing_request['id'] if existing_request else str(uuid4()),
            patient_id=patient_id,
            status='Closed',
            assigned_to=department,
            created_date=existing_request['created_date'] if existing_request else datetime.now(),
            updated_date=datetime.now(),
            messages=existing_request['messages'] if existing_request else [],
            medications=[],
            task_ids=set(),
            pharmacy_id=None
        )
    
    def close_remaining_requests(self, patient_id: str, remaining_requests: Dict[str, dict]) -> None:
        """Close any remaining open requests that no longer have associated tasks."""
        for req in remaining_requests.values():
            closed_req = self.create_closed_request(patient_id, req['assigned_to'], req)
            db.patient_requests.update(closed_req.model_dump(), where('id') == closed_req.id)

    def update_requests(self, tasks: list[PatientTask]):

        grouped_tasks: PatientToGroupedDepartmentTasks = defaultdict(
            lambda: defaultdict(list))
        
        for task in tasks:
            grouped_tasks[task.patient_id][task.assigned_to].append(task)
        
        for patient_id, dept_tasks in grouped_tasks.items():
            existing_requests = self.get_open_patient_requests(patient_id)
            existing_by_dept = {req['assigned_to']: req for req in existing_requests}

            for dept, dept_patient_tasks in dept_tasks.items():
                if self.process_department_tasks(
                    patient_id, dept, dept_patient_tasks, 
                    existing_by_dept.get(dept)):
                    existing_by_dept.pop(dept, None)
            
            self.close_remaining_requests(patient_id, existing_by_dept)
