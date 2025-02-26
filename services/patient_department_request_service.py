from collections import defaultdict
from models.patient_task import PatientTask
from tinydb import where
from .abstract_patient_request_service import PatientRequestService
from typing import NewType
import db.db_tinydb as db

DepartmentToPatientTasks = NewType(
    'DepartmentToPatientTasks', dict[str, list[PatientTask]])

PatientToGroupedDepartmentTasks = dict[str, DepartmentToPatientTasks]


class DepartmentPatientRequestService(PatientRequestService):

    def get_open_patient_requests(self, patient_id) -> list[dict]:
        return db.patient_requests.search(
            (where('patient_id') == patient_id) & (where('status') == 'Open'))

    def update_requests(self, tasks: list[PatientTask]):

        grouped_tasks: PatientToGroupedDepartmentTasks = defaultdict(
            lambda: defaultdict(list))
        
        for task in tasks:
            grouped_tasks[task.patient_id][task.assigned_to].append(task)
        
        for patient_id, dept_tasks in grouped_tasks.items():
            existing_requests = self.get_open_patient_requests(patient_id)
            existing_by_dept = {req['assigned_to']: req for req in existing_requests}
