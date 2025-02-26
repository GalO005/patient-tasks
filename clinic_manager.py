
from models import TaskInput
from services.patient_request_service import PerPatientRequestService
from services.abstract_patient_request_service import PatientRequestService
from services.task_service import TaskService


class ClinicManager:

    def __init__(self, patientRequestService: PatientRequestService = None):
        self.patient_request_service = patientRequestService or PerPatientRequestService()
        self.task_service = TaskService()

    def process_tasks_update(self, task_input: TaskInput):
        """Accepts a task_input object that contains all the tasks that were modified since
        the last time this method was called. The method process the changes to the tasks, and updates the patient requests appropriately. """

        tasks = task_input.tasks
        if not tasks:
            return

        self.task_service.updates_tasks(tasks)

        newly_closed_tasks = [t for t in tasks if t.status == 'Closed']

        # Question: What is a potential performance issue with this code ?
        # Answer: There are several potential performance issues here:
        # 1. list(self.task_service.get_open_tasks()) loads ALL open tasks from the database,
        #    even though we only need tasks related to the patients in the current update.
        #    This can be very inefficient with millions of patients.
        # 2. The concatenation of open_tasks + newly_closed_tasks might contain duplicate tasks
        #    if a task was both opened and closed in the same update.
        # 3. Loading all open tasks into memory at once can cause memory pressure with large datasets.
        # 
        # Better approach would be to:
        # 1. Only load open tasks for patients affected by the current update
        # 2. Use a set to deduplicate tasks
        # 3. Use batching or streaming for large datasets
        open_tasks = list(self.task_service.get_open_tasks())

        self.patient_request_service.update_requests(
            open_tasks + newly_closed_tasks)
